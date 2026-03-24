from __future__ import annotations

from fastapi import APIRouter

from app.platform.billing import service as billing_service
from app.platform.feature_flags import service as flags_service
from app.platform.schemas import FeatureFlagRead, SubscriptionRead, TenantPlatformRead
from app.platform.tenant import service as tenant_service

router = APIRouter(prefix="/api/v1/public", tags=["platform-core-public"])


@router.get("/tenants/{tenant_id}", response_model=TenantPlatformRead)
def get_tenant_public(tenant_id: int) -> TenantPlatformRead:
    row = tenant_service.get_tenant_profile(tenant_id)
    return TenantPlatformRead.model_validate(row)


@router.get("/tenants/{tenant_id}/features", response_model=list[FeatureFlagRead])
def get_tenant_features(tenant_id: int) -> list[FeatureFlagRead]:
    return [FeatureFlagRead.model_validate(item) for item in flags_service.list_tenant_features(tenant_id)]


@router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionRead | None)
def get_subscription(tenant_id: int) -> SubscriptionRead | None:
    row = billing_service.get_subscription(tenant_id)
    if row is None:
        return None
    return SubscriptionRead.model_validate(row)
