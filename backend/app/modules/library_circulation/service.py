"""A-023.2 — Library Circulation service skeleton (L2).

Tenant-scoped circulation lifecycle for loan requests and returns.
"""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher


LOAN_STATES: frozenset[str] = frozenset(
    {"REQUESTED", "CHECKED_OUT", "OVERDUE", "RETURNED", "CLOSED"}
)

_LOAN_FSM: dict[str, frozenset[str]] = {
    "REQUESTED": frozenset({"CHECKED_OUT"}),
    "CHECKED_OUT": frozenset({"OVERDUE", "RETURNED"}),
    "OVERDUE": frozenset({"RETURNED"}),
    "RETURNED": frozenset({"CLOSED"}),
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


def _get_loan(tenant_id: int, loan_id: str) -> dict:
    for row in list_entities_for_tenant(tenant_id, "library_circulation_loans"):
        if row.get("id") == loan_id:
            return row
    raise ValueError(f"Loan {loan_id!r} not found for tenant {tenant_id}")


def _assert_transition(current: str, target: str) -> None:
    allowed = _LOAN_FSM.get(current, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition loan from {current!r} to {target!r}. "
            f"Allowed: {sorted(allowed)}"
        )


def create_loan_request(
    tenant_id: int,
    *,
    student_id: str,
    item_id: str,
    due_date: str,
) -> dict:
    """Create a new circulation loan request in REQUESTED state."""
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if not item_id:
        raise ValueError("item_id is required")
    if not due_date:
        raise ValueError("due_date is required")

    row = create_entity_for_tenant(
        tenant_id,
        "library_circulation_loans",
        {
            "student_id": student_id,
            "item_id": item_id,
            "due_date": due_date,
            "status": "REQUESTED",
            "tenant_id": tenant_id,
        },
    )
    return {"loan_id": row["id"], "status": "REQUESTED"}


def checkout_item(tenant_id: int, *, loan_id: str, issued_by: str) -> dict:
    """Issue an item and move REQUESTED loan to CHECKED_OUT."""
    _validate_tenant(tenant_id)
    if not issued_by:
        raise ValueError("issued_by is required")
    loan = _get_loan(tenant_id, loan_id)
    _assert_transition(loan["status"], "CHECKED_OUT")
    loan["status"] = "CHECKED_OUT"
    loan["issued_by"] = issued_by
    _fire(tenant_id, "library_circulation.checked_out", {"loan_id": loan_id, "item_id": loan.get("item_id")})
    return {"loan_id": loan_id, "status": "CHECKED_OUT"}


def mark_overdue(tenant_id: int, *, loan_id: str) -> dict:
    """Mark an active checkout as overdue."""
    _validate_tenant(tenant_id)
    loan = _get_loan(tenant_id, loan_id)
    _assert_transition(loan["status"], "OVERDUE")
    loan["status"] = "OVERDUE"
    _fire(tenant_id, "library_circulation.overdue", {"loan_id": loan_id})
    return {"loan_id": loan_id, "status": "OVERDUE"}


def return_item(tenant_id: int, *, loan_id: str, received_by: str) -> dict:
    """Return an item from CHECKED_OUT or OVERDUE states."""
    _validate_tenant(tenant_id)
    if not received_by:
        raise ValueError("received_by is required")
    loan = _get_loan(tenant_id, loan_id)
    _assert_transition(loan["status"], "RETURNED")
    loan["status"] = "RETURNED"
    loan["received_by"] = received_by
    _fire(tenant_id, "library_circulation.returned", {"loan_id": loan_id})
    return {"loan_id": loan_id, "status": "RETURNED"}


def close_loan(tenant_id: int, *, loan_id: str) -> dict:
    """Close a RETURNED loan."""
    _validate_tenant(tenant_id)
    loan = _get_loan(tenant_id, loan_id)
    _assert_transition(loan["status"], "CLOSED")
    loan["status"] = "CLOSED"
    return {"loan_id": loan_id, "status": "CLOSED"}


def list_loans(
    tenant_id: int,
    *,
    status: str | None = None,
    student_id: str | None = None,
) -> list[dict]:
    """List circulation loans for a tenant with optional filters."""
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "library_circulation_loans")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if student_id:
        rows = [r for r in rows if r.get("student_id") == student_id]
    return rows


def evaluate_library_circulation_readiness(
    tenant_id: int,
    circulation_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for circulation workflows."""
    _validate_tenant(tenant_id)
    payload = circulation_payload or {}

    required_evidence = [
        "loan_id",
        "item_id",
        "student_id",
        "due_date",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    overdue_risk = bool(payload.get("overdue_risk"))
    return_gap = bool(payload.get("return_evidence_gap"))

    if missing_evidence:
        classification = "CIRCULATION_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_circulation_evidence"
        rationale = "Circulation evidence is incomplete."
    elif overdue_risk:
        classification = "OVERDUE_RISK_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "route_overdue_case_for_manual_review"
        rationale = "Overdue risk requires manual circulation review."
    elif return_gap:
        classification = "RETURN_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "collect_return_evidence_before_closure"
        rationale = "Return evidence gap blocks deterministic closure."
    elif payload.get("manual_review_ready"):
        classification = "READY_FOR_MANUAL_CIRCULATION_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "submit_loan_for_manual_review"
        rationale = "Loan evidence is complete for bounded manual review."
    else:
        classification = "READY_FOR_CIRCULATION_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_circulation_review"
        rationale = "Circulation payload is sufficient for deterministic review."

    return {
        "tenant_id": tenant_id,
        "module": "library_circulation",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_LOAN",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_FINE_STUDENT",
            "AUTO_BLOCK_BORROWING",
            "AUTO_CLOSE_OVERDUE_CASE",
        ],
        "human_review_required": True,
        "next_recommended_step": next_step,
        "rationale_notes": rationale,
        "safety_flags": {
            "tenant_scoped": True,
            "deterministic": True,
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_kpi_claim": True,
            "no_brain_claim": True,
            "no_autonomous_execution": True,
            "no_external_provider_call": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }