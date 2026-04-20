from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

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
from app.modules.rbac.security import get_actor
from app.platform.billing import service as platform_billing_service

router = APIRouter(prefix="/api/admin/billing", tags=["billing"])


@router.post("/plans", response_model=BillingPlanMutationReadSchema, status_code=201)
def create_billing_plan(
    payload: BillingPlanCreateRequestSchema,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
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
def list_billing_plans(_: Annotated[str, Depends(get_actor)]) -> list[BillingPlanReadSchema]:
    return [BillingPlanReadSchema.model_validate(item) for item in platform_billing_service.list_plans()]


@router.get("/tenants/{tenant_id}/state", response_model=BillingStateReadSchema)
def get_billing_state(
    tenant_id: int,
    _: Annotated[str, Depends(get_actor)],
) -> BillingStateReadSchema:
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
) -> BillingStateReadSchema:
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
) -> BillingPlanChangeResponseSchema:
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
) -> BillingSubscriptionMutationReadSchema:
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
) -> BillingUsageCounterReadSchema:
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
    _: Annotated[str, Depends(get_actor)],
    since_iso: Annotated[str | None, Query()] = None,
) -> BillingUsageReadSchema:
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
    _: Annotated[str, Depends(get_actor)],
    status: Annotated[str | None, Query()] = None,
) -> BillingDelinquencyListResponseSchema:
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
    _: Annotated[str, Depends(get_actor)],
) -> BillingDelinquencyRecordReadSchema:
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
) -> BillingDelinquencyRecordReadSchema:
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
) -> BillingDelinquencyRecordReadSchema:
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
) -> BillingDelinquencyRecordReadSchema:
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
    _: Annotated[str, Depends(get_actor)],
) -> BillingDunningPolicySchema:
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
) -> BillingDunningPolicySchema:
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
    _: Annotated[str, Depends(get_actor)],
) -> BillingDelinquencyDashboardSchema:
    try:
        dashboard = get_delinquency_dashboard(int(tenant_id))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return BillingDelinquencyDashboardSchema.model_validate(dashboard)
