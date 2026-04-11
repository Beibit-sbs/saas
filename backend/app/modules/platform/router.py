from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.billing.service import (
    change_subscription_plan,
    get_tenant_billing_state,
    transition_subscription_status,
)
from app.modules.observability.security_signals import record_security_signal
from app.modules.plans.schemas import PlanCreatePayload, PlanItemResponse, PlanListResponse, PlanUpdatePayload
from app.modules.plans.service import create_plan, list_plans, update_plan
from app.modules.quotas.schemas import (
    PlanQuotaConsistencyReportSchema,
    PlanQuotaPayload,
    QuotaListResponse,
)
from app.modules.quotas.service import (
    get_plan_quota_consistency_report,
    list_quotas,
    update_plan_quotas,
)
from app.modules.rbac.security import get_actor, resolve_current_user_claims
from app.modules.rbac.service import is_platform_admin
from app.modules.tenants.provisioning_service import TenantProvisioningService

router = APIRouter(prefix="/platform", tags=["platform"])
PLATFORM_TENANT_ID = 1


def _require_platform_admin(
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    claims = resolve_current_user_claims(request, authorization)
    claim_roles = {role.strip() for role in claims.roles if role.strip()}
    if "superadmin" in claim_roles and int(claims.tenant_id) == 1:
        return actor
    if is_platform_admin(actor):
        return actor
    record_security_signal(
        signal="platform.access.denied",
        outcome="denied",
        actor=actor,
        client_ip=request.client.host if request.client else "unknown",
        path=request.url.path,
        tenant_id=claims.tenant_id,
    )
    raise HTTPException(status_code=403, detail="platform admin access required")


@router.get("/plans", response_model=PlanListResponse)
def get_platform_plans(
    _: Annotated[str, Depends(_require_platform_admin)],
) -> PlanListResponse:
    return {"plans": list_plans(include_inactive=True)}


@router.post("/plans", response_model=PlanItemResponse)
def create_platform_plan(
    payload: PlanCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_admin)],
) -> PlanItemResponse:
    try:
        plan = create_plan(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="platform.plans.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform",
        result="success",
        metadata={"plan_id": int(plan.get("id", 0)) if plan.get("id") is not None else None, "code": str(plan.get("code", ""))},
    )
    return {"plan": plan}


@router.put("/plans/{plan_id}", response_model=PlanItemResponse)
def update_platform_plan(
    plan_id: int,
    payload: PlanUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_admin)],
) -> PlanItemResponse:
    try:
        plan = update_plan(plan_id, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="platform.plans.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform",
        result="success",
        metadata={"plan_id": plan_id, "code": str(plan.get("code", ""))},
    )
    return {"plan": plan}


@router.get("/quotas", response_model=QuotaListResponse)
def get_platform_quotas(
    _: Annotated[str, Depends(_require_platform_admin)],
) -> QuotaListResponse:
    return {"quotas": list_quotas()}


@router.get("/quotas/consistency", response_model=PlanQuotaConsistencyReportSchema)
def get_platform_quota_consistency(
    _: Annotated[str, Depends(_require_platform_admin)],
) -> PlanQuotaConsistencyReportSchema:
    return get_plan_quota_consistency_report()


@router.put("/quotas/{plan_id}", response_model=QuotaListResponse)
def put_platform_quotas(
    plan_id: int,
    payload: PlanQuotaPayload,
    request: Request,
    actor: Annotated[str, Depends(_require_platform_admin)],
) -> QuotaListResponse:
    try:
        rows = update_plan_quotas(plan_id, payload.quotas)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    log_admin_action(
        actor=actor,
        tenant_id=PLATFORM_TENANT_ID,
        action="platform.quotas.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform",
        result="success",
        metadata={"plan_id": plan_id, "quota_count": len(rows)},
    )
    return {"quotas": rows}


@router.post("/tenants")
def create_platform_tenant(
    request: Request,
    payload: dict[str, str],
    actor: Annotated[str, Depends(_require_platform_admin)],
) -> dict[str, object]:
    tenant_name = str(payload.get("tenant_name", "")).strip()
    admin_email = str(payload.get("admin_email", "")).strip().lower()
    plan_code = str(payload.get("plan_code", "free")).strip().lower() or "free"

    if not tenant_name:
        raise HTTPException(status_code=400, detail="tenant_name is required")
    if not admin_email:
        raise HTTPException(status_code=400, detail="admin_email is required")

    try:
        result = TenantProvisioningService.create_tenant_with_defaults(
            tenant_name=tenant_name,
            admin_email=admin_email,
            plan_code=plan_code,
            actor=actor,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "already exists" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    invite_token = secrets.token_urlsafe(24)
    tenant_data = result.get("tenant") if isinstance(result.get("tenant"), dict) else {}
    created_tenant_id = tenant_data.get("id") if isinstance(tenant_data, dict) else None
    if created_tenant_id is None:
        raise HTTPException(status_code=500, detail="tenant provisioning returned no tenant id")
    log_admin_action(
        actor=actor,
        tenant_id=int(created_tenant_id),
        action="platform.tenants.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform",
        result="success",
        metadata={
            "tenant_id": created_tenant_id,
            "tenant_name": tenant_name,
            "admin_email": admin_email,
            "plan_code": plan_code,
        },
    )
    return {
        "tenant": result["tenant"],
        "plan": result["plan"],
        "subscription": get_tenant_billing_state(int(created_tenant_id)).get("subscription"),
        "billing_state": get_tenant_billing_state(int(created_tenant_id)).get("billing_state"),
        "admin_email": admin_email,
        "invite_token": invite_token,
    }


@router.get("/tenants/{tenant_id}/billing")
def get_platform_tenant_billing_state(
    tenant_id: int,
    _: Annotated[str, Depends(_require_platform_admin)],
) -> dict[str, object]:
    try:
        return get_tenant_billing_state(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tenants/{tenant_id}/billing/subscription/transition")
def transition_platform_tenant_subscription(
    tenant_id: int,
    payload: dict[str, str],
    request: Request,
    actor: Annotated[str, Depends(_require_platform_admin)],
) -> dict[str, object]:
    target_status = str(payload.get("status", "")).strip().lower()
    if not target_status:
        raise HTTPException(status_code=400, detail="status is required")

    try:
        subscription = transition_subscription_status(
            tenant_id,
            target_status,
            actor=actor,
            reason="platform_admin_transition",
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 400
        if "not found" in detail:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="platform.billing.subscription.transition",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform",
        result="success",
        metadata={"tenant_id": int(tenant_id), "target_status": target_status},
    )
    return {
        "subscription": subscription,
        "billing_state": get_tenant_billing_state(tenant_id).get("billing_state"),
    }


@router.post("/tenants/{tenant_id}/billing/subscription/plan-change")
def change_platform_tenant_subscription_plan(
    tenant_id: int,
    payload: dict[str, str],
    request: Request,
    actor: Annotated[str, Depends(_require_platform_admin)],
) -> dict[str, object]:
    plan_code = str(payload.get("plan_code", "")).strip().lower()
    if not plan_code:
        raise HTTPException(status_code=400, detail="plan_code is required")

    effective = str(payload.get("effective", "auto")).strip().lower() or "auto"

    try:
        changed = change_subscription_plan(
            tenant_id,
            plan_code,
            effective=effective,
            actor=actor,
            reason="platform_admin_plan_change",
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 400
        if "not found" in detail:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="platform.billing.subscription.plan_change",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform",
        result="success",
        metadata={
            "tenant_id": int(tenant_id),
            "old_plan": changed.get("old_plan"),
            "new_plan": changed.get("new_plan"),
            "effective": changed.get("effective"),
        },
    )
    return {
        "subscription": changed.get("subscription"),
        "effective": changed.get("effective"),
        "billing_state": get_tenant_billing_state(tenant_id).get("billing_state"),
    }
