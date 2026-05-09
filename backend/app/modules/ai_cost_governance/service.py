"""A-023.5 — AI Cost Governance service skeleton (L2).

Tracks tenant-scoped governance policy metadata only.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


POLICY_STATES: frozenset[str] = frozenset(
    {"DRAFT", "ACTIVE", "SUSPENDED", "RETIRED"}
)
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_FAKE_MINISTRY_SUBMISSION",
        "NO_FAKE_COMPLIANCE_SCORE",
        "NO_SYNTHETIC_KPI_DASHBOARD_VALUES",
        "NO_AUTOMATIC_POLICY_ENFORCEMENT",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_cost_policy(
    tenant_id: int,
    *,
    policy_name: str,
    budget_scope: str,
    governance_note: str,
) -> dict:
    """Register AI cost-governance policy metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not policy_name:
        raise ValueError("policy_name is required")
    if not budget_scope:
        raise ValueError("budget_scope is required")
    if not governance_note:
        raise ValueError("governance_note is required")

    row = create_entity_for_tenant(
        tenant_id,
        "ai_cost_governance_policies",
        {
            "policy_name": policy_name,
            "budget_scope": budget_scope,
            "governance_note": governance_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"policy_id": row["id"], "status": "DRAFT"}


def set_policy_status(
    tenant_id: int,
    *,
    policy_id: str,
    status: str,
) -> dict:
    """Set governance policy status explicitly, without auto-application."""
    _validate_tenant(tenant_id)
    if status not in POLICY_STATES:
        raise ValueError(f"status must be one of {sorted(POLICY_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "ai_cost_governance_policies"):
        if row.get("id") == policy_id:
            row["status"] = status
            return {"policy_id": policy_id, "status": status}

    raise ValueError(f"Policy {policy_id!r} not found for tenant {tenant_id}")


def list_policies(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped governance policy metadata entries."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "ai_cost_governance_policies")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
