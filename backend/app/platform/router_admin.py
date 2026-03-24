from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor
from app.platform.billing import service as billing_service
from app.platform.feature_flags import service as flags_service
from app.platform.jobs import service as jobs_service
from app.platform.notifications import service as notifications_service
from app.platform.schemas import (
    FeatureFlagRead,
    FeatureFlagSetRequest,
    JobEnqueueRequest,
    JobRead,
    NotificationRead,
    NotificationRequest,
    PlanCreateRequest,
    PlanRead,
    SubscriptionAssignRequest,
    SubscriptionRead,
    TenantCreateRequest,
    TenantMapRequest,
    TenantPlatformRead,
    TenantSettingsPatchRequest,
    TenantSuspendRequest,
    UsageCounterIncrementRequest,
    UsageCounterRead,
)
from app.platform.tenant import service as tenant_service

router = APIRouter(prefix="/api/v1/admin", tags=["platform-core-admin"])


Actor = Annotated[str, Depends(get_actor)]


def _audit(request: Request, actor: str, action: str, tenant_id: int, metadata: dict[str, object] | None = None) -> None:
    log_admin_action(
        actor=actor,
        tenant_id=int(tenant_id),
        action=action,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="platform-core",
        result="success",
        metadata=metadata or {},
    )


@router.post("/tenants", response_model=TenantPlatformRead, status_code=201)
def create_tenant(request: Request, payload: TenantCreateRequest, actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.create_tenant(payload.slug, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.create", int(row["tenant_id"]), {"slug": payload.slug})
    return TenantPlatformRead.model_validate(row)


@router.get("/tenants/{tenant_id}", response_model=TenantPlatformRead)
def get_tenant_profile(tenant_id: int, _actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.get_tenant_profile(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TenantPlatformRead.model_validate(row)


@router.patch("/tenants/{tenant_id}/settings", response_model=TenantPlatformRead)
def patch_tenant_settings(
    tenant_id: int,
    payload: TenantSettingsPatchRequest,
    request: Request,
    actor: Actor,
) -> TenantPlatformRead:
    try:
        row = tenant_service.patch_settings(tenant_id, payload.settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.settings.patch", tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.put("/tenants/{tenant_id}/quotas", response_model=TenantPlatformRead)
def set_tenant_quotas(tenant_id: int, payload: TenantMapRequest, request: Request, actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.set_quotas(tenant_id, payload.values)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.quotas.put", tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.put("/tenants/{tenant_id}/limits", response_model=TenantPlatformRead)
def set_tenant_limits(tenant_id: int, payload: TenantMapRequest, request: Request, actor: Actor) -> TenantPlatformRead:
    try:
        row = tenant_service.set_limits(tenant_id, payload.values)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.limits.put", tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.post("/tenants/{tenant_id}/suspension", response_model=TenantPlatformRead)
def set_tenant_suspension(
    tenant_id: int,
    payload: TenantSuspendRequest,
    request: Request,
    actor: Actor,
) -> TenantPlatformRead:
    try:
        row = tenant_service.set_suspended(tenant_id, payload.suspended)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.tenant.suspension.set", tenant_id, {"suspended": payload.suspended})
    return TenantPlatformRead.model_validate(row)


@router.put("/features/{module}/{key}", response_model=FeatureFlagRead)
def set_platform_feature(module: str, key: str, payload: FeatureFlagSetRequest, request: Request, actor: Actor) -> FeatureFlagRead:
    row = flags_service.set_platform_feature(module, key, payload.enabled)
    _audit(request, actor, "platform_core.feature.platform.set", 1, {"module": module, "key": key})
    return FeatureFlagRead.model_validate(row)


@router.put("/tenants/{tenant_id}/features/{module}/{key}", response_model=FeatureFlagRead)
def set_tenant_feature(
    tenant_id: int,
    module: str,
    key: str,
    payload: FeatureFlagSetRequest,
    request: Request,
    actor: Actor,
) -> FeatureFlagRead:
    row = flags_service.set_tenant_feature(tenant_id, module, key, payload.enabled)
    _audit(request, actor, "platform_core.feature.tenant.set", tenant_id, {"module": module, "key": key})
    return FeatureFlagRead.model_validate(row)


@router.post("/billing/plans", response_model=PlanRead, status_code=201)
def create_plan(payload: PlanCreateRequest, request: Request, actor: Actor) -> PlanRead:
    try:
        row = billing_service.create_plan(payload.code, payload.name, payload.price_cents, payload.features, payload.limits)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.billing.plan.create", 1, {"code": payload.code})
    return PlanRead.model_validate(row)


@router.get("/billing/plans", response_model=list[PlanRead])
def list_plans(_actor: Actor) -> list[PlanRead]:
    return [PlanRead.model_validate(item) for item in billing_service.list_plans()]


@router.put("/tenants/{tenant_id}/billing/subscription", response_model=SubscriptionRead)
def assign_subscription(
    tenant_id: int,
    payload: SubscriptionAssignRequest,
    request: Request,
    actor: Actor,
) -> SubscriptionRead:
    try:
        row = billing_service.assign_plan(tenant_id, payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.billing.subscription.assign", tenant_id, {"plan_code": payload.plan_code})
    return SubscriptionRead.model_validate(row)


@router.post("/tenants/{tenant_id}/billing/usage/{metric}", response_model=UsageCounterRead)
def increment_usage(
    tenant_id: int,
    metric: str,
    payload: UsageCounterIncrementRequest,
    request: Request,
    actor: Actor,
) -> UsageCounterRead:
    row = billing_service.increment_usage(tenant_id, metric, payload.value)
    _audit(request, actor, "platform_core.billing.usage.increment", tenant_id, {"metric": metric, "value": payload.value})
    return UsageCounterRead.model_validate(row)


@router.post("/jobs", response_model=JobRead, status_code=201)
def enqueue_job(payload: JobEnqueueRequest, request: Request, actor: Actor) -> JobRead:
    row = jobs_service.enqueue_job(payload.tenant_id, payload.job_type, payload.payload, max_retries=payload.max_retries)
    _audit(request, actor, "platform_core.jobs.enqueue", payload.tenant_id, {"job_type": payload.job_type})
    return JobRead.model_validate(row)


@router.post("/notifications", response_model=NotificationRead, status_code=201)
def dispatch_notification(payload: NotificationRequest, request: Request, actor: Actor) -> NotificationRead:
    try:
        row = notifications_service.dispatch_notification(
            tenant_id=payload.tenant_id,
            channel=payload.channel,
            target=payload.target,
            payload=payload.payload,
            subject=payload.subject,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(request, actor, "platform_core.notification.dispatch", payload.tenant_id, {"channel": payload.channel})
    return NotificationRead.model_validate(row)
