"""Phase LIII — Counseling / Mental Health service."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher

logger = logging.getLogger("app.modules.counseling")

APPOINTMENT_STATES = {"requested", "confirmed", "completed", "cancelled", "no_show"}
SESSION_TYPES = {"individual", "group", "crisis", "follow_up"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
CASE_STATES = {"open", "active", "on_hold", "closed"}


class CounselingError(Exception):
    """Raised on invalid counseling service input."""


def _audit(tenant_id: int, action: str, actor_id: str, entity_id: object = None, detail: object = None) -> None:
    try:
        log_admin_action(tenant_id=tenant_id, action=action, actor_id=actor_id, entity_id=entity_id, detail=detail)
    except Exception:
        logger.exception("counseling audit failed action=%s", action)


def _record_outcome(entity_id: object, outcome_type: str, actor_id: str) -> None:
    try:
        from app.modules.brain_core import service as brain_core_service  # noqa: PLC0415
        brain_core_service.record_dispatch_outcome(
            entity_id=entity_id,
            outcome_type=outcome_type,
            actor_id=str(actor_id),
        )
    except Exception:
        logger.exception("counseling outcome failed entity_id=%s outcome=%s", entity_id, outcome_type)


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        logger.exception("counseling metric failed metric=%s", metric)


@dataclass
class CounselingAppointment:
    appointment_id: int
    student_id: int
    counselor_id: int
    session_type: str
    status: str
    scheduled_at: str
    tenant_id: int


@dataclass
class CounselingCase:
    case_id: int
    student_id: int
    counselor_id: int
    risk_level: str
    status: str
    tenant_id: int


@dataclass
class CrisisReport:
    report_id: int
    student_id: int
    risk_level: str
    description: str
    tenant_id: int


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------


def request_appointment(
    *,
    student_id: int,
    counselor_id: int,
    session_type: str,
    scheduled_at: str,
    tenant_id: int,
) -> CounselingAppointment:
    """Student requests a counseling appointment."""
    if not student_id or student_id <= 0:
        raise CounselingError("student_id is required")
    if not counselor_id or counselor_id <= 0:
        raise CounselingError("counselor_id is required")
    if session_type not in SESSION_TYPES:
        raise CounselingError(f"invalid session_type: {session_type!r}; must be one of {SESSION_TYPES}")
    if not scheduled_at or not scheduled_at.strip():
        raise CounselingError("scheduled_at is required")

    record = create_entity_for_tenant(
        "counseling_appointments",
        {
            "student_id": student_id,
            "counselor_id": counselor_id,
            "session_type": session_type,
            "scheduled_at": scheduled_at.strip(),
            "status": "requested",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="counseling.appointment_requested",
            aggregate_type="counseling_appointment",
            aggregate_id=str(record["id"]),
            payload_json={"student_id": student_id, "session_type": session_type},
        )
    except Exception:
        pass

    result = CounselingAppointment(
        appointment_id=record["id"],
        student_id=student_id,
        counselor_id=counselor_id,
        session_type=session_type,
        status="requested",
        scheduled_at=scheduled_at.strip(),
        tenant_id=tenant_id,
    )
    _record_outcome(record["id"], "counseling_appointment_requested", str(student_id))
    _metric(tenant_id, "counseling_appointments_requested")
    return result


def confirm_appointment(*, appointment_id: int, tenant_id: int) -> CounselingAppointment:
    """Counselor confirms the appointment."""
    if not appointment_id or appointment_id <= 0:
        raise CounselingError("appointment_id is required")

    appts = list_entities_for_tenant("counseling_appointments", tenant_id)
    matched = [a for a in appts if a["id"] == appointment_id]
    if not matched:
        raise CounselingError(f"appointment {appointment_id} not found")

    appt = matched[0]
    if appt["status"] != "requested":
        raise CounselingError(
            f"cannot confirm appointment in status {appt['status']!r}; must be 'requested'"
        )

    update_entity_for_tenant(
        "counseling_appointments", appointment_id, {"status": "confirmed"}, tenant_id
    )

    return CounselingAppointment(
        appointment_id=appointment_id,
        student_id=appt["student_id"],
        counselor_id=appt["counselor_id"],
        session_type=appt["session_type"],
        status="confirmed",
        scheduled_at=appt["scheduled_at"],
        tenant_id=tenant_id,
    )


def complete_appointment(*, appointment_id: int, notes: str, tenant_id: int) -> CounselingAppointment:
    """Mark appointment as completed with session notes."""
    if not appointment_id or appointment_id <= 0:
        raise CounselingError("appointment_id is required")
    if not notes or not notes.strip():
        raise CounselingError("notes are required to complete an appointment")

    appts = list_entities_for_tenant("counseling_appointments", tenant_id)
    matched = [a for a in appts if a["id"] == appointment_id]
    if not matched:
        raise CounselingError(f"appointment {appointment_id} not found")

    appt = matched[0]
    if appt["status"] != "confirmed":
        raise CounselingError(
            f"cannot complete appointment in status {appt['status']!r}; must be 'confirmed'"
        )

    update_entity_for_tenant(
        "counseling_appointments",
        appointment_id,
        {"status": "completed", "notes": notes.strip()},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="counseling.session_completed",
            aggregate_type="counseling_appointment",
            aggregate_id=str(appointment_id),
            payload_json={"student_id": appt["student_id"], "appointment_id": appointment_id},
        )
    except Exception:
        pass

    return CounselingAppointment(
        appointment_id=appointment_id,
        student_id=appt["student_id"],
        counselor_id=appt["counselor_id"],
        session_type=appt["session_type"],
        status="completed",
        scheduled_at=appt["scheduled_at"],
        tenant_id=tenant_id,
    )


def cancel_appointment(*, appointment_id: int, tenant_id: int) -> CounselingAppointment:
    """Cancel a requested or confirmed appointment."""
    if not appointment_id or appointment_id <= 0:
        raise CounselingError("appointment_id is required")

    appts = list_entities_for_tenant("counseling_appointments", tenant_id)
    matched = [a for a in appts if a["id"] == appointment_id]
    if not matched:
        raise CounselingError(f"appointment {appointment_id} not found")

    appt = matched[0]
    if appt["status"] not in ("requested", "confirmed"):
        raise CounselingError(
            f"cannot cancel appointment in status {appt['status']!r}"
        )

    update_entity_for_tenant(
        "counseling_appointments", appointment_id, {"status": "cancelled"}, tenant_id
    )

    return CounselingAppointment(
        appointment_id=appointment_id,
        student_id=appt["student_id"],
        counselor_id=appt["counselor_id"],
        session_type=appt["session_type"],
        status="cancelled",
        scheduled_at=appt["scheduled_at"],
        tenant_id=tenant_id,
    )


def list_appointments(*, student_id: int, tenant_id: int) -> list[CounselingAppointment]:
    """List all appointments for a student."""
    rows = list_entities_for_tenant("counseling_appointments", tenant_id)
    return [
        CounselingAppointment(
            appointment_id=r["id"],
            student_id=r["student_id"],
            counselor_id=r["counselor_id"],
            session_type=r["session_type"],
            status=r["status"],
            scheduled_at=r["scheduled_at"],
            tenant_id=tenant_id,
        )
        for r in rows
        if r.get("student_id") == student_id
    ]


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


def open_case(
    *,
    student_id: int,
    counselor_id: int,
    risk_level: str,
    tenant_id: int,
) -> CounselingCase:
    """Open a counseling case for ongoing support."""
    if not student_id or student_id <= 0:
        raise CounselingError("student_id is required")
    if risk_level not in RISK_LEVELS:
        raise CounselingError(f"invalid risk_level: {risk_level!r}; must be one of {RISK_LEVELS}")

    record = create_entity_for_tenant(
        "counseling_cases",
        {
            "student_id": student_id,
            "counselor_id": counselor_id,
            "risk_level": risk_level,
            "status": "open",
        },
        tenant_id,
    )

    if risk_level in ("high", "critical"):
        try:
            EventPublisher.publish(
                tenant_id=tenant_id,
                event_type="counseling.high_risk_case_opened",
                aggregate_type="counseling_case",
                aggregate_id=str(record["id"]),
                payload_json={"student_id": student_id, "risk_level": risk_level},
            )
        except Exception:
            pass

    result = CounselingCase(
        case_id=record["id"],
        student_id=student_id,
        counselor_id=counselor_id,
        risk_level=risk_level,
        status="open",
        tenant_id=tenant_id,
    )
    _record_outcome(record["id"], "counseling_case_opened", str(student_id))
    _metric(tenant_id, "counseling_cases_opened")
    return result


def escalate_case(*, case_id: int, risk_level: str, tenant_id: int) -> CounselingCase:
    """Escalate a case to a higher risk level."""
    if risk_level not in RISK_LEVELS:
        raise CounselingError(f"invalid risk_level: {risk_level!r}")

    cases = list_entities_for_tenant("counseling_cases", tenant_id)
    matched = [c for c in cases if c["id"] == case_id]
    if not matched:
        raise CounselingError(f"case {case_id} not found")

    case = matched[0]
    if case["status"] not in ("open", "active"):
        raise CounselingError(f"cannot escalate case in status {case['status']!r}")

    update_entity_for_tenant(
        "counseling_cases", case_id, {"risk_level": risk_level, "status": "active"}, tenant_id
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="counseling.case_escalated",
            aggregate_type="counseling_case",
            aggregate_id=str(case_id),
            payload_json={"student_id": case["student_id"], "risk_level": risk_level},
        )
    except Exception:
        pass

    return CounselingCase(
        case_id=case_id,
        student_id=case["student_id"],
        counselor_id=case["counselor_id"],
        risk_level=risk_level,
        status="active",
        tenant_id=tenant_id,
    )


def close_case(*, case_id: int, tenant_id: int) -> CounselingCase:
    """Close a counseling case."""
    cases = list_entities_for_tenant("counseling_cases", tenant_id)
    matched = [c for c in cases if c["id"] == case_id]
    if not matched:
        raise CounselingError(f"case {case_id} not found")

    case = matched[0]
    if case["status"] == "closed":
        raise CounselingError("case is already closed")

    update_entity_for_tenant("counseling_cases", case_id, {"status": "closed"}, tenant_id)

    return CounselingCase(
        case_id=case_id,
        student_id=case["student_id"],
        counselor_id=case["counselor_id"],
        risk_level=case["risk_level"],
        status="closed",
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# Crisis reporting
# ---------------------------------------------------------------------------


def report_crisis(
    *,
    student_id: int,
    risk_level: str,
    description: str,
    tenant_id: int,
) -> CrisisReport:
    """Report a mental health crisis for immediate intervention."""
    if not student_id or student_id <= 0:
        raise CounselingError("student_id is required")
    if risk_level not in RISK_LEVELS:
        raise CounselingError(f"invalid risk_level: {risk_level!r}")
    if not description or not description.strip():
        raise CounselingError("description is required for crisis report")

    record = create_entity_for_tenant(
        "crisis_reports",
        {
            "student_id": student_id,
            "risk_level": risk_level,
            "description": description.strip(),
            "status": "open",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="counseling.crisis_reported",
            aggregate_type="crisis_report",
            aggregate_id=str(record["id"]),
            payload_json={"student_id": student_id, "risk_level": risk_level},
        )
    except Exception:
        pass

    result = CrisisReport(
        report_id=record["id"],
        student_id=student_id,
        risk_level=risk_level,
        description=description.strip(),
        tenant_id=tenant_id,
    )
    _record_outcome(record["id"], "crisis_report_created", str(student_id))
    _metric(tenant_id, "crisis_reports_created")
    return result
