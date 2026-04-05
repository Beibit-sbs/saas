from __future__ import annotations

from fastapi import HTTPException

from app.modules.billing.service import get_tenant_subscription


WRITE_ALLOWED_STATUSES = {"trial", "active"}


def get_legacy_subscription(tenant_id: int) -> dict[str, object] | None:
    return get_tenant_subscription(int(tenant_id))


def has_legacy_subscription(tenant_id: int) -> bool:
    return get_legacy_subscription(int(tenant_id)) is not None


def assert_legacy_billing_write_allowed(
    tenant_id: int,
    *,
    action: str,
    subscription: dict[str, object] | None = None,
) -> None:
    current = subscription if subscription is not None else get_legacy_subscription(int(tenant_id))
    if current is None:
        raise HTTPException(status_code=403, detail="billing_required: legacy subscription state unavailable")

    status = str(current.get("status", "trial")).strip().lower()
    if status not in WRITE_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=403,
            detail=f"billing_required: tenant subscription is '{status}' (read-only mode)",
        )
