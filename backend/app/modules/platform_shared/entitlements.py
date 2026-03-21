from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.feature_flags.service import list_flags
from app.modules.plans.service import get_plan_by_id
from app.modules.quotas.service import get_plan_quotas
from app.modules.tenants.service import get_tenant


@dataclass(frozen=True)
class TenantEntitlementSnapshot:
    tenant_id: int
    plan_code: str
    quota_limits: dict[str, int] = field(default_factory=dict)
    module_entitlements: dict[str, bool] = field(default_factory=dict)
    runtime_feature_flags: dict[str, bool] = field(default_factory=dict)


_DEFAULT_MODULE_ENTITLEMENTS_BY_PLAN: dict[str, dict[str, bool]] = {
    "free": {
        "identity": True,
        "ai_gateway": True,
        "workflow": False,
        "notifications": False,
        "webhooks": False,
    },
    "pro": {
        "identity": True,
        "ai_gateway": True,
        "workflow": True,
        "notifications": True,
        "webhooks": False,
    },
    "enterprise": {
        "identity": True,
        "ai_gateway": True,
        "workflow": True,
        "notifications": True,
        "webhooks": True,
    },
}


def resolve_tenant_entitlements(tenant_id: int) -> TenantEntitlementSnapshot:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    tenant = get_tenant(normalized_tenant_id)
    if tenant is None:
        raise ValueError("tenant not found")

    plan_id = int(tenant.get("plan_id") or 0)
    plan = get_plan_by_id(plan_id)
    if plan is None:
        raise ValueError("tenant plan not found")

    plan_code = str(plan.get("code", "")).strip().lower()
    module_entitlements = dict(_DEFAULT_MODULE_ENTITLEMENTS_BY_PLAN.get(plan_code, {}))
    quota_limits = {key: int(value) for key, value in get_plan_quotas(plan_id).items()}

    runtime_flags = {
        str(item.get("key", "")).strip(): bool(item.get("enabled", False))
        for item in list_flags(tenant_id=normalized_tenant_id)
        if str(item.get("key", "")).strip()
    }

    return TenantEntitlementSnapshot(
        tenant_id=normalized_tenant_id,
        plan_code=plan_code,
        quota_limits=quota_limits,
        module_entitlements=module_entitlements,
        runtime_feature_flags=runtime_flags,
    )


def is_module_enabled(snapshot: TenantEntitlementSnapshot, module_key: str) -> bool:
    normalized_module_key = str(module_key).strip().lower()
    if not normalized_module_key:
        return False
    return bool(snapshot.module_entitlements.get(normalized_module_key, False))
