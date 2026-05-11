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


def evaluate_contracts_legal_readiness(
    tenant_id: int,
    contract_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for legal contract workflows."""
    _validate_tenant(tenant_id)
    payload = contract_payload or {}

    required_evidence = [
        "contract_id",
        "party_context",
        "signature_context",
        "expiry_context",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    signature_gap = bool(payload.get("signature_evidence_gap"))
    expiry_risk = bool(payload.get("expiry_risk"))

    if missing_evidence:
        classification = "CONTRACT_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_contract_evidence"
        rationale = "Contract evidence payload is incomplete."
    elif signature_gap:
        classification = "SIGNATURE_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "request_signature_evidence_for_manual_review"
        rationale = "Signature evidence must be completed before legal review."
    elif expiry_risk:
        classification = "EXPIRY_RISK_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "escalate_expiry_risk_for_manual_legal_action"
        rationale = "Expiry risk requires legal reviewer intervention."
    elif payload.get("manual_action_ready"):
        classification = "READY_FOR_MANUAL_CONTRACT_ACTION"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "route_contract_for_manual_legal_action"
        rationale = "Contract package is ready for bounded manual action."
    else:
        classification = "READY_FOR_LEGAL_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_legal_review"
        rationale = "Contract evidence is sufficient for legal review."

    return {
        "tenant_id": tenant_id,
        "module": "contracts_legal_repository",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_CONTRACT",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_SIGN_CONTRACT",
            "AUTO_APPROVE_LEGAL_TERMS",
            "AUTO_TERMINATE_CONTRACT",
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
