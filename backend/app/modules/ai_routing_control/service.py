"""A-023.6 — AI Routing Control service skeleton (L2)."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


ROUTING_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "SUSPENDED", "RETIRED"})
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_AUTONOMOUS_EXECUTION",
        "NO_EXTERNAL_LLM_PROVIDER_CALLS",
        "NO_FAKE_BRAIN_DECISIONS",
        "NO_SYNTHETIC_OBSERVABILITY_ALERTS",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_routing_policy(
    tenant_id: int,
    *,
    policy_name: str,
    route_scope: str,
    governance_note: str,
) -> dict:
    """Register routing policy metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not policy_name:
        raise ValueError("policy_name is required")
    if not route_scope:
        raise ValueError("route_scope is required")
    if not governance_note:
        raise ValueError("governance_note is required")

    row = create_entity_for_tenant(
        tenant_id,
        "ai_routing_control_policies",
        {
            "policy_name": policy_name,
            "route_scope": route_scope,
            "governance_note": governance_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"policy_id": row["id"], "status": "DRAFT"}


def list_routing_policies(tenant_id: int, *, status: str | None = None) -> list[dict]:
    """List tenant-scoped routing policies with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "ai_routing_control_policies")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
