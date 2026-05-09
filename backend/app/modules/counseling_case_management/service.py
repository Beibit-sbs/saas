"""A-023.2 — Counseling Case Management service skeleton (L2).

Tenant-scoped counseling case lifecycle with minimal FSM and event hooks.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher


CASE_STATES: frozenset[str] = frozenset(
    {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
)

_CASE_FSM: dict[str, frozenset[str]] = {
    "OPEN": frozenset({"IN_PROGRESS"}),
    "IN_PROGRESS": frozenset({"RESOLVED"}),
    "RESOLVED": frozenset({"CLOSED"}),
}


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        publisher = EventPublisher()
        publisher.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_case(tenant_id: int, case_id: str) -> dict:
    for row in list_entities_for_tenant(tenant_id, "counseling_cases"):
        if row.get("id") == case_id:
            return row
    raise ValueError(f"Case {case_id!r} not found for tenant {tenant_id}")


def _assert_transition(current: str, target: str) -> None:
    allowed = _CASE_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition case from {current!r} to {target!r}. "
            f"Allowed: {sorted(allowed)}"
        )


def create_case(
    tenant_id: int,
    *,
    student_id: str,
    concern_type: str,
    summary: str,
) -> dict:
    """Create a counseling case in OPEN state."""
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if not concern_type:
        raise ValueError("concern_type is required")
    if not summary:
        raise ValueError("summary is required")

    row = create_entity_for_tenant(
        tenant_id,
        "counseling_cases",
        {
            "student_id": student_id,
            "concern_type": concern_type,
            "summary": summary,
            "status": "OPEN",
            "tenant_id": tenant_id,
        },
    )
    return {"case_id": row["id"], "status": "OPEN"}


def assign_case(tenant_id: int, *, case_id: str, counselor_id: str) -> dict:
    """Assign an OPEN case and move it to IN_PROGRESS."""
    _validate_tenant(tenant_id)
    if not counselor_id:
        raise ValueError("counselor_id is required")
    case = _get_case(tenant_id, case_id)
    _assert_transition(case["status"], "IN_PROGRESS")
    case["status"] = "IN_PROGRESS"
    case["counselor_id"] = counselor_id
    _fire(tenant_id, "counseling_case.assigned", {"case_id": case_id, "student_id": case.get("student_id")})
    return {"case_id": case_id, "status": "IN_PROGRESS"}


def resolve_case(tenant_id: int, *, case_id: str, resolution_notes: str) -> dict:
    """Resolve an IN_PROGRESS case."""
    _validate_tenant(tenant_id)
    if not resolution_notes:
        raise ValueError("resolution_notes is required")
    case = _get_case(tenant_id, case_id)
    _assert_transition(case["status"], "RESOLVED")
    case["status"] = "RESOLVED"
    case["resolution_notes"] = resolution_notes
    _fire(tenant_id, "counseling_case.resolved", {"case_id": case_id})
    return {"case_id": case_id, "status": "RESOLVED"}


def close_case(tenant_id: int, *, case_id: str) -> dict:
    """Close a RESOLVED case."""
    _validate_tenant(tenant_id)
    case = _get_case(tenant_id, case_id)
    _assert_transition(case["status"], "CLOSED")
    case["status"] = "CLOSED"
    _fire(tenant_id, "counseling_case.closed", {"case_id": case_id})
    return {"case_id": case_id, "status": "CLOSED"}


def list_cases(
    tenant_id: int,
    *,
    status: str | None = None,
    student_id: str | None = None,
) -> list[dict]:
    """List counseling cases for the tenant with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "counseling_cases")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if student_id:
        rows = [r for r in rows if r.get("student_id") == student_id]
    return rows
