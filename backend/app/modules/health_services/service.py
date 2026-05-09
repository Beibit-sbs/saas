"""A-023.3 — Health Services service skeleton (L2).

Tenant-scoped health service intake and referral metadata only.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


SERVICE_STATES: frozenset[str] = frozenset(
    {"INTAKE", "SCHEDULED", "IN_SERVICE", "COMPLETED", "REFERRED"}
)


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def create_service_case(
    tenant_id: int,
    *,
    student_id: str,
    service_type: str,
    notes: str,
) -> dict:
    """Create health service intake record in INTAKE state."""
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if not service_type:
        raise ValueError("service_type is required")
    if not notes:
        raise ValueError("notes is required")

    row = create_entity_for_tenant(
        tenant_id,
        "health_service_cases",
        {
            "student_id": student_id,
            "service_type": service_type,
            "notes": notes,
            "status": "INTAKE",
            "tenant_id": tenant_id,
        },
    )
    return {"case_id": row["id"], "status": "INTAKE"}


def update_service_status(
    tenant_id: int,
    *,
    case_id: str,
    status: str,
) -> dict:
    """Update service case status explicitly (no automatic escalation)."""
    _validate_tenant(tenant_id)
    if status not in SERVICE_STATES:
        raise ValueError(f"status must be one of {sorted(SERVICE_STATES)}")

    for row in list_entities_for_tenant(tenant_id, "health_service_cases"):
        if row.get("id") == case_id:
            row["status"] = status
            return {"case_id": case_id, "status": status}

    raise ValueError(f"Service case {case_id!r} not found for tenant {tenant_id}")


def list_service_cases(
    tenant_id: int,
    *,
    status: str | None = None,
    student_id: str | None = None,
) -> list[dict]:
    """List tenant-scoped service cases with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "health_service_cases")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if student_id:
        rows = [row for row in rows if row.get("student_id") == student_id]
    return rows