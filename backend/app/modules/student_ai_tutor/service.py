"""Phase XLVI.1 — Student AI Tutor sub-module."""
from __future__ import annotations

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

SESSION_STATES: frozenset[str] = frozenset({"ACTIVE", "ENDED", "ABANDONED"})

# Number of consecutive struggle signals before intervention brain-signal fires
STRUGGLE_THRESHOLD: int = 3


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher()
        pub.publish_event(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _get_session(tenant_id: int, session_id: str) -> dict:
    for r in list_entities_for_tenant(tenant_id, "tutor_sessions"):
        if r.get("id") == session_id:
            return r
    raise ValueError(f"Session {session_id!r} not found")


def start_session(tenant_id: int, *, student_id: str, topic: str) -> dict:
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if not topic:
        raise ValueError("topic is required")
    row = create_entity_for_tenant(
        tenant_id,
        "tutor_sessions",
        {
            "student_id": student_id,
            "topic": topic,
            "status": "ACTIVE",
            "struggle_count": 0,
            "messages": [],
            "tenant_id": tenant_id,
        },
    )
    _fire(tenant_id, "tutor_session.started", {"session_id": row["id"], "student_id": student_id, "topic": topic})
    return {"session_id": row["id"], "status": "ACTIVE"}


def send_message(tenant_id: int, *, session_id: str, message: str, is_struggle: bool = False) -> dict:
    _validate_tenant(tenant_id)
    if not message:
        raise ValueError("message is required")
    session = _get_session(tenant_id, session_id)
    if session["status"] != "ACTIVE":
        raise ValueError("Session is not active")
    if is_struggle:
        session["struggle_count"] = session.get("struggle_count", 0) + 1
        if session["struggle_count"] >= STRUGGLE_THRESHOLD:
            _fire(tenant_id, "student.needs_intervention", {
                "session_id": session_id,
                "student_id": session.get("student_id"),
                "struggle_count": session["struggle_count"],
            })
    # Simulate LLM response (abstract)
    response = f"[AI] Responding to: {message[:50]}"
    return {"session_id": session_id, "response": response, "struggle_count": session.get("struggle_count", 0)}


def detect_breakthrough(tenant_id: int, *, session_id: str) -> dict:
    _validate_tenant(tenant_id)
    session = _get_session(tenant_id, session_id)
    if session["status"] != "ACTIVE":
        raise ValueError("Session is not active")
    _fire(tenant_id, "learning.breakthrough_detected", {
        "session_id": session_id,
        "student_id": session.get("student_id"),
        "topic": session.get("topic"),
    })
    return {"session_id": session_id, "breakthrough": True}


def end_session(tenant_id: int, *, session_id: str) -> dict:
    _validate_tenant(tenant_id)
    session = _get_session(tenant_id, session_id)
    if session["status"] != "ACTIVE":
        raise ValueError("Session is not active")
    session["status"] = "ENDED"
    return {"session_id": session_id, "status": "ENDED"}


def abandon_session(tenant_id: int, *, session_id: str) -> dict:
    _validate_tenant(tenant_id)
    session = _get_session(tenant_id, session_id)
    if session["status"] != "ACTIVE":
        raise ValueError("Session is not active")
    session["status"] = "ABANDONED"
    return {"session_id": session_id, "status": "ABANDONED"}


def list_sessions(tenant_id: int, *, student_id: str | None = None) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant(tenant_id, "tutor_sessions")
    if student_id:
        rows = [r for r in rows if r.get("student_id") == student_id]
    return rows


def evaluate_student_ai_tutor_readiness(
    tenant_id: int,
    tutor_payload: dict | None = None,
) -> dict:
    """Return deterministic L3 readiness classification for student AI tutor sessions."""
    _validate_tenant(tenant_id)
    payload = tutor_payload or {}

    required_evidence = [
        "session_id",
        "student_id",
        "topic",
        "support_context",
    ]
    missing_evidence = [key for key in required_evidence if not payload.get(key)]

    struggle_escalation = bool(payload.get("struggle_escalation_flag"))
    safety_gap = bool(payload.get("safety_evidence_missing"))

    if missing_evidence:
        classification = "TUTOR_SESSION_INPUT_INCOMPLETE"
        evaluation_status = "INCOMPLETE"
        readiness_level = "PENDING"
        risk_level = "MEDIUM"
        next_step = "collect_missing_tutor_session_evidence"
        rationale = "Tutor session evidence is incomplete."
    elif struggle_escalation:
        classification = "STUDENT_SUPPORT_ESCALATION_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "escalate_to_manual_student_support_review"
        rationale = "Struggle escalation requires human support intervention."
    elif safety_gap:
        classification = "TUTOR_SAFETY_EVIDENCE_REQUIRED"
        evaluation_status = "REVIEW_REQUIRED"
        readiness_level = "PENDING"
        risk_level = "HIGH"
        next_step = "collect_tutor_safety_evidence_before_review"
        rationale = "Safety evidence gap blocks deterministic review closure."
    elif payload.get("manual_review_ready"):
        classification = "READY_FOR_MANUAL_TUTOR_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "route_session_for_manual_tutor_review"
        rationale = "Session packet is complete for bounded manual review."
    else:
        classification = "READY_FOR_TUTOR_REVIEW"
        evaluation_status = "READY"
        readiness_level = "READY"
        risk_level = "LOW"
        next_step = "start_manual_tutor_review"
        rationale = "Tutor session evidence is sufficient for deterministic review."

    return {
        "tenant_id": tenant_id,
        "module": "student_ai_tutor",
        "maturity_level": "L3",
        "evaluation_status": evaluation_status,
        "classification": classification,
        "readiness_level": readiness_level,
        "risk_level": risk_level,
        "required_evidence": required_evidence,
        "missing_evidence": missing_evidence,
        "allowed_actions": [
            "REVIEW_SESSION",
            "REQUEST_EVIDENCE",
            "ESCALATE_REVIEW",
        ],
        "forbidden_actions": [
            "AUTO_DECIDE_INTERVENTION",
            "AUTO_DISCIPLINARY_LABEL",
            "AUTO_CLOSE_STRUGGLE_CASE",
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
