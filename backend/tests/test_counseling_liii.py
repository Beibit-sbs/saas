"""Phase LIII — Counseling / Mental Health tests (20 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

BASE = "app.modules.counseling.service"


def _make_create(return_id: int = 1) -> MagicMock:
    return MagicMock(return_value={"id": return_id})


def _appt_row(
    appt_id: int = 1,
    student_id: int = 10,
    counselor_id: int = 5,
    session_type: str = "individual",
    status: str = "requested",
    scheduled_at: str = "2026-06-01T10:00",
) -> dict:
    return {
        "id": appt_id,
        "student_id": student_id,
        "counselor_id": counselor_id,
        "session_type": session_type,
        "status": status,
        "scheduled_at": scheduled_at,
    }


def _case_row(
    case_id: int = 1,
    student_id: int = 10,
    counselor_id: int = 5,
    risk_level: str = "medium",
    status: str = "open",
) -> dict:
    return {
        "id": case_id,
        "student_id": student_id,
        "counselor_id": counselor_id,
        "risk_level": risk_level,
        "status": status,
    }


# ── request_appointment ───────────────────────────────────────────────────────

def test_request_appointment_success():
    with patch(f"{BASE}.create_entity_for_tenant", _make_create(1)), \
         patch(f"{BASE}.EventPublisher") as ep:
        from app.modules.counseling.service import request_appointment
        result = request_appointment(
            student_id=10, counselor_id=5, session_type="individual",
            scheduled_at="2026-06-01T10:00", tenant_id=1
        )
    assert result.appointment_id == 1
    assert result.status == "requested"
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "counseling.appointment_requested"


def test_request_appointment_invalid_type():
    from app.modules.counseling.service import request_appointment, CounselingError
    with pytest.raises(CounselingError, match="session_type"):
        request_appointment(student_id=1, counselor_id=2, session_type="chat",
                            scheduled_at="2026-06-01", tenant_id=1)


def test_request_appointment_missing_student():
    from app.modules.counseling.service import request_appointment, CounselingError
    with pytest.raises(CounselingError, match="student_id"):
        request_appointment(student_id=0, counselor_id=2, session_type="group",
                            scheduled_at="2026-06-01", tenant_id=1)


def test_request_appointment_missing_scheduled_at():
    from app.modules.counseling.service import request_appointment, CounselingError
    with pytest.raises(CounselingError, match="scheduled_at"):
        request_appointment(student_id=1, counselor_id=2, session_type="crisis",
                            scheduled_at="   ", tenant_id=1)


# ── confirm_appointment ───────────────────────────────────────────────────────

def test_confirm_appointment_success():
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[_appt_row()]), \
         patch(f"{BASE}.update_entity_for_tenant") as upd:
        from app.modules.counseling.service import confirm_appointment
        result = confirm_appointment(appointment_id=1, tenant_id=1)
    assert result.status == "confirmed"
    upd.assert_called_once()


def test_confirm_appointment_wrong_status():
    row = _appt_row(status="cancelled")
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.counseling.service import confirm_appointment, CounselingError
        with pytest.raises(CounselingError, match="requested"):
            confirm_appointment(appointment_id=1, tenant_id=1)


def test_confirm_appointment_not_found():
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[]):
        from app.modules.counseling.service import confirm_appointment, CounselingError
        with pytest.raises(CounselingError, match="not found"):
            confirm_appointment(appointment_id=99, tenant_id=1)


# ── complete_appointment ──────────────────────────────────────────────────────

def test_complete_appointment_success():
    row = _appt_row(status="confirmed")
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[row]), \
         patch(f"{BASE}.update_entity_for_tenant"), \
         patch(f"{BASE}.EventPublisher") as ep:
        from app.modules.counseling.service import complete_appointment
        result = complete_appointment(appointment_id=1, notes="Good session", tenant_id=1)
    assert result.status == "completed"
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "counseling.session_completed"


def test_complete_appointment_missing_notes():
    row = _appt_row(status="confirmed")
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.counseling.service import complete_appointment, CounselingError
        with pytest.raises(CounselingError, match="notes"):
            complete_appointment(appointment_id=1, notes="", tenant_id=1)


def test_complete_appointment_wrong_status():
    row = _appt_row(status="requested")
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.counseling.service import complete_appointment, CounselingError
        with pytest.raises(CounselingError, match="confirmed"):
            complete_appointment(appointment_id=1, notes="notes", tenant_id=1)


# ── cancel_appointment ────────────────────────────────────────────────────────

def test_cancel_appointment_success():
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[_appt_row()]), \
         patch(f"{BASE}.update_entity_for_tenant"):
        from app.modules.counseling.service import cancel_appointment
        result = cancel_appointment(appointment_id=1, tenant_id=1)
    assert result.status == "cancelled"


def test_cancel_appointment_completed_fails():
    row = _appt_row(status="completed")
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.counseling.service import cancel_appointment, CounselingError
        with pytest.raises(CounselingError, match="cancel"):
            cancel_appointment(appointment_id=1, tenant_id=1)


# ── open_case ─────────────────────────────────────────────────────────────────

def test_open_case_low_risk_no_event():
    with patch(f"{BASE}.create_entity_for_tenant", _make_create(5)), \
         patch(f"{BASE}.EventPublisher") as ep:
        from app.modules.counseling.service import open_case
        result = open_case(student_id=10, counselor_id=3, risk_level="low", tenant_id=1)
    assert result.status == "open"
    ep.publish.assert_not_called()


def test_open_case_critical_fires_event():
    with patch(f"{BASE}.create_entity_for_tenant", _make_create(6)), \
         patch(f"{BASE}.EventPublisher") as ep:
        from app.modules.counseling.service import open_case
        open_case(student_id=10, counselor_id=3, risk_level="critical", tenant_id=1)
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "counseling.high_risk_case_opened"


def test_open_case_invalid_risk_level():
    from app.modules.counseling.service import open_case, CounselingError
    with pytest.raises(CounselingError, match="risk_level"):
        open_case(student_id=1, counselor_id=2, risk_level="extreme", tenant_id=1)


# ── escalate_case ─────────────────────────────────────────────────────────────

def test_escalate_case_fires_event():
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[_case_row()]), \
         patch(f"{BASE}.update_entity_for_tenant"), \
         patch(f"{BASE}.EventPublisher") as ep:
        from app.modules.counseling.service import escalate_case
        result = escalate_case(case_id=1, risk_level="critical", tenant_id=1)
    assert result.risk_level == "critical"
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "counseling.case_escalated"


def test_escalate_case_closed_fails():
    row = _case_row(status="closed")
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[row]):
        from app.modules.counseling.service import escalate_case, CounselingError
        with pytest.raises(CounselingError, match="escalate"):
            escalate_case(case_id=1, risk_level="high", tenant_id=1)


# ── close_case ────────────────────────────────────────────────────────────────

def test_close_case_success():
    with patch(f"{BASE}.list_entities_for_tenant", return_value=[_case_row()]), \
         patch(f"{BASE}.update_entity_for_tenant"):
        from app.modules.counseling.service import close_case
        result = close_case(case_id=1, tenant_id=1)
    assert result.status == "closed"


# ── report_crisis ─────────────────────────────────────────────────────────────

def test_report_crisis_fires_event():
    with patch(f"{BASE}.create_entity_for_tenant", _make_create(9)), \
         patch(f"{BASE}.EventPublisher") as ep:
        from app.modules.counseling.service import report_crisis
        result = report_crisis(
            student_id=7, risk_level="critical",
            description="Student expressed suicidal ideation", tenant_id=1
        )
    assert result.report_id == 9
    ep.publish.assert_called_once()
    assert ep.publish.call_args.kwargs["event_type"] == "counseling.crisis_reported"


def test_report_crisis_missing_description():
    from app.modules.counseling.service import report_crisis, CounselingError
    with pytest.raises(CounselingError, match="description"):
        report_crisis(student_id=1, risk_level="high", description="", tenant_id=1)
