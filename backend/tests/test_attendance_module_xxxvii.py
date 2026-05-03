"""Tests for Phase XXXVII — Attendance Module."""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from app.modules.attendance.service import (
    LOW_ATTENDANCE_THRESHOLD,
    VALID_STATUSES,
    check_low_attendance_risk,
    excuse_absence,
    get_attendance_summary,
    list_attendance_records,
    mark_attendance,
)

TENANT = 1

# ─── helpers ──────────────────────────────────────────────────────────────────

def _rec(id_="r1", session_id="s1", student_id="st1", status="PRESENT", course_id=None):
    d = {"id": id_, "session_id": session_id, "student_id": student_id, "status": status}
    if course_id:
        d["course_id"] = course_id
    return d


def _session(id_="s1", course_id="c1"):
    return {"id": id_, "course_id": course_id}


# ─── constants ────────────────────────────────────────────────────────────────

def test_valid_statuses():
    assert VALID_STATUSES == {"PRESENT", "ABSENT", "EXCUSED", "LATE"}


def test_low_attendance_threshold():
    assert LOW_ATTENDANCE_THRESHOLD == 0.75


# ─── mark_attendance ─────────────────────────────────────────────────────────

def test_mark_attendance_present_fires_marked_event():
    with (
        patch("app.modules.attendance.service.create_entity_for_tenant", return_value={"id": "r1"}) as mock_create,
        patch("app.modules.attendance.service.EventPublisher") as mock_pub,
    ):
        result = mark_attendance(TENANT, session_id="s1", student_id="st1", status="PRESENT")
        assert result["status"] == "PRESENT"
        assert result["record_id"] == "r1"
        mock_create.assert_called_once()
        instance = mock_pub.return_value
        instance.publish_event.assert_called_once()
        call_kwargs = instance.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "attendance.record.marked"


def test_mark_attendance_absent_fires_absence_event():
    with (
        patch("app.modules.attendance.service.create_entity_for_tenant", return_value={"id": "r2"}),
        patch("app.modules.attendance.service.EventPublisher") as mock_pub,
    ):
        result = mark_attendance(TENANT, session_id="s1", student_id="st2", status="ABSENT")
        assert result["status"] == "ABSENT"
        instance = mock_pub.return_value
        call_kwargs = instance.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "attendance.absence.recorded"


def test_mark_attendance_late_fires_marked_event():
    with (
        patch("app.modules.attendance.service.create_entity_for_tenant", return_value={"id": "r3"}),
        patch("app.modules.attendance.service.EventPublisher") as mock_pub,
    ):
        result = mark_attendance(TENANT, session_id="s1", student_id="st3", status="LATE")
        instance = mock_pub.return_value
        call_kwargs = instance.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "attendance.record.marked"


def test_mark_attendance_invalid_status():
    with pytest.raises(ValueError, match="Invalid status"):
        mark_attendance(TENANT, session_id="s1", student_id="st1", status="MISSING")


def test_mark_attendance_invalid_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        mark_attendance(0, session_id="s1", student_id="st1", status="PRESENT")


def test_mark_attendance_missing_session():
    with pytest.raises(ValueError, match="session_id"):
        mark_attendance(TENANT, session_id="", student_id="st1", status="PRESENT")


def test_mark_attendance_missing_student():
    with pytest.raises(ValueError, match="student_id"):
        mark_attendance(TENANT, session_id="s1", student_id="", status="PRESENT")


# ─── excuse_absence ──────────────────────────────────────────────────────────

def test_excuse_absence_success():
    absent_rec = _rec(id_="r1", status="ABSENT")
    with (
        patch("app.modules.attendance.service.list_entities_for_tenant", return_value=[absent_rec]),
        patch("app.modules.attendance.service.create_entity_for_tenant", return_value={"id": "e1"}),
        patch("app.modules.attendance.service.EventPublisher") as mock_pub,
    ):
        result = excuse_absence(TENANT, record_id="r1", reason="Medical")
        assert result["excuse_id"] == "e1"
        assert result["status"] == "EXCUSED"
        instance = mock_pub.return_value
        call_kwargs = instance.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "attendance.absence.excused"


def test_excuse_absence_not_absent_raises():
    present_rec = _rec(id_="r1", status="PRESENT")
    with (
        patch("app.modules.attendance.service.list_entities_for_tenant", return_value=[present_rec]),
    ):
        with pytest.raises(ValueError, match="only ABSENT"):
            excuse_absence(TENANT, record_id="r1", reason="Medical")


def test_excuse_absence_not_found_raises():
    with (
        patch("app.modules.attendance.service.list_entities_for_tenant", return_value=[]),
    ):
        with pytest.raises(LookupError):
            excuse_absence(TENANT, record_id="nonexistent", reason="Family")


def test_excuse_absence_missing_reason():
    with pytest.raises(ValueError, match="reason"):
        excuse_absence(TENANT, record_id="r1", reason="")


# ─── get_attendance_summary ──────────────────────────────────────────────────

def test_get_attendance_summary_all_present():
    recs = [_rec(id_=str(i), student_id="st1", status="PRESENT") for i in range(4)]
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=recs):
        summary = get_attendance_summary(TENANT, student_id="st1")
    assert summary["total_sessions"] == 4
    assert summary["present_count"] == 4
    assert summary["attendance_pct"] == 1.0
    assert summary["low_risk"] is False


def test_get_attendance_summary_low_risk():
    # 3 absent, 1 present → 25% → low_risk
    recs = [
        _rec(id_="r1", student_id="st1", status="PRESENT"),
        _rec(id_="r2", student_id="st1", status="ABSENT"),
        _rec(id_="r3", student_id="st1", status="ABSENT"),
        _rec(id_="r4", student_id="st1", status="ABSENT"),
    ]
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=recs):
        summary = get_attendance_summary(TENANT, student_id="st1")
    assert summary["low_risk"] is True
    assert summary["attendance_pct"] == 0.25


def test_get_attendance_summary_no_records():
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=[]):
        summary = get_attendance_summary(TENANT, student_id="st1")
    assert summary["total_sessions"] == 0
    assert summary["attendance_pct"] == 1.0
    assert summary["low_risk"] is False


def test_get_attendance_summary_by_course():
    sessions = [_session(id_="s1", course_id="c1"), _session(id_="s2", course_id="c2")]
    recs = [
        _rec(id_="r1", session_id="s1", student_id="st1", status="PRESENT"),
        _rec(id_="r2", session_id="s2", student_id="st1", status="ABSENT"),
    ]

    def mock_list(entity_type, tenant_id):
        if entity_type == "attendance_sessions":
            return sessions
        return recs

    with patch("app.modules.attendance.service.list_entities_for_tenant", side_effect=mock_list):
        summary = get_attendance_summary(TENANT, student_id="st1", course_id="c1")
    # Only s1 belongs to c1
    assert summary["total_sessions"] == 1
    assert summary["present_count"] == 1


def test_get_attendance_summary_late_counts_as_present():
    recs = [
        _rec(id_="r1", student_id="st1", status="LATE"),
        _rec(id_="r2", student_id="st1", status="LATE"),
    ]
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=recs):
        summary = get_attendance_summary(TENANT, student_id="st1")
    assert summary["present_count"] == 2
    assert summary["low_risk"] is False


# ─── check_low_attendance_risk ───────────────────────────────────────────────

def test_check_low_attendance_risk_fires_event_when_breached():
    recs = [
        _rec(id_="r1", session_id="s1", student_id="st1", status="ABSENT"),
        _rec(id_="r2", session_id="s2", student_id="st1", status="ABSENT"),
        _rec(id_="r3", session_id="s3", student_id="st1", status="ABSENT"),
        _rec(id_="r4", session_id="s4", student_id="st1", status="PRESENT"),
    ]
    sessions = [_session(id_=f"s{i}", course_id="c1") for i in range(1, 5)]

    def mock_list(entity_type, tenant_id):
        if entity_type == "attendance_sessions":
            return sessions
        return recs

    with (
        patch("app.modules.attendance.service.list_entities_for_tenant", side_effect=mock_list),
        patch("app.modules.attendance.service.create_entity_for_tenant", return_value={"id": "risk1"}),
        patch("app.modules.attendance.service.EventPublisher") as mock_pub,
    ):
        result = check_low_attendance_risk(TENANT, student_id="st1", course_id="c1")
    assert result["event_fired"] is True
    assert result["risk_record_id"] == "risk1"
    instance = mock_pub.return_value
    call_kwargs = instance.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "attendance.threshold.breached"


def test_check_low_attendance_risk_no_event_when_safe():
    recs = [_rec(id_=str(i), session_id=f"s{i}", student_id="st1", status="PRESENT") for i in range(4)]
    sessions = [_session(id_=f"s{i}", course_id="c1") for i in range(4)]

    def mock_list(entity_type, tenant_id):
        if entity_type == "attendance_sessions":
            return sessions
        return recs

    with (
        patch("app.modules.attendance.service.list_entities_for_tenant", side_effect=mock_list),
        patch("app.modules.attendance.service.EventPublisher") as mock_pub,
    ):
        result = check_low_attendance_risk(TENANT, student_id="st1", course_id="c1")
    assert result["event_fired"] is False
    mock_pub.return_value.publish_event.assert_not_called()


# ─── list_attendance_records ─────────────────────────────────────────────────

def test_list_attendance_records_unfiltered():
    recs = [_rec(id_="r1"), _rec(id_="r2", session_id="s2")]
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=recs):
        result = list_attendance_records(TENANT)
    assert len(result) == 2


def test_list_attendance_records_by_session():
    recs = [_rec(id_="r1", session_id="s1"), _rec(id_="r2", session_id="s2")]
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=recs):
        result = list_attendance_records(TENANT, session_id="s1")
    assert len(result) == 1
    assert result[0]["id"] == "r1"


def test_list_attendance_records_by_student():
    recs = [_rec(id_="r1", student_id="st1"), _rec(id_="r2", student_id="st2")]
    with patch("app.modules.attendance.service.list_entities_for_tenant", return_value=recs):
        result = list_attendance_records(TENANT, student_id="st2")
    assert len(result) == 1
    assert result[0]["id"] == "r2"
