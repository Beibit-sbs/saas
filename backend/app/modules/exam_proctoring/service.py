"""Phase LVI — Exam Proctoring (AI camera) service."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

SESSION_STATUSES = {"active", "paused", "ended", "aborted"}
VIOLATION_TYPES = {
    "gaze_away",
    "multiple_faces",
    "phone_detected",
    "absence_detected",
    "audio_anomaly",
    "tab_switch",
}


class ProctoringError(Exception):
    """Raised on invalid Exam Proctoring service input."""


@dataclass
class ProctoringSession:
    session_id: int
    tenant_id: int
    exam_id: int
    student_id: int
    status: str


@dataclass
class ProctoringViolation:
    violation_id: int
    tenant_id: int
    session_id: int
    violation_type: str
    confidence: float
    reviewed: bool


@dataclass
class ProctoringConfig:
    config_id: int
    tenant_id: int
    exam_id: int
    rules: dict


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


def start_session(*, exam_id: int, student_id: int, tenant_id: int) -> ProctoringSession:
    """Start a new proctoring session for a student."""
    if exam_id <= 0:
        raise ProctoringError("exam_id is required")
    if student_id <= 0:
        raise ProctoringError("student_id is required")

    # Prevent duplicate active session for same student+exam
    existing = list_entities_for_tenant("proctoring_sessions", tenant_id)
    active = [
        s for s in existing
        if s.get("exam_id") == exam_id
        and s.get("student_id") == student_id
        and s.get("status") == "active"
    ]
    if active:
        raise ProctoringError(
            f"student {student_id} already has an active proctoring session for exam {exam_id}"
        )

    record = create_entity_for_tenant(
        "proctoring_sessions",
        {
            "exam_id": exam_id,
            "student_id": student_id,
            "status": "active",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="proctoring.session_started",
            payload={"session_id": record["id"], "exam_id": exam_id, "student_id": student_id},
        )
    except Exception:
        pass

    return ProctoringSession(
        session_id=record["id"],
        tenant_id=tenant_id,
        exam_id=exam_id,
        student_id=student_id,
        status="active",
    )


def pause_session(*, session_id: int, tenant_id: int) -> ProctoringSession:
    """Pause an active proctoring session."""
    sessions = list_entities_for_tenant("proctoring_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise ProctoringError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] != "active":
        raise ProctoringError(
            f"only active sessions can be paused; current: {session['status']!r}"
        )

    update_entity_for_tenant(
        "proctoring_sessions", session_id, {"status": "paused"}, tenant_id
    )

    return ProctoringSession(
        session_id=session_id,
        tenant_id=tenant_id,
        exam_id=session["exam_id"],
        student_id=session["student_id"],
        status="paused",
    )


def resume_session(*, session_id: int, tenant_id: int) -> ProctoringSession:
    """Resume a paused proctoring session."""
    sessions = list_entities_for_tenant("proctoring_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise ProctoringError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] != "paused":
        raise ProctoringError(
            f"only paused sessions can be resumed; current: {session['status']!r}"
        )

    update_entity_for_tenant(
        "proctoring_sessions", session_id, {"status": "active"}, tenant_id
    )

    return ProctoringSession(
        session_id=session_id,
        tenant_id=tenant_id,
        exam_id=session["exam_id"],
        student_id=session["student_id"],
        status="active",
    )


def end_session(*, session_id: int, tenant_id: int) -> ProctoringSession:
    """End a proctoring session."""
    sessions = list_entities_for_tenant("proctoring_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise ProctoringError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] in ("ended", "aborted"):
        raise ProctoringError(f"session is already {session['status']!r}")

    update_entity_for_tenant(
        "proctoring_sessions", session_id, {"status": "ended"}, tenant_id
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="proctoring.session_ended",
            payload={"session_id": session_id, "exam_id": session["exam_id"]},
        )
    except Exception:
        pass

    return ProctoringSession(
        session_id=session_id,
        tenant_id=tenant_id,
        exam_id=session["exam_id"],
        student_id=session["student_id"],
        status="ended",
    )


def abort_session(*, session_id: int, reason: str, tenant_id: int) -> ProctoringSession:
    """Abort a proctoring session (forced termination)."""
    sessions = list_entities_for_tenant("proctoring_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise ProctoringError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] in ("ended", "aborted"):
        raise ProctoringError(f"session is already {session['status']!r}")

    update_entity_for_tenant(
        "proctoring_sessions",
        session_id,
        {"status": "aborted", "abort_reason": reason or ""},
        tenant_id,
    )

    return ProctoringSession(
        session_id=session_id,
        tenant_id=tenant_id,
        exam_id=session["exam_id"],
        student_id=session["student_id"],
        status="aborted",
    )


def list_sessions(*, exam_id: int, tenant_id: int) -> list[ProctoringSession]:
    """List all proctoring sessions for an exam."""
    rows = list_entities_for_tenant("proctoring_sessions", tenant_id)
    return [
        ProctoringSession(
            session_id=r["id"],
            tenant_id=tenant_id,
            exam_id=r["exam_id"],
            student_id=r["student_id"],
            status=r["status"],
        )
        for r in rows
        if r.get("exam_id") == exam_id
    ]


# ---------------------------------------------------------------------------
# Violation management
# ---------------------------------------------------------------------------


def report_violation(
    *,
    session_id: int,
    violation_type: str,
    confidence: float,
    snapshot_ref: str,
    tenant_id: int,
) -> ProctoringViolation:
    """Record an AI-detected violation during a proctoring session."""
    if violation_type not in VIOLATION_TYPES:
        raise ProctoringError(
            f"unknown violation_type {violation_type!r}; must be one of {VIOLATION_TYPES}"
        )
    if not (0.0 <= confidence <= 1.0):
        raise ProctoringError("confidence must be between 0.0 and 1.0")

    sessions = list_entities_for_tenant("proctoring_sessions", tenant_id)
    matched = [s for s in sessions if s["id"] == session_id]
    if not matched:
        raise ProctoringError(f"session {session_id} not found")

    session = matched[0]
    if session["status"] not in ("active", "paused"):
        raise ProctoringError(
            f"cannot report violation for session in status {session['status']!r}"
        )

    record = create_entity_for_tenant(
        "proctoring_violations",
        {
            "session_id": session_id,
            "violation_type": violation_type,
            "confidence": confidence,
            "snapshot_ref": snapshot_ref or "",
            "reviewed": False,
            "resolution": "",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="proctoring.violation_detected",
            payload={
                "violation_id": record["id"],
                "session_id": session_id,
                "violation_type": violation_type,
                "confidence": confidence,
            },
        )
    except Exception:
        pass

    return ProctoringViolation(
        violation_id=record["id"],
        tenant_id=tenant_id,
        session_id=session_id,
        violation_type=violation_type,
        confidence=confidence,
        reviewed=False,
    )


def review_violation(
    *,
    violation_id: int,
    resolution: str,
    tenant_id: int,
) -> ProctoringViolation:
    """Mark a detected violation as reviewed with a resolution note."""
    if not resolution or not resolution.strip():
        raise ProctoringError("resolution is required")

    violations = list_entities_for_tenant("proctoring_violations", tenant_id)
    matched = [v for v in violations if v["id"] == violation_id]
    if not matched:
        raise ProctoringError(f"violation {violation_id} not found")

    viol = matched[0]
    if viol.get("reviewed"):
        raise ProctoringError("violation is already reviewed")

    update_entity_for_tenant(
        "proctoring_violations",
        violation_id,
        {"reviewed": True, "resolution": resolution.strip()},
        tenant_id,
    )

    return ProctoringViolation(
        violation_id=violation_id,
        tenant_id=tenant_id,
        session_id=viol["session_id"],
        violation_type=viol["violation_type"],
        confidence=viol["confidence"],
        reviewed=True,
    )


def list_violations(*, session_id: int, tenant_id: int) -> list[ProctoringViolation]:
    """List all violations for a proctoring session."""
    rows = list_entities_for_tenant("proctoring_violations", tenant_id)
    return [
        ProctoringViolation(
            violation_id=r["id"],
            tenant_id=tenant_id,
            session_id=r["session_id"],
            violation_type=r["violation_type"],
            confidence=r.get("confidence", 0.0),
            reviewed=r.get("reviewed", False),
        )
        for r in rows
        if r.get("session_id") == session_id
    ]


# ---------------------------------------------------------------------------
# Proctoring configuration
# ---------------------------------------------------------------------------


def create_proctoring_config(
    *,
    exam_id: int,
    rules: dict,
    tenant_id: int,
) -> ProctoringConfig:
    """Create proctoring rules configuration for an exam."""
    if exam_id <= 0:
        raise ProctoringError("exam_id is required")
    if not isinstance(rules, dict):
        raise ProctoringError("rules must be a dict")

    record = create_entity_for_tenant(
        "proctoring_configs",
        {
            "exam_id": exam_id,
            "rules": rules,
        },
        tenant_id,
    )

    return ProctoringConfig(
        config_id=record["id"],
        tenant_id=tenant_id,
        exam_id=exam_id,
        rules=rules,
    )


def get_proctoring_config(*, exam_id: int, tenant_id: int) -> ProctoringConfig | None:
    """Get proctoring config for an exam (returns the most recent one)."""
    rows = list_entities_for_tenant("proctoring_configs", tenant_id)
    matched = [r for r in rows if r.get("exam_id") == exam_id]
    if not matched:
        return None
    r = matched[-1]
    return ProctoringConfig(
        config_id=r["id"],
        tenant_id=tenant_id,
        exam_id=exam_id,
        rules=r.get("rules", {}),
    )
