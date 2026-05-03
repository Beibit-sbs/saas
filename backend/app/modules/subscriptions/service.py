"""Phase LXXVII — Subscriptions in-memory service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_store: Dict[str, Dict[str, Any]] = {}
_seq = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id() -> str:
    global _seq
    _seq += 1
    return f"sub_{_seq}"


def clear_subscriptions_state() -> None:
    global _seq
    _store.clear()
    _seq = 0


def create_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    # Only one active subscription per tenant
    for existing in _store.values():
        if existing["tenant_id"] == data["tenant_id"] and existing["status"] == "active":
            raise ValueError(
                f"Tenant {data['tenant_id']} already has an active subscription"
            )
    sub_id = _next_id()
    now = _now()
    row: Dict[str, Any] = {
        "id": sub_id,
        "tenant_id": data["tenant_id"],
        "plan_id": data["plan_id"],
        "status": "active",
        "notes": data.get("notes"),
        "created_at": now,
        "updated_at": now,
    }
    _store[sub_id] = row
    return dict(row)


def list_subscriptions(
    *,
    tenant_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows = list(_store.values())
    if tenant_id is not None:
        rows = [r for r in rows if r["tenant_id"] == tenant_id]
    if plan_id is not None:
        rows = [r for r in rows if r["plan_id"] == plan_id]
    if status is not None:
        rows = [r for r in rows if r["status"] == status]
    return [dict(r) for r in rows]


def get_subscription_by_id(sub_id: str) -> Dict[str, Any]:
    if sub_id not in _store:
        raise KeyError(f"Subscription {sub_id!r} not found")
    return dict(_store[sub_id])


def cancel_subscription(sub_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    row = get_subscription_by_id(sub_id)
    if row["status"] != "active":
        raise ValueError(f"Subscription {sub_id!r} is not active (status={row['status']})")
    row["status"] = "cancelled"
    row["notes"] = reason or row.get("notes")
    row["updated_at"] = _now()
    _store[sub_id] = row
    return dict(row)


def upgrade_subscription(
    sub_id: str, new_plan_id: int, notes: Optional[str] = None
) -> Dict[str, Any]:
    row = get_subscription_by_id(sub_id)
    if row["status"] != "active":
        raise ValueError(f"Subscription {sub_id!r} is not active (status={row['status']})")
    if row["plan_id"] == new_plan_id:
        raise ValueError(f"Subscription {sub_id!r} is already on plan {new_plan_id}")
    row["plan_id"] = new_plan_id
    if notes:
        row["notes"] = notes
    row["updated_at"] = _now()
    _store[sub_id] = row
    return dict(row)


def get_subscriptions_stats() -> Dict[str, Any]:
    rows = list(_store.values())
    active = sum(1 for r in rows if r["status"] == "active")
    cancelled = sum(1 for r in rows if r["status"] == "cancelled")
    expired = sum(1 for r in rows if r["status"] == "expired")
    return {
        "total": len(rows),
        "active": active,
        "cancelled": cancelled,
        "expired": expired,
    }
