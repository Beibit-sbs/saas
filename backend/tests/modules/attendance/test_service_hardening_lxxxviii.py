"""
LXXXVIII — Attendance Service Hardening Tests.

Verifies:
  1. mark_attendance persists record BEFORE firing event (persist-first).
  2. mark_attendance survives publisher failure (fire-and-forget).
  3. check_low_attendance_risk uses canonical tenant API signature.
  4. excuse_absence persists first — no rollback when event publish fails.
"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

MODULE = "app.modules.attendance.service"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_record(
    *,
    id: str = "rec-1",
    student_id: str = "s-1",
    session_id: str = "sess-1",
    status: str = "ABSENT",
    tenant_id: int = 1,
) -> dict:
    return {
        "id": id,
        "student_id": student_id,
        "session_id": session_id,
        "status": status,
        "tenant_id": tenant_id,
    }


# ─── test 1 ───────────────────────────────────────────────────────────────────

def test_mark_attendance_persists_before_event():
    """create_entity_for_tenant must be called BEFORE EventPublisher.publish_event."""
    call_order: list[str] = []

    fake_record = _make_record(id="rec-42", status="PRESENT")

    def fake_create(entity_name, payload, tenant_id):
        call_order.append("persist")
        return fake_record

    def fake_publish(self, **kwargs):
        call_order.append("event")

    with (
        patch(f"{MODULE}.create_entity_for_tenant", side_effect=fake_create),
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.EventPublisher.publish_event", fake_publish),
    ):
        from app.modules.attendance import service as svc

        svc.mark_attendance(
            1, session_id="sess-1", student_id="s-1", status="PRESENT"
        )

    assert call_order == ["persist", "event"], (
        "persist must come before event publish"
    )


# ─── test 2 ───────────────────────────────────────────────────────────────────

def test_mark_attendance_survives_publish_failure():
    """mark_attendance must succeed even when EventPublisher raises."""
    fake_record = _make_record(id="rec-7", status="PRESENT")

    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=fake_record),
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(
            f"{MODULE}.EventPublisher.publish_event",
            side_effect=RuntimeError("kafka down"),
        ),
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.attendance import service as svc

        result = svc.mark_attendance(
            1, session_id="sess-1", student_id="s-1", status="PRESENT"
        )

    assert result["status"] == "PRESENT"
    assert result["record_id"] == "rec-7"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()


# ─── test 3 ───────────────────────────────────────────────────────────────────

def test_check_low_attendance_risk_uses_canonical_tenant_api():
    """list_entities_for_tenant must be called with positional args (entity, tenant_id)."""
    # Provide minimal records so risk is triggered.
    absent_record = _make_record(status="ABSENT")
    session = {"id": "sess-1", "course_id": "c-1", "tenant_id": 1}
    risk_record = {
        "id": "risk-1",
        "student_id": "s-1",
        "course_id": "c-1",
        "attendance_pct": 0.0,
        "tenant_id": 1,
    }

    mock_list = MagicMock(side_effect=lambda entity, tid: {
        "attendance_records": [absent_record],
        "attendance_sessions": [session],
    }.get(entity, []))

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=risk_record),
        patch(f"{MODULE}.EventPublisher.publish_event", return_value=None),
    ):
        from app.modules.attendance import service as svc

        result = svc.check_low_attendance_risk(
            1, student_id="s-1", course_id="c-1"
        )

    # Every call must pass tenant_id as 2nd positional, NOT as keyword arg.
    for c in mock_list.call_args_list:
        args, kwargs = c
        assert len(args) == 2, (
            f"list_entities_for_tenant called with kwargs instead of positional: {c}"
        )
        assert "tenant_id" not in kwargs, (
            f"tenant_id must be positional, not keyword: {c}"
        )

    assert result.get("risk_record_id") == "risk-1"


# ─── test 4 ───────────────────────────────────────────────────────────────────

def test_excuse_absence_persist_before_event_no_rollback():
    """excuse_absence must persist the excuse record even if event publish fails."""
    absent_record = _make_record(id="rec-1", status="ABSENT")
    excuse_record = {
        "id": "exc-1",
        "record_id": "rec-1",
        "reason": "medical",
        "tenant_id": 1,
    }

    mock_create = MagicMock(return_value=excuse_record)

    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[absent_record]),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(
            f"{MODULE}.EventPublisher.publish_event",
            side_effect=Exception("broker unavailable"),
        ),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.attendance import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.excuse_absence(1, record_id="rec-1", reason="medical")

    # create_entity_for_tenant must have been called with positional args.
    mock_create.assert_called_once()
    args, kwargs = mock_create.call_args
    assert len(args) == 3, "create_entity_for_tenant must use positional args"
    assert "tenant_id" not in kwargs
    # Result must reflect the persisted excuse.
    assert result["excuse_id"] == "exc-1"
    assert result["status"] == "EXCUSED"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()
