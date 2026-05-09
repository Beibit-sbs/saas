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

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

VALID_STATUSES = frozenset({"PRESENT", "ABSENT", "EXCUSED", "LATE"})
LOW_ATTENDANCE_THRESHOLD: float = 0.75  # 75%

ATTENDANCE_VISIBILITY_STATUSES = frozenset({"present", "absent", "late", "excused", "unknown"})
ATTENDANCE_VISIBILITY_RISK_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    """Best-effort event publish — never raises."""
    try:
        EventPublisher().publish_event(
            tenant_id=int(tenant_id),
            event_type=event_type,
            aggregate_type="attendance",
            aggregate_id=str(payload.get("record_id") or payload.get("risk_record_id") or ""),
            payload_json=payload,
        )
    except Exception:
        pass


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _visibility_risk_rank(level: str) -> int:
    return ATTENDANCE_VISIBILITY_RISK_LEVELS.index(level)


def _max_visibility_risk(current: str, candidate: str) -> str:
    return candidate if _visibility_risk_rank(candidate) > _visibility_risk_rank(current) else current


def build_attendance_evidence_item(
    *,
    tenant_id: int,
    record: dict,
    source_entity_type: str,
    source_entity_id: str,
) -> dict:
    """Normalize an attendance record into deterministic visibility evidence."""
    _validate_tenant(tenant_id)
    if int(record.get("tenant_id", tenant_id) or tenant_id) != tenant_id:
        raise ValueError("attendance record tenant_id mismatch")

    status_raw = str(record.get("status", "")).strip().lower()
    status = status_raw if status_raw in ATTENDANCE_VISIBILITY_STATUSES else "unknown"
    return {
        "record_id": str(record.get("id", "")),
        "student_id": str(record.get("student_id", "")),
        "session_id": str(record.get("session_id", "")),
        "status": status,
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id,
    }


def classify_attendance_visibility_risk(
    *,
    total_records: int,
    absent_count: int,
    late_count: int,
    unknown_count: int,
) -> tuple[str, bool]:
    """Classify attendance visibility risk with deterministic thresholds."""
    if total_records <= 0:
        return "medium", True

    absence_ratio = absent_count / total_records
    late_ratio = late_count / total_records

    risk = "low"
    review_required = False

    if absence_ratio >= 0.45:
        risk = _max_visibility_risk(risk, "critical")
        review_required = True
    elif absence_ratio >= 0.30:
        risk = _max_visibility_risk(risk, "high")
        review_required = True
    elif absence_ratio >= 0.15:
        risk = _max_visibility_risk(risk, "medium")

    if late_ratio >= 0.25:
        risk = _max_visibility_risk(risk, "high")
        review_required = True
    elif late_ratio >= 0.12:
        risk = _max_visibility_risk(risk, "medium")

    if unknown_count > 0:
        risk = _max_visibility_risk(risk, "high")
        review_required = True

    return risk, review_required


def build_attendance_visibility_summary(
    *,
    tenant_id: int,
    records: list[dict],
    source_entity_type: str,
    source_entity_id: str,
) -> dict:
    """Build deterministic tenant-safe attendance operational visibility summary."""
    _validate_tenant(tenant_id)
    if not source_entity_type:
        raise ValueError("source_entity_type is required")
    if not source_entity_id:
        raise ValueError("source_entity_id is required")

    normalized = [
        build_attendance_evidence_item(
            tenant_id=tenant_id,
            record=record,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
        )
        for record in records
    ]

    total_records = len(normalized)
    present_count = sum(1 for item in normalized if item["status"] == "present")
    absent_count = sum(1 for item in normalized if item["status"] == "absent")
    late_count = sum(1 for item in normalized if item["status"] == "late")
    excused_count = sum(1 for item in normalized if item["status"] == "excused")
    unknown_count = sum(1 for item in normalized if item["status"] == "unknown")

    risk_level, review_required = classify_attendance_visibility_risk(
        total_records=total_records,
        absent_count=absent_count,
        late_count=late_count,
        unknown_count=unknown_count,
    )

    data_quality_note: str | None = None
    if total_records == 0:
        data_quality_note = "no attendance records available"
    elif unknown_count > 0:
        data_quality_note = "attendance records include unknown statuses"

    return {
        "tenant_id": tenant_id,
        "total_records": total_records,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "excused_count": excused_count,
        "unknown_count": unknown_count,
        "risk_level": risk_level,
        "review_required": review_required,
        "evidence_items": sorted(
            normalized,
            key=lambda item: (item["student_id"], item["session_id"], item["record_id"]),
        ),
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id,
        "data_quality_note": data_quality_note,
        "no_fake_attendance_data": True,
        "no_fake_attendance_analytics": True,
    }


def _audit(tenant_id: int, actor: str, action: str, path: str, metadata: dict) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=path,
            client_ip="service",
            entity="attendance",
            metadata=metadata,
            tenant_id=tenant_id,
        )
    except Exception:
        pass


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        pass


def _record_outcome(record_id: str, outcome_type: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            record_id,
            payload={
                "outcome_type": outcome_type,
                "source_module": "attendance",
                "record_id": record_id,
            },
            actor=actor,
        )
    except Exception:
        pass


# ─── mark_attendance ─────────────────────────────────────────────────────────

def mark_attendance(
    tenant_id: int,
    *,
    session_id: str,
    student_id: str,
    status: str,
    actor: str = "system",
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
        {
            "session_id": session_id,
            "student_id": student_id,
            "status": status,
            "recorded_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    event_type = "attendance.absence.recorded" if status == "ABSENT" else "attendance.record.marked"
    _fire(tenant_id, event_type, {
        "session_id": session_id,
        "student_id": student_id,
        "status": status,
        "record_id": record.get("id"),
        "tenant_id": tenant_id,
    })
    _audit(
        tenant_id,
        actor,
        build_audit_action("attendance", "record", "mark"),
        f"/internal/attendance/{record.get('id')}/mark",
        {
            "record_id": record.get("id"),
            "session_id": session_id,
            "student_id": student_id,
            "status": status,
        },
    )
    _metric(tenant_id, "attendance_records_marked", 1)

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
    actor: str = "system",
) -> dict:
    """Excuse an absence record."""
    _validate_tenant(tenant_id)
    if not record_id:
        raise ValueError("record_id is required")
    if not reason:
        raise ValueError("reason is required")

    records = list_entities_for_tenant("attendance_records", tenant_id)
    record = next((r for r in records if str(r.get("id", "")) == str(record_id)), None)
    if record is None:
        raise LookupError(f"Attendance record {record_id} not found for tenant {tenant_id}")
    if record.get("status") != "ABSENT":
        raise ValueError(f"Cannot excuse record with status '{record.get('status')}' — only ABSENT records can be excused")

    excuse = create_entity_for_tenant(
        "attendance_excuses",
        {
            "record_id": record_id,
            "student_id": record.get("student_id"),
            "session_id": record.get("session_id"),
            "reason": reason,
            "excused_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    _fire(tenant_id, "attendance.absence.excused", {
        "record_id": record_id,
        "student_id": record.get("student_id"),
        "excuse_id": excuse.get("id"),
        "reason": reason,
        "tenant_id": tenant_id,
    })
    _record_outcome(str(record_id), "absence_excused", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("attendance", "absence", "excuse"),
        f"/internal/attendance/{record_id}/excuse",
        {"record_id": record_id, "excuse_id": excuse.get("id")},
    )
    _metric(tenant_id, "attendance_absences_excused", 1)

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

    records = list_entities_for_tenant("attendance_records", tenant_id)
    student_records = [r for r in records if str(r.get("student_id", "")) == str(student_id)]

    if course_id:
        # Filter by course via sessions
        sessions = list_entities_for_tenant("attendance_sessions", tenant_id)
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
    actor: str = "system",
) -> dict:
    """Check if student is at low-attendance risk and fire event if threshold breached."""
    _validate_tenant(tenant_id)
    summary = get_attendance_summary(tenant_id, student_id=student_id, course_id=course_id)

    if summary["low_risk"]:
        risk_record = create_entity_for_tenant(
            "attendance_risk_records",
            {
                "student_id": student_id,
                "course_id": course_id,
                "attendance_pct": summary["attendance_pct"],
                "threshold": LOW_ATTENDANCE_THRESHOLD,
                "detected_at": _utc_now().isoformat(),
                "tenant_id": tenant_id,
            },
            tenant_id,
        )

        _fire(tenant_id, "attendance.threshold.breached", {
            "student_id": student_id,
            "course_id": course_id,
            "attendance_pct": summary["attendance_pct"],
            "threshold": LOW_ATTENDANCE_THRESHOLD,
            "risk_record_id": risk_record.get("id"),
            "tenant_id": tenant_id,
        })
        _record_outcome(str(risk_record.get("id") or ""), "threshold_breached", actor)
        _audit(
            tenant_id,
            actor,
            build_audit_action("attendance", "risk", "detect"),
            f"/internal/attendance/risk/{risk_record.get('id')}",
            {
                "risk_record_id": risk_record.get("id"),
                "student_id": student_id,
                "course_id": course_id,
                "attendance_pct": summary["attendance_pct"],
            },
        )
        _metric(tenant_id, "attendance_threshold_breaches", 1)

        # A-014.3: Direct Brain Core signal for attendance recovery loop.
        # Same fire-and-forget pattern used by grade/thesis/admissions services.
        try:
            from uuid import uuid4 as _uuid4
            from app.modules.brain_core.service import brain_core_service as _bcs
            _bcs.process_signal({
                "signal_id": str(_uuid4()),
                "tenant_id": int(tenant_id),
                "correlation_id": str(risk_record.get("id") or _uuid4()),
                "event_type": "academic.attendance_risk.detected",
                "source_entity_type": "section_attendance",
                "source_entity_id": str(risk_record.get("id") or course_id),
                "subject": {"student_id": student_id, "course_id": course_id},
                "payload": {
                    "student_id": student_id,
                    "attendance_rate": summary["attendance_pct"],
                    "course_id": course_id,
                    "source_entity_type": "section_attendance",
                    "source_entity_id": str(risk_record.get("id") or course_id),
                },
                "metadata": {},
            })
        except Exception:
            pass  # Brain Core errors must never break attendance service

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
    rows = list_entities_for_tenant("attendance_records", tenant_id)
    if session_id:
        rows = [r for r in rows if str(r.get("session_id", "")) == str(session_id)]
    if student_id:
        rows = [r for r in rows if str(r.get("student_id", "")) == str(student_id)]
    return rows
