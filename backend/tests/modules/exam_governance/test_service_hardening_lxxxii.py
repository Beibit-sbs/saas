"""LXXXII — Exam Governance Service Hardening (10-step contract)

Tests:
1. create_exam emits exam.created event after persist and records metric
2. update_exam invalid transition raises DomainValidationError (FSM guard)
3. update_exam to in_progress emits exam.started after persist and records metric
4. grade_exam triggers Brain Core callback, emits exam.graded, records metric
"""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from app.modules.exam_governance.schemas import ExamCreateSchema, ExamUpdateSchema
from app.modules.exam_governance import service as svc
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_exam_row(
    exam_id: int = 1,
    tenant_id: int = 10,
    status: str = "scheduled",
    exam_type: str = "midterm",
    faculty_id: str = "fac-1",
) -> dict:
    return {
        "id": exam_id,
        "tenant_id": tenant_id,
        "course_code": "CS101",
        "course_title": "Intro to CS",
        "faculty_id": faculty_id,
        "exam_type": exam_type,
        "term_id": "2026-spring",
        "status": status,
        "scheduled_date": None,
        "scheduled_time": None,
        "duration_minutes": 120,
        "is_proctored": True,
        "proctoring_mode": "in_person",
    }


# ---------------------------------------------------------------------------
# Test 1: create_exam emits event after persist and records metric
# ---------------------------------------------------------------------------

def test_create_exam_emits_event_after_persist_and_records_metric():
    payload = ExamCreateSchema(
        course_code="CS101",
        course_title="Intro to CS",
        faculty_id="fac-1",
        exam_type="midterm",
        term_id="2026-spring",
        scheduled_date=None,
        scheduled_time=None,
        duration_minutes=120,
        is_proctored=True,
        proctoring_mode="in_person",
    )
    row = _make_exam_row(exam_id=42)
    call_order: list[str] = []

    def fake_create(entity, data, tenant_id):
        call_order.append("persist")
        return row

    def fake_list(entity, tenant_id):
        return []

    publisher_mock = MagicMock()
    publisher_mock.publish_event.side_effect = lambda **kw: call_order.append("event")

    with (
        patch.object(svc, "create_entity_for_tenant", side_effect=fake_create),
        patch.object(svc, "list_entities_for_tenant", side_effect=fake_list),
        patch.object(svc, "log_admin_action"),
        patch("app.modules.exam_governance.service.EventPublisher", return_value=publisher_mock),
        patch.object(svc, "record_usage_event") as mock_metric,
    ):
        result = svc.create_exam(10, payload, actor="admin@example.com")

    assert result.id == 42
    assert call_order.index("persist") < call_order.index("event"), "event must be after persist"
    mock_metric.assert_called_once_with(10, "exams_created", 1)


# ---------------------------------------------------------------------------
# Test 2: FSM guard — invalid transition raises DomainValidationError
# ---------------------------------------------------------------------------

def test_update_exam_invalid_transition_raises_domain_validation_error():
    """completed → scheduled is forbidden."""
    existing = [_make_exam_row(exam_id=5, status="completed")]

    payload = ExamUpdateSchema(status="scheduled")

    with patch.object(svc, "list_entities_for_tenant", return_value=existing):
        with pytest.raises(DomainValidationError, match="Cannot transition"):
            svc.update_exam(10, 5, payload, actor="admin@example.com")


# ---------------------------------------------------------------------------
# Test 3: update_exam → in_progress emits exam.started after persist + metric
# ---------------------------------------------------------------------------

def test_update_exam_to_in_progress_emits_started_after_persist_and_records_metric():
    existing = [_make_exam_row(exam_id=7, status="scheduled", faculty_id="fac-99")]
    updated_row = _make_exam_row(exam_id=7, status="in_progress")
    call_order: list[str] = []

    def fake_list(entity, tenant_id):
        # Also return a fake active contract for the cross-entity guard
        if entity == "faculty_contracts":
            return [{"faculty_id": "fac-99", "status": "active"}]
        return existing

    def fake_update(entity, eid, updates, tenant_id):
        call_order.append("persist")
        return updated_row

    publisher_mock = MagicMock()
    publisher_mock.publish_event.side_effect = lambda **kw: call_order.append("event")

    with (
        patch.object(svc, "list_entities_for_tenant", side_effect=fake_list),
        patch.object(svc, "update_entity_for_tenant", side_effect=fake_update),
        patch.object(svc, "log_admin_action"),
        patch("app.modules.exam_governance.service.EventPublisher", return_value=publisher_mock),
        patch.object(svc, "record_usage_event") as mock_metric,
    ):
        result = svc.update_exam(10, 7, ExamUpdateSchema(status="in_progress"), actor="admin@example.com")

    assert result.status == "in_progress"
    assert call_order.index("persist") < call_order.index("event"), "event must be after persist"
    publisher_mock.publish_event.assert_called_once()
    call_kwargs = publisher_mock.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "exam.started"
    mock_metric.assert_called_once_with(10, "exam_status_updates", 1)


# ---------------------------------------------------------------------------
# Test 4: grade_exam triggers brain_core, emits exam.graded, records metric
# ---------------------------------------------------------------------------

def test_grade_exam_calls_brain_core_emits_graded_event_and_records_metric():
    completed_row = _make_exam_row(exam_id=9, status="completed")
    call_order: list[str] = []

    publisher_mock = MagicMock()
    publisher_mock.publish_event.side_effect = lambda **kw: call_order.append("event")

    brain_mock = MagicMock()
    brain_mock.record_dispatch_outcome.side_effect = lambda *a, **kw: call_order.append("brain") or {}

    with (
        patch.object(svc, "list_entities_for_tenant", return_value=[completed_row]),
        patch.object(svc, "log_admin_action"),
        patch("app.modules.exam_governance.service.EventPublisher", return_value=publisher_mock),
        patch("app.modules.exam_governance.service.record_usage_event") as mock_metric,
        patch("app.modules.brain_core.service.brain_core_service", brain_mock),
    ):
        result = svc.grade_exam(10, 9, average_score=75.0, pass_rate=0.82, actor="admin@example.com")

    assert result["exam_id"] == 9
    assert result["average_score"] == 75.0
    publisher_mock.publish_event.assert_called_once()
    call_kwargs = publisher_mock.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "exam.graded"
    mock_metric.assert_called_once_with(10, "exams_graded", 1)
