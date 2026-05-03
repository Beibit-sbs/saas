"""Attendance module service — XXXVII.

Состояния записи посещаемости:
  PRESENT / ABSENT / EXCUSED / LATE

Операции:
  mark_attendance(tenant_id, session_id, student_id, status)
  excuse_absence(tenant_id, record_id, reason)
  get_attendance_summary(tenant_id, student_id, course_id=None)
  check_low_attendance_risk(tenant_id, student_id, course_id)
  list_attendance_records(tenant_id, session_id=None, student_id=None)

Константа порога:
  LOW_ATTENDANCE_THRESHOLD = 0.75  (75%)

События:
  attendance.record.marked
  attendance.absence.recorded
  attendance.absence.excused
  attendance.threshold.breached
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

VALID_STATUSES = frozenset({"PRESENT", "ABSENT", "EXCUSED", "LATE"})
LOW_ATTENDANCE_THRESHOLD: float = 0.75  # 75%


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher(tenant_id=tenant_id)
        pub.publish_event(event_type=event_type, payload=payload)
    except Exception:
        pass


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


# ─── mark_attendance ─────────────────────────────────────────────────────────

def mark_attendance(
    tenant_id: int,
    *,
    session_id: str,
    student_id: str,
    status: str,
) -> dict:
    """Record attendance for a student in a session."""
    _validate_tenant(tenant_id)
    if not session_id:
        raise ValueError("session_id is required")
    if not student_id:
        raise ValueError("student_id is required")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}")

    record = create_entity_for_tenant(
        "attendance_records",
        tenant_id=tenant_id,
        data={
            "session_id": session_id,
            "student_id": student_id,
            "status": status,
            "recorded_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    event_type = "attendance.absence.recorded" if status == "ABSENT" else "attendance.record.marked"
    _fire(tenant_id, event_type, {
        "session_id": session_id,
        "student_id": student_id,
        "status": status,
        "record_id": record.get("id"),
        "tenant_id": tenant_id,
    })

    return {
        "record_id": record.get("id"),
        "session_id": session_id,
        "student_id": student_id,
        "status": status,
    }


# ─── excuse_absence ──────────────────────────────────────────────────────────

def excuse_absence(
    tenant_id: int,
    *,
    record_id: str,
    reason: str,
) -> dict:
    """Excuse an absence record."""
    _validate_tenant(tenant_id)
    if not record_id:
        raise ValueError("record_id is required")
    if not reason:
        raise ValueError("reason is required")

    records = list_entities_for_tenant("attendance_records", tenant_id=tenant_id)
    record = next((r for r in records if str(r.get("id", "")) == str(record_id)), None)
    if record is None:
        raise LookupError(f"Attendance record {record_id} not found for tenant {tenant_id}")
    if record.get("status") != "ABSENT":
        raise ValueError(f"Cannot excuse record with status '{record.get('status')}' — only ABSENT records can be excused")

    excuse = create_entity_for_tenant(
        "attendance_excuses",
        tenant_id=tenant_id,
        data={
            "record_id": record_id,
            "student_id": record.get("student_id"),
            "session_id": record.get("session_id"),
            "reason": reason,
            "excused_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "attendance.absence.excused", {
        "record_id": record_id,
        "student_id": record.get("student_id"),
        "excuse_id": excuse.get("id"),
        "reason": reason,
        "tenant_id": tenant_id,
    })

    return {
        "record_id": record_id,
        "excuse_id": excuse.get("id"),
        "status": "EXCUSED",
    }


# ─── get_attendance_summary ──────────────────────────────────────────────────

def get_attendance_summary(
    tenant_id: int,
    *,
    student_id: str,
    course_id: str | None = None,
) -> dict:
    """Calculate attendance percentage for a student (optionally per course)."""
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")

    records = list_entities_for_tenant("attendance_records", tenant_id=tenant_id)
    student_records = [r for r in records if str(r.get("student_id", "")) == str(student_id)]

    if course_id:
        # Filter by course via sessions
        sessions = list_entities_for_tenant("attendance_sessions", tenant_id=tenant_id)
        course_session_ids = {
            str(s.get("id", ""))
            for s in sessions
            if str(s.get("course_id", "")) == str(course_id)
        }
        student_records = [r for r in student_records if str(r.get("session_id", "")) in course_session_ids]

    total = len(student_records)
    if total == 0:
        return {
            "student_id": student_id,
            "course_id": course_id,
            "total_sessions": 0,
            "present_count": 0,
            "absent_count": 0,
            "attendance_pct": 1.0,
            "low_risk": False,
        }

    present_statuses = {"PRESENT", "LATE", "EXCUSED"}
    present_count = sum(1 for r in student_records if r.get("status") in present_statuses)
    absent_count = total - present_count
    pct = present_count / total

    return {
        "student_id": student_id,
        "course_id": course_id,
        "total_sessions": total,
        "present_count": present_count,
        "absent_count": absent_count,
        "attendance_pct": round(pct, 4),
        "low_risk": pct < LOW_ATTENDANCE_THRESHOLD,
    }


# ─── check_low_attendance_risk ───────────────────────────────────────────────

def check_low_attendance_risk(
    tenant_id: int,
    *,
    student_id: str,
    course_id: str,
) -> dict:
    """Check if student is at low-attendance risk and fire event if threshold breached."""
    _validate_tenant(tenant_id)
    summary = get_attendance_summary(tenant_id, student_id=student_id, course_id=course_id)

    if summary["low_risk"]:
        risk_record = create_entity_for_tenant(
            "attendance_risk_records",
            tenant_id=tenant_id,
            data={
                "student_id": student_id,
                "course_id": course_id,
                "attendance_pct": summary["attendance_pct"],
                "threshold": LOW_ATTENDANCE_THRESHOLD,
                "detected_at": _utc_now().isoformat(),
                "tenant_id": tenant_id,
            },
        )

        _fire(tenant_id, "attendance.threshold.breached", {
            "student_id": student_id,
            "course_id": course_id,
            "attendance_pct": summary["attendance_pct"],
            "threshold": LOW_ATTENDANCE_THRESHOLD,
            "risk_record_id": risk_record.get("id"),
            "tenant_id": tenant_id,
        })

        return {**summary, "risk_record_id": risk_record.get("id"), "event_fired": True}

    return {**summary, "event_fired": False}


# ─── list helpers ─────────────────────────────────────────────────────────────

def list_attendance_records(
    tenant_id: int,
    *,
    session_id: str | None = None,
    student_id: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("attendance_records", tenant_id=tenant_id)
    if session_id:
        rows = [r for r in rows if str(r.get("session_id", "")) == str(session_id)]
    if student_id:
        rows = [r for r in rows if str(r.get("student_id", "")) == str(student_id)]
    return rows
