"""A-023.4 — Contracts Legal Repository service skeleton (L2).

Tracks tenant-scoped contract metadata only. No automatic signing actions.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


CONTRACT_STATES: frozenset[str] = frozenset(
    {"DRAFT", "UNDER_REVIEW", "PENDING_SIGNATURE", "SIGNED", "ARCHIVED"}
)
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_AUTOMATIC_CONTRACT_SIGNING",
        "NO_AUTOMATIC_VENDOR_ONBOARDING",
        "NO_AUTOMATIC_BUDGET_MUTATION",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def register_contract(
    tenant_id: int,
    *,
    contract_code: str,
    counterpart: str,
    summary: str,
) -> dict:
    """Register contract metadata in DRAFT status."""
    _validate_tenant(tenant_id)
    if not contract_code:
        raise ValueError("contract_code is required")
    if not counterpart:
        raise ValueError("counterpart is required")
    if not summary:
        raise ValueError("summary is required")

    row = create_entity_for_tenant(
        tenant_id,
        "contracts_legal_repository_records",
        {
            "contract_code": contract_code,
            "counterpart": counterpart,
            "summary": summary,
            "status": "DRAFT",
            "tenant_id": tenant_id,
        },
    )
    return {"contract_id": row["id"], "status": "DRAFT"}


def set_contract_status(
    tenant_id: int,
    *,
    contract_id: str,
    status: str,
) -> dict:
    """Set status explicitly. No automatic signature execution is performed."""
    _validate_tenant(tenant_id)
    if status not in CONTRACT_STATES:
        raise ValueError(f"status must be one of {sorted(CONTRACT_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "contracts_legal_repository_records"):
        if row.get("id") == contract_id:
            row["status"] = status
            return {"contract_id": contract_id, "status": status}

    raise ValueError(f"Contract {contract_id!r} not found for tenant {tenant_id}")


def list_contracts(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped contract records with optional status filter."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "contracts_legal_repository_records")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
