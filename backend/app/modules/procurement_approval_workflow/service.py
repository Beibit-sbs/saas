"""A-023.4 — Procurement Approval Workflow service skeleton (L2).

Tracks procurement request workflow states with explicit operator transitions.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


WORKFLOW_STATES: frozenset[str] = frozenset(
    {"REQUESTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PO_READY"}
)
SAFETY_GUARDS: frozenset[str] = frozenset(
    {
        "NO_AUTOMATIC_PROCUREMENT_APPROVAL",
        "NO_AUTOMATIC_PAYMENT_EXECUTION",
        "NO_AUTOMATIC_BUDGET_MUTATION",
        "NO_AUTOMATIC_VENDOR_ONBOARDING",
    }
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def create_procurement_request(
    tenant_id: int,
    *,
    request_code: str,
    cost_center: str,
    justification: str,
) -> dict:
    """Create request in REQUESTED state without automated approvals."""
    _validate_tenant(tenant_id)
    if not request_code:
        raise ValueError("request_code is required")
    if not cost_center:
        raise ValueError("cost_center is required")
    if not justification:
        raise ValueError("justification is required")

    row = create_entity_for_tenant(
        tenant_id,
        "procurement_approval_workflow_requests",
        {
            "request_code": request_code,
            "cost_center": cost_center,
            "justification": justification,
            "status": "REQUESTED",
            "tenant_id": tenant_id,
        },
    )
    return {"request_id": row["id"], "status": "REQUESTED"}


def set_request_status(
    tenant_id: int,
    *,
    request_id: str,
    status: str,
) -> dict:
    """Set workflow status explicitly. No auto-approval behavior exists."""
    _validate_tenant(tenant_id)
    if status not in WORKFLOW_STATES:
        raise ValueError(f"status must be one of {sorted(WORKFLOW_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "procurement_approval_workflow_requests"):
        if row.get("id") == request_id:
            row["status"] = status
            return {"request_id": request_id, "status": status}

    raise ValueError(f"Procurement request {request_id!r} not found for tenant {tenant_id}")


def list_requests(
    tenant_id: int,
    *,
    status: str | None = None,
) -> list[dict]:
    """List tenant-scoped procurement workflow requests."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "procurement_approval_workflow_requests")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
