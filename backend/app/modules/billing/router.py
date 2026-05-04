from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.tenant import get_current_tenant
from app.modules.auth.token_service import parse_access_token_from_request
from app.modules.audit.service import log_admin_action
from app.modules.billing.schemas import (
    BillingDelinquencyDashboardSchema,
    BillingDelinquencyEscalateRequestSchema,
    BillingDelinquencyListResponseSchema,
    BillingDelinquencyRecordReadSchema,
    BillingDelinquencyReminderRequestSchema,
    BillingDelinquencyResolveRequestSchema,
    BillingDunningPolicySchema,
    BillingPlanCreateRequestSchema,
    BillingPlanChangeRequestSchema,
    BillingPlanChangeResponseSchema,
    BillingPlanMutationReadSchema,
    BillingPlanReadSchema,
    BillingPlanUpdateRequestSchema,
    BillingStateReadSchema,
    BillingSubscriptionAssignRequestSchema,
    BillingSubscriptionMutationReadSchema,
    BillingTransitionRequestSchema,
    BillingUsageCounterReadSchema,
    BillingUsageIncrementRequestSchema,
    BillingUsageReadSchema,
)
from app.modules.billing.service import (
    change_subscription_plan,
    escalate_delinquency_record,
    get_delinquency_dashboard,
    get_delinquency_record,
    get_dunning_policy,
    get_tenant_billing_state,
    get_usage_snapshot,
    list_delinquency_records,
    resolve_delinquency_record,
    send_delinquency_reminder,
    transition_subscription_status,
    update_dunning_policy,
)
from app.modules.rbac.security import get_actor, permission_dependency
from app.platform.billing import service as platform_billing_service

router = APIRouter(prefix="/api/admin/billing", tags=["billing"])


def _platform_override_permission_for_method(method: str) -> str:
    normalized = method.upper()
    if normalized in {"POST", "PUT", "PATCH", "DELETE"}:
        return "platform.admin.write"
    return "platform.admin.read"


def _assert_tenant_access(
    *,
    request: Request,
    actor: str,
    tenant_id: int,
    current_tenant: dict[str, object],
) -> None:
    if int(tenant_id) <= 0:
        raise HTTPException(status_code=400, detail="invalid tenant_id")

    effective_tenant_id = int(current_tenant.get("id", 0) or 0)
    if effective_tenant_id <= 0:
        raise HTTPException(status_code=403, detail="invalid tenant context")

    if int(tenant_id) == effective_tenant_id:
        return

    claims = parse_access_token_from_request(request, request.headers.get("Authorization"))
    if claims is None:
        raise HTTPException(status_code=401, detail="valid authentication is required")

    override_permission = _platform_override_permission_for_method(request.method)
    granted_permissions = {str(item).strip() for item in claims.permissions if str(item).strip()}
    if override_permission not in granted_permissions:
        raise HTTPException(status_code=403, detail="tenant_id_mismatch")

    log_admin_action(
        actor=actor,
        tenant_id=effective_tenant_id,
        action="billing.cross_tenant.override",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={
            "requested_tenant_id": int(tenant_id),
            "effective_tenant_id": effective_tenant_id,
            "required_platform_permission": override_permission,
        },
    )


@router.post("/plans", response_model=BillingPlanMutationReadSchema, status_code=201)
def create_billing_plan(
    payload: BillingPlanCreateRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.manage"))] = None,
) -> BillingPlanMutationReadSchema:
    existing = None
    for item in platform_billing_service.list_plans():
        if str(item.get("code", "")).strip().lower() == payload.code.strip().lower():
            existing = item
            break

    if existing is not None:
        same_payload = (
            str(existing.get("name", "")).strip() == payload.name.strip()
            and int(existing.get("price_cents", 0)) == int(payload.price_cents)
            and dict(existing.get("features") or {}) == dict(payload.features)
            and dict(existing.get("limits") or {}) == dict(payload.limits)
        )
        if not same_payload:
            raise HTTPException(status_code=400, detail=f"plan '{payload.code}' already exists with different payload")
        return BillingPlanMutationReadSchema.model_validate({**existing, "plan": existing, "idempotent_replay": True})

    try:
        created = platform_billing_service.create_plan(
            payload.code,
            payload.name,
            payload.price_cents,
            payload.features,
            payload.limits,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=1,
        action="billing.module.plan.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"code": payload.code},
    )
    return BillingPlanMutationReadSchema.model_validate({**created, "plan": created, "idempotent_replay": False})


@router.get("/plans", response_model=list[BillingPlanReadSchema])
def list_billing_plans(
    _actor: Annotated[str, Depends(get_actor)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.manage"))] = None,
) -> list[BillingPlanReadSchema]:
    return [BillingPlanReadSchema.model_validate(item) for item in platform_billing_service.list_plans()]


@router.patch("/plans/{plan_id}", response_model=BillingPlanReadSchema)
def update_billing_plan(
    plan_id: int,
    payload: BillingPlanUpdateRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.manage"))] = None,
) -> BillingPlanReadSchema:
    updated = platform_billing_service.update_plan(plan_id, name=payload.name, active=payload.active)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Billing plan '{plan_id}' not found")
    log_admin_action(
        actor=actor,
        tenant_id=1,
        action="billing.plan.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"plan_id": plan_id, "name": payload.name, "active": payload.active},
    )
    return BillingPlanReadSchema.model_validate(updated)


@router.get("/tenants/{tenant_id}/state", response_model=BillingStateReadSchema)
def get_billing_state(
    tenant_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.read"))] = None,
) -> BillingStateReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        row = get_tenant_billing_state(int(tenant_id))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingStateReadSchema.model_validate(row)


@router.post("/tenants/{tenant_id}/subscription/transition", response_model=BillingStateReadSchema)
def transition_billing_subscription(
    tenant_id: int,
    payload: BillingTransitionRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingStateReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        transition_subscription_status(
            int(tenant_id),
            payload.status,
            actor=actor,
            reason="billing_module_transition",
        )
        row = get_tenant_billing_state(int(tenant_id))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.subscription.transition",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"target_status": payload.status},
    )
    return BillingStateReadSchema.model_validate(row)


@router.post("/tenants/{tenant_id}/subscription/plan-change", response_model=BillingPlanChangeResponseSchema)
def change_billing_subscription_plan(
    tenant_id: int,
    payload: BillingPlanChangeRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingPlanChangeResponseSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        changed = change_subscription_plan(
            int(tenant_id),
            payload.plan_code,
            effective=payload.effective,
            actor=actor,
            reason="billing_module_plan_change",
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.subscription.plan_change",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"new_plan": payload.plan_code, "effective": payload.effective},
    )
    return BillingPlanChangeResponseSchema.model_validate(changed)


@router.put("/tenants/{tenant_id}/subscription", response_model=BillingSubscriptionMutationReadSchema)
def assign_billing_subscription(
    tenant_id: int,
    payload: BillingSubscriptionAssignRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingSubscriptionMutationReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    existing = platform_billing_service.get_subscription(int(tenant_id))
    if existing is not None and str(existing.get("plan_code", "")).strip().lower() == payload.plan_code.strip().lower():
        log_admin_action(
            actor=actor,
            tenant_id=int(tenant_id),
            action="billing.module.subscription.assign",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="billing",
            result="success",
            metadata={"plan_code": payload.plan_code, "idempotent_replay": True},
        )
        return BillingSubscriptionMutationReadSchema.model_validate(
            {**existing, "subscription": existing, "idempotent_replay": True}
        )

    try:
        assigned = platform_billing_service.assign_plan(int(tenant_id), payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.subscription.assign",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"plan_code": payload.plan_code, "idempotent_replay": False},
    )
    return BillingSubscriptionMutationReadSchema.model_validate(
        {**assigned, "subscription": assigned, "idempotent_replay": False}
    )


@router.post("/tenants/{tenant_id}/usage/{metric}", response_model=BillingUsageCounterReadSchema)
def increment_billing_usage(
    tenant_id: int,
    metric: str,
    payload: BillingUsageIncrementRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingUsageCounterReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    row = platform_billing_service.increment_usage(int(tenant_id), metric, payload.value)
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.usage.increment",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"metric": metric, "value": payload.value},
    )
    return BillingUsageCounterReadSchema.model_validate(row)


@router.get("/tenants/{tenant_id}/usage", response_model=BillingUsageReadSchema)
def get_billing_usage(
    tenant_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.read"))] = None,
    since_iso: Annotated[str | None, Query()] = None,
) -> BillingUsageReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        usage = get_usage_snapshot(int(tenant_id), since_iso=since_iso)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingUsageReadSchema.model_validate({"tenant_id": int(tenant_id), "usage": usage})


@router.get("/tenants/{tenant_id}/delinquency", response_model=BillingDelinquencyListResponseSchema)
def list_tenant_delinquency(
    tenant_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.read"))] = None,
    status: Annotated[str | None, Query()] = None,
) -> BillingDelinquencyListResponseSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        items = list_delinquency_records(int(tenant_id), status=status)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingDelinquencyListResponseSchema.model_validate({"items": items, "total": len(items)})


@router.get("/tenants/{tenant_id}/delinquency/{record_id:int}", response_model=BillingDelinquencyRecordReadSchema)
def get_tenant_delinquency_record(
    tenant_id: int,
    record_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.read"))] = None,
) -> BillingDelinquencyRecordReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        record = get_delinquency_record(int(tenant_id), int(record_id))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingDelinquencyRecordReadSchema.model_validate(record)


@router.post("/tenants/{tenant_id}/delinquency/{record_id:int}/escalate", response_model=BillingDelinquencyRecordReadSchema)
def escalate_tenant_delinquency_record(
    tenant_id: int,
    record_id: int,
    payload: BillingDelinquencyEscalateRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingDelinquencyRecordReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        record = escalate_delinquency_record(int(tenant_id), int(record_id), actor=actor, notes=payload.notes)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.delinquency.escalate",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"record_id": int(record_id)},
    )
    return BillingDelinquencyRecordReadSchema.model_validate(record)


@router.post("/tenants/{tenant_id}/delinquency/{record_id:int}/resolve", response_model=BillingDelinquencyRecordReadSchema)
def resolve_tenant_delinquency_record(
    tenant_id: int,
    record_id: int,
    payload: BillingDelinquencyResolveRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingDelinquencyRecordReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        record = resolve_delinquency_record(
            int(tenant_id),
            int(record_id),
            resolution=payload.resolution,
            actor=actor,
            notes=payload.notes,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.delinquency.resolve",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"record_id": int(record_id), "resolution": payload.resolution},
    )
    return BillingDelinquencyRecordReadSchema.model_validate(record)


@router.post("/tenants/{tenant_id}/delinquency/{record_id:int}/reminder", response_model=BillingDelinquencyRecordReadSchema)
def reminder_tenant_delinquency_record(
    tenant_id: int,
    record_id: int,
    payload: BillingDelinquencyReminderRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingDelinquencyRecordReadSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        record = send_delinquency_reminder(int(tenant_id), int(record_id), actor=actor, notes=payload.notes)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.delinquency.reminder",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"record_id": int(record_id)},
    )
    return BillingDelinquencyRecordReadSchema.model_validate(record)


@router.get("/tenants/{tenant_id}/delinquency/policy", response_model=BillingDunningPolicySchema)
def get_tenant_dunning_policy(
    tenant_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.read"))] = None,
) -> BillingDunningPolicySchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        policy = get_dunning_policy(int(tenant_id))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingDunningPolicySchema.model_validate(policy)


@router.put("/tenants/{tenant_id}/delinquency/policy", response_model=BillingDunningPolicySchema)
def put_tenant_dunning_policy(
    tenant_id: int,
    payload: BillingDunningPolicySchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.write"))] = None,
) -> BillingDunningPolicySchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        policy = update_dunning_policy(int(tenant_id), payload.model_dump(), actor=actor)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action="billing.module.delinquency.policy.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="billing",
        result="success",
        metadata={"tenant_id": int(tenant_id)},
    )
    return BillingDunningPolicySchema.model_validate(policy)


@router.get("/tenants/{tenant_id}/delinquency/dashboard", response_model=BillingDelinquencyDashboardSchema)
def get_tenant_delinquency_dashboard(
    tenant_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    current_tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _perm: Annotated[None, Depends(permission_dependency("billing.admin.read"))] = None,
) -> BillingDelinquencyDashboardSchema:
    _assert_tenant_access(request=request, actor=actor, tenant_id=tenant_id, current_tenant=current_tenant)
    try:
        dashboard = get_delinquency_dashboard(int(tenant_id))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingDelinquencyDashboardSchema.model_validate(dashboard)
