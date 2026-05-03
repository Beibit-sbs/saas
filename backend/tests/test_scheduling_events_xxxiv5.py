"""Phase XXXIV.5 — scheduling lifecycle event/entity tests (10-step loop hardening)."""
from __future__ import annotations

import asyncio
from datetime import time
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.scheduling.models import DayOfWeek, InstructorRole, SectionStatus
from app.modules.scheduling.schemas import (
    CourseSectionCreateSchema,
    InstructorAssignmentSchema,
    SectionCancelSchema,
    SectionRescheduleSchema,
    SectionScheduleCreateSchema,
)
from app.modules.scheduling.service import SchedulingService


def _run(coro):
    return asyncio.run(coro)


def _make_db():
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []
    return db


def _make_section(status=SectionStatus.PLANNED, version=1, capacity=30):
    s = MagicMock()
    s.id = 1
    s.tenant_id = 1
    s.status = status
    s.max_capacity = capacity
    s.instructor_id = None
    s.version = version
    return s


def _make_slot():
    s = MagicMock()
    s.id = 1
    s.start_time = time(9, 0)
    s.end_time = time(10, 0)
    s.is_active = True
    return s


def _make_classroom(capacity=50):
    c = MagicMock()
    c.id = 1
    c.tenant_id = 1
    c.capacity = capacity
    c.is_active = True
    return c


def _make_schedule(version=1):
    s = MagicMock()
    s.id = 1
    s.tenant_id = 1
    s.version = version
    s.time_slot_id = 1
    s.classroom_id = 1
    s.day_of_week = DayOfWeek.MONDAY
    return s


def _section_create_payload():
    return CourseSectionCreateSchema(
        course_id=1,
        term_id=1,
        section_code="CS101-A",
        max_capacity=30,
        instructor_id=None,
    )


def _schedule_payload():
    return SectionScheduleCreateSchema(
        time_slot_id=1,
        classroom_id=1,
        day_of_week=DayOfWeek.MONDAY,
    )


# ---------------------------------------------------------------------------
# Test 1: create_course_section publishes scheduling.section.created
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.CourseSectionReadSchema")
def test_create_section_publishes_section_created(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    svc = SchedulingService(db_session=db)
    svc._load_course_placeholder = MagicMock(return_value=MagicMock())
    svc._validate_term_exists = MagicMock(return_value=None)

    with patch("app.modules.scheduling.service.EventPublisher") as mock_ep:
        publisher = MagicMock()
        mock_ep.return_value = publisher

        _run(svc.create_course_section(tenant_id=1, request=_section_create_payload(), actor_id="admin@test.com"))

    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "scheduling.section.created" in event_types


# ---------------------------------------------------------------------------
# Test 2: schedule_section publishes scheduling.section.scheduled
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.SectionScheduleReadSchema")
def test_schedule_section_publishes_section_scheduled(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section()
    slot = _make_slot()
    classroom = _make_classroom()
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._load_time_slot = MagicMock(return_value=slot)
    svc._load_classroom = MagicMock(return_value=classroom)
    svc._get_room_conflict = MagicMock(return_value=None)
    svc._find_instructor_conflicts = MagicMock(return_value=[])
    svc._load_section_schedule = MagicMock(return_value=None)

    with patch("app.modules.scheduling.service.EventPublisher") as mock_ep:
        publisher = MagicMock()
        mock_ep.return_value = publisher
        with patch("app.modules.scheduling.service._create_tenant_entity", return_value=None):
            _run(svc.schedule_section(tenant_id=1, section_id=1, request=_schedule_payload(), actor_id="admin@test.com"))

    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "scheduling.section.scheduled" in event_types


# ---------------------------------------------------------------------------
# Test 3: schedule_section creates action_log and outcome entities
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.SectionScheduleReadSchema")
def test_schedule_section_creates_action_log_and_outcome(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section()
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._load_time_slot = MagicMock(return_value=_make_slot())
    svc._load_classroom = MagicMock(return_value=_make_classroom())
    svc._get_room_conflict = MagicMock(return_value=None)
    svc._find_instructor_conflicts = MagicMock(return_value=[])
    svc._load_section_schedule = MagicMock(return_value=None)

    created_entities: list[tuple] = []

    def _capture_entity(entity_name, tenant_id, payload):
        created_entities.append((entity_name, tenant_id, payload))
        return {"id": len(created_entities), **payload}

    with patch("app.modules.scheduling.service.EventPublisher"):
        with patch("app.modules.scheduling.service._create_tenant_entity", side_effect=_capture_entity):
            _run(svc.schedule_section(tenant_id=1, section_id=1, request=_schedule_payload(), actor_id="admin@test.com"))

    entity_names = [e[0] for e in created_entities]
    assert "scheduling_section_action_logs" in entity_names
    assert "scheduling_section_outcomes" in entity_names


# ---------------------------------------------------------------------------
# Test 4: cancel_section publishes scheduling.section.cancelled
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.CourseSectionReadSchema")
def test_cancel_section_publishes_section_cancelled(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section(version=1)
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)

    cancel_req = SectionCancelSchema(expected_version=1)

    with patch("app.modules.scheduling.service.EventPublisher") as mock_ep:
        publisher = MagicMock()
        mock_ep.return_value = publisher
        with patch("app.modules.scheduling.service._create_tenant_entity", return_value=None):
            _run(svc.cancel_section(tenant_id=1, section_id=1, request=cancel_req, actor_id="admin@test.com"))

    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "scheduling.section.cancelled" in event_types


# ---------------------------------------------------------------------------
# Test 5: cancel_section creates cancellation outcome entity
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.CourseSectionReadSchema")
def test_cancel_section_creates_outcome_entity(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section(version=1)
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)

    cancel_req = SectionCancelSchema(expected_version=1)
    created_entities: list[str] = []

    with patch("app.modules.scheduling.service.EventPublisher"):
        with patch("app.modules.scheduling.service._create_tenant_entity", side_effect=lambda n, t, p: created_entities.append(n)):
            _run(svc.cancel_section(tenant_id=1, section_id=1, request=cancel_req, actor_id="admin@test.com"))

    assert "scheduling_section_outcomes" in created_entities


# ---------------------------------------------------------------------------
# Test 6: assign_instructor publishes scheduling.instructor.assigned
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
def test_assign_instructor_publishes_instructor_assigned(mock_audit, mock_billing):
    db = _make_db()
    section = _make_section()
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._check_instructor_has_active_contract = MagicMock(return_value=None)

    assign_req = InstructorAssignmentSchema(instructor_id="prof@univ.edu", role=InstructorRole.PRIMARY)

    with patch("app.modules.scheduling.service.EventPublisher") as mock_ep:
        publisher = MagicMock()
        mock_ep.return_value = publisher
        _run(svc.assign_instructor(tenant_id=1, section_id=1, request=assign_req, actor_id="admin@test.com"))

    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "scheduling.instructor.assigned" in event_types


# ---------------------------------------------------------------------------
# Test 7: assign_instructor guard blocks terminated contract (fail-closed)
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
def test_assign_instructor_guard_blocks_terminated_contract(mock_billing):
    db = _make_db()
    section = _make_section()
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._check_instructor_has_active_contract = MagicMock(
        side_effect=DomainValidationError("instructor has no active contract")
    )

    assign_req = InstructorAssignmentSchema(instructor_id="fired@univ.edu", role=InstructorRole.PRIMARY)

    with pytest.raises(DomainValidationError, match="active contract"):
        _run(svc.assign_instructor(tenant_id=1, section_id=1, request=assign_req, actor_id="admin@test.com"))


# ---------------------------------------------------------------------------
# Test 8: reschedule_section publishes scheduling.section.rescheduled
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.SectionScheduleReadSchema")
def test_reschedule_section_publishes_section_rescheduled(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section(status=SectionStatus.SCHEDULED)
    schedule = _make_schedule(version=1)
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._load_section_schedule = MagicMock(return_value=schedule)
    svc._load_time_slot = MagicMock(return_value=_make_slot())
    svc._load_classroom = MagicMock(return_value=_make_classroom())
    svc._get_room_conflict = MagicMock(return_value=None)
    svc._find_instructor_conflicts = MagicMock(return_value=[])

    resched_req = SectionRescheduleSchema(
        time_slot_id=2,
        classroom_id=2,
        day_of_week=DayOfWeek.TUESDAY,
        expected_version=1,
    )

    with patch("app.modules.scheduling.service.EventPublisher") as mock_ep:
        publisher = MagicMock()
        mock_ep.return_value = publisher
        _run(svc.reschedule_section(tenant_id=1, section_id=1, request=resched_req, actor_id="admin@test.com"))

    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "scheduling.section.rescheduled" in event_types


# ---------------------------------------------------------------------------
# Test 9: create_section survives event publisher failure (fire-and-forget)
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.CourseSectionReadSchema")
def test_create_section_survives_event_publisher_failure(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    svc = SchedulingService(db_session=db)
    svc._load_course_placeholder = MagicMock(return_value=MagicMock())
    svc._validate_term_exists = MagicMock(return_value=None)

    with patch("app.modules.scheduling.service.EventPublisher") as mock_ep:
        publisher = MagicMock()
        publisher.publish_event.side_effect = RuntimeError("kafka down")
        mock_ep.return_value = publisher

        # Should not raise — event is fire-and-forget
        result = _run(svc.create_course_section(tenant_id=1, request=_section_create_payload(), actor_id="admin@test.com"))

    assert result is not None


# ---------------------------------------------------------------------------
# Test 10: schedule_section entity log failure does not prevent scheduling
# ---------------------------------------------------------------------------


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.SectionScheduleReadSchema")
def test_schedule_section_entity_log_failure_doesnt_block_schedule(mock_schema, mock_audit, mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section()
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._load_time_slot = MagicMock(return_value=_make_slot())
    svc._load_classroom = MagicMock(return_value=_make_classroom())
    svc._get_room_conflict = MagicMock(return_value=None)
    svc._find_instructor_conflicts = MagicMock(return_value=[])
    svc._load_section_schedule = MagicMock(return_value=None)

    with patch("app.modules.scheduling.service.EventPublisher"):
        with patch("app.modules.scheduling.service._create_tenant_entity", side_effect=Exception("DB unreachable")):
            # Should not raise — entity creation is fire-and-forget
            result = _run(svc.schedule_section(
                tenant_id=1, section_id=1, request=_schedule_payload(), actor_id="admin@test.com"
            ))

    assert result is not None
