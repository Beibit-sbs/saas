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


def evaluate_health_services_readiness(
    tenant_id: int,
    health_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for health service referrals."""
    _validate_tenant(tenant_id)
    payload = health_payload or {}

    required_evidence = [
        "case_id",
        "student_id",
        "consent_context",
        "triage_context",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    urgent_risk_flag = bool(payload.get("urgent_risk_flag"))
    consent_gap = bool(payload.get("consent_evidence_missing"))

    if missing_evidence:
        classification = "HEALTH_REFERRAL_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_health_referral_evidence"
        rationale = "Health referral evidence is incomplete."
    elif urgent_risk_flag:
        classification = "URGENT_HEALTH_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "escalate_to_manual_clinical_review"
        rationale = "Urgent risk must be handled by qualified human staff."
    elif consent_gap:
        classification = "HEALTH_CONSENT_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "obtain_consent_evidence_before_triage"
        rationale = "Consent evidence is required for compliant referral handling."
    elif payload.get("manual_triage_ready"):
        classification = "READY_FOR_MANUAL_HEALTH_TRIAGE"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "route_referral_for_manual_triage"
        rationale = "Referral packet is complete for bounded human triage."
    else:
        classification = "READY_FOR_HEALTH_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_health_review"
        rationale = "Health referral evidence supports deterministic manual review."

    return {
        "tenant_id": tenant_id,
        "module": "health_services",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_REFERRAL",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_DIAGNOSE",
            "AUTO_ASSIGN_TREATMENT",
            "AUTO_CLOSE_CRITICAL_CASE",
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