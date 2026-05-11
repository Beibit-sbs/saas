"""Phase XLVI.2 — AI Plagiarism Detection sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

SCAN_STATES: frozenset[str] = frozenset({"SUBMITTED", "SCANNING", "RESULT_READY"})

_SCAN_FSM: dict[str, frozenset[str]] = {
    "SUBMITTED": frozenset({"SCANNING"}),
    "SCANNING": frozenset({"RESULT_READY"}),
}

# Similarity score thresholds
OK_THRESHOLD: float = 0.10        # < 10% — OK
WARNING_THRESHOLD: float = 0.30   # 10-30% — WARNING, >30% — VIOLATION


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_scan(tenant_id: int, scan_id: str) -> dict:
    for r in list_entities_for_tenant(tenant_id, "scan_requests"):
        if r.get("id") == scan_id:
            return r
    raise ValueError(f"Scan {scan_id!r} not found")


def _assert_transition(current: str, target: str) -> None:
    if target not in _SCAN_FSM.get(current, frozenset()):
        raise ValueError(f"Cannot transition scan from {current} to {target}")


def submit_scan(tenant_id: int, *, document_id: str, content: str) -> dict:
    _validate_tenant(tenant_id)
    if not document_id:
        raise ValueError("document_id is required")
    if not content:
        raise ValueError("content is required")
    row = create_entity_for_tenant(
        tenant_id,
        "scan_requests",
        {
            "document_id": document_id,
            "content_length": len(content),
            "status": "SUBMITTED",
            "similarity_score": None,
            "verdict": None,
            "tenant_id": tenant_id,
        },
    )
    return {"scan_id": row["id"], "status": "SUBMITTED"}


def start_scanning(tenant_id: int, *, scan_id: str) -> dict:
    _validate_tenant(tenant_id)
    scan = _get_scan(tenant_id, scan_id)
    _assert_transition(scan["status"], "SCANNING")
    scan["status"] = "SCANNING"
    return {"scan_id": scan_id, "status": "SCANNING"}


def complete_scan(tenant_id: int, *, scan_id: str, similarity_score: float) -> dict:
    _validate_tenant(tenant_id)
    if similarity_score < 0.0 or similarity_score > 1.0:
        raise ValueError("similarity_score must be between 0.0 and 1.0")
    scan = _get_scan(tenant_id, scan_id)
    _assert_transition(scan["status"], "RESULT_READY")
    scan["status"] = "RESULT_READY"
    scan["similarity_score"] = similarity_score

    if similarity_score < OK_THRESHOLD:
        verdict = "OK"
    elif similarity_score < WARNING_THRESHOLD:
        verdict = "WARNING"
    else:
        verdict = "VIOLATION"

    scan["verdict"] = verdict
    _fire(tenant_id, "scan.complete", {
        "scan_id": scan_id,
        "similarity_score": similarity_score,
        "verdict": verdict,
    })
    if verdict == "VIOLATION":
        _fire(tenant_id, "plagiarism.detected", {
            "scan_id": scan_id,
            "document_id": scan.get("document_id"),
            "similarity_score": similarity_score,
        })
    return {"scan_id": scan_id, "status": "RESULT_READY", "verdict": verdict, "similarity_score": similarity_score}


def list_scans(tenant_id: int, *, status: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "scan_requests")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


def evaluate_ai_plagiarism_readiness(
    tenant_id: int,
    plagiarism_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for plagiarism governance."""
    _validate_tenant(tenant_id)
    payload = plagiarism_payload or {}

    required_evidence = [
        "document_id",
        "submission_id",
        "integrity_policy_ref",
        "review_context",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    similarity_evidence_missing = bool(payload.get("similarity_evidence_missing"))
    requires_human_integrity = bool(payload.get("requires_human_integrity_review"))

    if missing_evidence:
        classification = "PLAGIARISM_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_integrity_evidence"
        rationale = "Submission integrity evidence is incomplete."
    elif similarity_evidence_missing:
        classification = "SIMILARITY_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "request_similarity_evidence_for_manual_review"
        rationale = "Similarity evidence is required before case triage."
    elif requires_human_integrity:
        classification = "HUMAN_ACADEMIC_INTEGRITY_REVIEW_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "route_case_to_human_integrity_committee"
        rationale = "Case is flagged for human-only academic integrity review."
    elif payload.get("manual_case_ready"):
        classification = "READY_FOR_MANUAL_CASE_TRIAGE"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_case_triage"
        rationale = "Evidence is sufficient for manual case triage."
    else:
        classification = "READY_FOR_INTEGRITY_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "perform_manual_integrity_review"
        rationale = "Input is complete for bounded human review."

    return {
        "tenant_id": tenant_id,
        "module": "ai_plagiarism",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_SIGNAL",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_ACCUSATION",
            "AUTO_PENALTY",
            "AUTO_REJECT_ASSIGNMENT",
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
