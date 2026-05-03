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
