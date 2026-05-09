"""A-024.2 — Procurement Approval Workflow operational contract (L3 evidence).

This service provides deterministic procurement review evidence only.
It never auto-approves, executes payments, or executes contracts.
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

PROCUREMENT_APPROVAL_STATUSES: frozenset[str] = frozenset(
    {"draft", "review_required", "ready_for_human_approval", "blocked", "returned_for_revision"}
)
PROCUREMENT_RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high", "critical"})
PROCUREMENT_EVENT_READINESS: dict[str, str] = {
    "review_required": "procurement.approval.review_required",
    "ready_for_human_approval": "procurement.approval.ready_for_human_approval",
    "blocked": "procurement.approval.blocked",
    "returned_for_revision": "procurement.approval.returned_for_revision",
}


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _normalize_required(value: str, *, field: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def build_procurement_approval_review(
    *,
    tenant_id: int,
    request_id: str,
    amount: float,
    currency: str,
    procurement_method: str,
    has_budget_reference: bool,
    has_required_documents: bool,
    is_single_source: bool,
    requester_role: str,
    source_entity_type: str,
    source_entity_id: str,
    vendor_id: str | None = None,
) -> dict[str, object]:
    """Build deterministic procurement review evidence without approval execution."""
    _validate_tenant(tenant_id)
    req_id = _normalize_required(request_id, field="request_id")
    curr = _normalize_required(currency, field="currency").upper()
    method = _normalize_required(procurement_method, field="procurement_method").lower()
    role = _normalize_required(requester_role, field="requester_role").lower()
    source_type = _normalize_required(source_entity_type, field="source_entity_type")
    source_id = _normalize_required(source_entity_id, field="source_entity_id")

    if amount <= 0:
        raise ValueError("amount must be > 0")

    missing_requirements: list[str] = []
    policy_reasons: list[str] = []
    risk_level = "low"
    approval_status = "ready_for_human_approval"
    review_required = False

    if not has_required_documents:
        missing_requirements.append("required_documents")
        approval_status = "blocked"
        risk_level = "high"
        review_required = True

    if not has_budget_reference:
        missing_requirements.append("budget_reference")
        if approval_status != "blocked":
            approval_status = "review_required"
        if risk_level == "low":
            risk_level = "medium"
        review_required = True

    if is_single_source:
        policy_reasons.append("SINGLE_SOURCE_REQUIRES_REVIEW")
        if approval_status == "ready_for_human_approval":
            approval_status = "review_required"
        if risk_level in {"low", "medium"}:
            risk_level = "high"
        review_required = True

    if amount >= 100000:
        policy_reasons.append("HIGH_AMOUNT_THRESHOLD")
        if approval_status == "ready_for_human_approval":
            approval_status = "review_required"
        if risk_level == "low":
            risk_level = "medium"
        review_required = True

    if role in {"intern", "guest", "anonymous"}:
        policy_reasons.append("INSUFFICIENT_REQUESTER_ROLE")
        approval_status = "blocked"
        risk_level = "critical"
        review_required = True

    if method in {"unknown", "invalid"}:
        policy_reasons.append("UNKNOWN_PROCUREMENT_METHOD")
        if approval_status != "blocked":
            approval_status = "returned_for_revision"
        if risk_level == "low":
            risk_level = "medium"
        review_required = True

    policy_reasons.extend(
        [
            "NO_AUTO_APPROVAL_IN_A0242",
            "NO_PAYMENT_EXECUTION_IN_A0242",
            "NO_CONTRACT_EXECUTION_IN_A0242",
        ]
    )

    if approval_status not in PROCUREMENT_APPROVAL_STATUSES:
        approval_status = "blocked"
        risk_level = "critical"
        review_required = True

    event_readiness = PROCUREMENT_EVENT_READINESS.get(
        approval_status, "procurement.approval.review_required"
    )

    return {
        "tenant_id": tenant_id,
        "request_id": req_id,
        "amount": float(amount),
        "currency": curr,
        "procurement_method": method,
        "vendor_id": vendor_id,
        "has_budget_reference": has_budget_reference,
        "has_required_documents": has_required_documents,
        "is_single_source": is_single_source,
        "requester_role": role,
        "source_entity_type": source_type,
        "source_entity_id": source_id,
        "approval_status": approval_status,
        "risk_level": risk_level,
        "review_required": review_required,
        "missing_requirements": sorted(set(missing_requirements)),
        "policy_reasons": sorted(set(policy_reasons)),
        "audit_action": f"procurement_approval_workflow.{approval_status}",
        "event_readiness": event_readiness,
        "no_auto_approval": True,
        "no_payment_execution": True,
        "no_contract_execution": True,
    }


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
        "procurement_approval_workflow_requests",
        {
            "request_code": request_code,
            "cost_center": cost_center,
            "justification": justification,
            "status": "REQUESTED",
            "tenant_id": tenant_id,
        },
        tenant_id,
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

    for row in list_entities_for_tenant("procurement_approval_workflow_requests", tenant_id):
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
    rows = list_entities_for_tenant("procurement_approval_workflow_requests", tenant_id)
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return rows
