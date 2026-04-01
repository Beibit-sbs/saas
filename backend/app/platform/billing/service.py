from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.modules.billing.service import (
    change_subscription_plan,
    get_tenant_subscription,
    transition_subscription_status,
)
from app.modules.plans.service import list_plans as list_module_plans
from app.modules.quotas.service import get_plan_quotas
from app.modules.usage.service import get_usage_sum, record_usage_event


LEGACY_BILLING_LAYER_MESSAGE = (
    "platform-core billing is legacy; use app.modules.billing/service as the canonical source of truth"
)


def create_plan(code: str, name: str, price_cents: int, features: dict[str, bool], limits: dict[str, int]) -> dict[str, Any]:
    raise RuntimeError(
        f"{LEGACY_BILLING_LAYER_MESSAGE}; plan creation must go through /platform/plans"
    )


def list_plans() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_module_plans(include_inactive=True):
        plan_id = int(item["id"])
        rows.append(
            {
                "id": plan_id,
                "code": str(item["code"]),
                "name": str(item["name"]),
                "price_cents": 0,
                "features": {},
                "limits": get_plan_quotas(plan_id),
                "active": bool(item.get("active", True)),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return rows


def assign_plan(tenant_id: int, plan_code: str) -> dict[str, Any]:
    current = get_tenant_subscription(int(tenant_id))
    if current is not None and str(current.get("status", "")).strip().lower() == "cancelled":
        raise ValueError("cancelled subscriptions cannot be reactivated without a new subscription cycle")

    changed = change_subscription_plan(int(tenant_id), plan_code, effective="immediate")
    status = str((changed.get("subscription") or {}).get("status", "trial")).lower()
    if status != "active":
        return transition_subscription_status(int(tenant_id), "active")
    return dict(changed.get("subscription") or {})


def get_subscription(tenant_id: int) -> dict[str, Any] | None:
    return get_tenant_subscription(int(tenant_id))


def increment_usage(tenant_id: int, metric: str, value: int, period_key: str = "current") -> dict[str, Any]:
    del period_key
    event = record_usage_event(int(tenant_id), metric, int(value))
    return {
        "tenant_id": int(tenant_id),
        "metric": str(metric).strip().lower(),
        "period_key": "event_log",
        "value": get_usage_sum(int(tenant_id), str(metric).strip().lower()),
        "updated_at": str(event["created_at"]),
    }
