"""A-023.6 — Developer Portal service skeleton (L2)."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


PORTAL_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "MAINTENANCE", "RETIRED"})
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_FAKE_OBSERVABILITY_ALERTS",
        "NO_FAKE_KPI_DASHBOARD_VALUES",
        "NO_AUTONOMOUS_EXECUTION",
        "NO_EXTERNAL_PROVIDER_REGISTRATION",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_portal_channel(
    tenant_id: int,
    *,
    channel_name: str,
    audience: str,
    governance_note: str,
) -> dict:
    """Register developer portal channel metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not channel_name:
        raise ValueError("channel_name is required")
    if not audience:
        raise ValueError("audience is required")
    if not governance_note:
        raise ValueError("governance_note is required")

    row = create_entity_for_tenant(
        tenant_id,
        "developer_portal_channels",
        {
            "channel_name": channel_name,
            "audience": audience,
            "governance_note": governance_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"channel_id": row["id"], "status": "DRAFT"}


def list_portal_channels(tenant_id: int, *, status: str | None = None) -> list[dict]:
    """List tenant-scoped developer portal channels."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "developer_portal_channels")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
