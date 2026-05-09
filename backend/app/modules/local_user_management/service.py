"""A-023.3 — Local User Management service skeleton (L2).

Defines tenant-scoped local user profile operations without automatic lockouts.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


ACCOUNT_STATES: frozenset[str] = frozenset({"ACTIVE", "SUSPENDED", "ARCHIVED"})


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def create_local_user(
    tenant_id: int,
    *,
    username: str,
    email: str,
    display_name: str,
) -> dict:
    """Create local user metadata in ACTIVE state."""
    _validate_tenant(tenant_id)
    if not username:
        raise ValueError("username is required")
    if not email:
        raise ValueError("email is required")
    if not display_name:
        raise ValueError("display_name is required")

    row = create_entity_for_tenant(
        tenant_id,
        "local_user_accounts",
        {
            "username": username,
            "email": email,
            "display_name": display_name,
            "status": "ACTIVE",
            "tenant_id": tenant_id,
        },
    )
    return {"user_id": row["id"], "status": "ACTIVE"}


def update_account_status(
    tenant_id: int,
    *,
    user_id: str,
    status: str,
) -> dict:
    """Update account status with explicit, non-automatic transition calls."""
    _validate_tenant(tenant_id)
    if status not in ACCOUNT_STATES:
        raise ValueError(f"status must be one of {sorted(ACCOUNT_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "local_user_accounts"):
        if row.get("id") == user_id:
            row["status"] = status
            return {"user_id": user_id, "status": status}

    raise ValueError(f"Local user {user_id!r} not found for tenant {tenant_id}")


def list_local_users(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped local users with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "local_user_accounts")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
