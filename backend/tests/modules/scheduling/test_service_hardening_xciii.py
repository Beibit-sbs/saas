"""XCIII — Scheduling Service Hardening Tests.

Verifies:
1. create_course_section uses canonical EventPublisher constructor and records metric.
2. schedule_section uses canonical EventPublisher constructor and records metric.
3. assign_instructor survives publish failure (fire-and-forget) and still records metric.
4. cancel_section uses canonical EventPublisher constructor and records metric.
"""
from __future__ import annotations

import asyncio
from datetime import time
from unittest.mock import MagicMock, patch

from app.modules.scheduling.models import DayOfWeek, InstructorRole, SectionStatus
from app.modules.scheduling.schemas import (
    CourseSectionCreateSchema,
    InstructorAssignmentSchema,
    SectionCancelSchema,
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
    slot = MagicMock()
    slot.id = 1
    slot.start_time = time(9, 0)
    slot.end_time = time(10, 0)
    slot.is_active = True
    return slot


def _make_classroom(capacity=50):
    classroom = MagicMock()
    classroom.id = 1
    classroom.tenant_id = 1
    classroom.capacity = capacity
    classroom.is_active = True
    return classroom


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.CourseSectionReadSchema")
def test_create_section_uses_canonical_event_publisher_and_metric(mock_schema, _mock_audit, _mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    svc = SchedulingService(db_session=db)
    svc._load_course_placeholder = MagicMock(return_value=MagicMock())
    svc._validate_term_exists = MagicMock(return_value=None)

    payload = CourseSectionCreateSchema(
        course_id=1,
        term_id=1,
        section_code="CS101-A",
        max_capacity=30,
        instructor_id=None,
    )

    with (
        patch("app.modules.scheduling.service.EventPublisher") as mock_ep,
        patch("app.modules.scheduling.service.record_usage_event") as mock_metric,
    ):
        pub = MagicMock()
        mock_ep.return_value = pub
        _run(svc.create_course_section(tenant_id=1, request=payload, actor_id="admin@test.com"))

    mock_ep.assert_called_once_with()
    pub.publish_event.assert_called_once()
    mock_metric.assert_called_once_with(tenant_id=1, metric="scheduling_sections_created", value=1)


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.SectionScheduleReadSchema")
def test_schedule_section_uses_canonical_event_publisher_and_metric(mock_schema, _mock_audit, _mock_billing):
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

    payload = SectionScheduleCreateSchema(
        time_slot_id=1,
        classroom_id=1,
        day_of_week=DayOfWeek.MONDAY,
    )

    with (
        patch("app.modules.scheduling.service.EventPublisher") as mock_ep,
        patch("app.modules.scheduling.service.record_usage_event") as mock_metric,
        patch("app.modules.scheduling.service._create_tenant_entity", return_value=None),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        pub = MagicMock()
        mock_ep.return_value = pub
        mock_brain.process_signal.side_effect = RuntimeError("brain down")
        _run(svc.schedule_section(tenant_id=1, section_id=1, request=payload, actor_id="admin@test.com"))

    mock_ep.assert_called_once_with()
    pub.publish_event.assert_called_once()
    mock_metric.assert_called_once_with(tenant_id=1, metric="scheduling_sections_scheduled", value=1)


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
def test_assign_instructor_survives_publish_failure_and_records_metric(_mock_audit, _mock_billing):
    db = _make_db()
    section = _make_section()
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)
    svc._check_instructor_has_active_contract = MagicMock(return_value=None)

    payload = InstructorAssignmentSchema(instructor_id="fac-1", role=InstructorRole.PRIMARY)

    with (
        patch("app.modules.scheduling.service.EventPublisher") as mock_ep,
        patch("app.modules.scheduling.service.record_usage_event") as mock_metric,
    ):
        pub = MagicMock()
        pub.publish_event.side_effect = RuntimeError("kafka down")
        mock_ep.return_value = pub
        result = _run(svc.assign_instructor(tenant_id=1, section_id=1, request=payload, actor_id="admin@test.com"))

    assert result["section_id"] == 1
    mock_ep.assert_called_once_with()
    mock_metric.assert_called_once_with(tenant_id=1, metric="scheduling_instructor_assignments", value=1)


@patch("app.modules.scheduling.service.assert_billing_write_allowed", return_value=None)
@patch("app.modules.scheduling.service._audit", return_value=None)
@patch("app.modules.scheduling.service.CourseSectionReadSchema")
def test_cancel_section_uses_canonical_event_publisher_and_metric(mock_schema, _mock_audit, _mock_billing):
    mock_schema.model_validate.return_value = MagicMock(id=1)
    db = _make_db()
    section = _make_section(status=SectionStatus.SCHEDULED, version=1)
    svc = SchedulingService(db_session=db)
    svc._load_course_section = MagicMock(return_value=section)

    with (
        patch("app.modules.scheduling.service.EventPublisher") as mock_ep,
        patch("app.modules.scheduling.service.record_usage_event") as mock_metric,
        patch("app.modules.scheduling.service._create_tenant_entity", return_value=None),
    ):
        pub = MagicMock()
        mock_ep.return_value = pub
        _run(svc.cancel_section(tenant_id=1, section_id=1, request=SectionCancelSchema(expected_version=1), actor_id="admin@test.com"))

    mock_ep.assert_called_once_with()
    pub.publish_event.assert_called_once()
    mock_metric.assert_called_once_with(tenant_id=1, metric="scheduling_sections_cancelled", value=1)
