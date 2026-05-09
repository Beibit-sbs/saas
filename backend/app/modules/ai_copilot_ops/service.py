"""A-023.6 — AI Copilot Ops service skeleton (L2)."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


OPS_STATES: frozenset[str] = frozenset({"DRAFT", "ACTIVE", "PAUSED", "ARCHIVED"})
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_AUTONOMOUS_EXECUTION",
        "NO_EXTERNAL_LLM_PROVIDER_CALLS",
        "NO_FAKE_BRAIN_DECISIONS",
        "NO_SYNTHETIC_KPI_DASHBOARD_VALUES",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_ops_profile(
    tenant_id: int,
    *,
    profile_name: str,
    scope: str,
    policy_note: str,
) -> dict:
    """Register ops profile metadata in DRAFT state."""
    _validate_tenant(tenant_id)
    if not profile_name:
        raise ValueError("profile_name is required")
    if not scope:
        raise ValueError("scope is required")
    if not policy_note:
        raise ValueError("policy_note is required")

    row = create_entity_for_tenant(
        tenant_id,
        "ai_copilot_ops_profiles",
        {
            "profile_name": profile_name,
            "scope": scope,
            "policy_note": policy_note,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"profile_id": row["id"], "status": "DRAFT"}


def list_ops_profiles(tenant_id: int, *, status: str | None = None) -> list[dict]:
    """List tenant-scoped ops profiles with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "ai_copilot_ops_profiles")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
