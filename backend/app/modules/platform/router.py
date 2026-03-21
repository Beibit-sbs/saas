from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.observability.security_signals import record_security_signal
from app.modules.plans.schemas import PlanCreatePayload, PlanItemResponse, PlanListResponse, PlanUpdatePayload
from app.modules.plans.service import create_plan, list_plans, update_plan
from app.modules.quotas.schemas import PlanQuotaPayload, QuotaListResponse
from app.modules.quotas.service import list_quotas, update_plan_quotas
from app.modules.rbac.security import get_actor, resolve_current_user_claims
from app.modules.rbac.service import is_platform_admin
from app.modules.tenants.provisioning_service import TenantProvisioningService

router = APIRouter(prefix="/platform", tags=["platform"])


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
        tenant_id=1,
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
        tenant_id=1,
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
        tenant_id=1,
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
    log_admin_action(
        actor=actor,
        tenant_id=int(created_tenant_id) if created_tenant_id is not None else 1,
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
        "admin_email": admin_email,
        "invite_token": invite_token,
    }
