"""A-023.3 — Platform Health service skeleton (L2).

Provides tenant-scoped health checks registry metadata without auto-remediation.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


HEALTH_STATES: frozenset[str] = frozenset({"HEALTHY", "DEGRADED", "OUTAGE"})


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_health_signal(
    tenant_id: int,
    *,
    component: str,
    status: str,
    summary: str,
) -> dict:
    """Register a platform health signal snapshot for a tenant."""
    _validate_tenant(tenant_id)
    if not component:
        raise ValueError("component is required")
    if status not in HEALTH_STATES:
        raise ValueError(f"status must be one of {sorted(HEALTH_STATES)}")
    if not summary:
        raise ValueError("summary is required")

    row = create_entity_for_tenant(
        tenant_id,
        "platform_health_signals",
        {
            "component": component,
            "status": status,
            "summary": summary,
            "tenant_id": tenant_id,
        },
    )
    return {"signal_id": row["id"], "status": status}


def list_health_signals(
    tenant_id: int,
    *,
    status: str | None = None,
    component: str | None = None,
) -> list[dict]:
    """List tenant-scoped platform health signals with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "platform_health_signals")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if component:
        rows = [row for row in rows if row.get("component") == component]
    return rows
