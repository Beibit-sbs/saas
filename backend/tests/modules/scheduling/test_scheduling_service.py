from __future__ import annotations

import asyncio
from datetime import UTC, datetime, time
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.modules.scheduling.models import (
    ClassroomModel,
    CourseSectionModel,
    DayOfWeek,
    SectionScheduleModel,
    SectionStatus,
    TimeSlotModel,
)
from app.modules.scheduling.schemas import (
    CourseSectionCreateSchema,
    SectionRescheduleSchema,
    SectionScheduleCreateSchema,
)
from app.modules.scheduling.service import SchedulingService


class ExecuteResult:
    def __init__(
        self,
        *,
        scalar_one_or_none: object | None = None,
        rows: list[object] | None = None,
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._rows = rows or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def all(self) -> list[object]:
        return list(self._rows)


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC)
        if getattr(instance, "id", None) is None:
            defaults = {
                "CourseSectionModel": 1101,
                "SectionScheduleModel": 2201,
            }
            instance.id = defaults.get(instance.__class__.__name__, 1)
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if hasattr(instance, "updated_at") and getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.scheduling.service.log_admin_action", mock)
    return mock


def test_create_course_section_success(run_async, db_session, audit_mock) -> None:
    service = SchedulingService(db_session)
    request = CourseSectionCreateSchema(
        course_id=701,
        term_id=1,
        section_code="A-01",
        instructor_id="inst@example.com",
        max_capacity=30,
    )

    course = MagicMock(id=701, tenant_id=1)
    term = MagicMock(id=1, tenant_id=1)
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=course),
        ExecuteResult(scalar_one_or_none=term),
    ]

    result = run_async(service.create_course_section(tenant_id=1, request=request, actor_id="owner@example.com"))

    assert result.course_id == 701
    assert result.term_id == 1
    assert result.section_code == "A-01"
    assert result.status == SectionStatus.PLANNED
    db_session.commit.assert_called_once()
    audit_mock.assert_called_once()


def test_schedule_section_room_conflict_raises(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    section = CourseSectionModel(
        id=1101,
        tenant_id=1,
        course_id=701,
        term_id=1,
        section_code="A-01",
        instructor_id="inst@example.com",
        max_capacity=30,
        status=SectionStatus.PLANNED,
        version=1,
        created_at=datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC),
    )
    slot = TimeSlotModel(
        id=301,
        tenant_id=1,
        day_of_week=DayOfWeek.MONDAY,
        start_time=time(9, 0),
        end_time=time(10, 0),
        is_active=True,
    )
    room = ClassroomModel(
        id=401,
        tenant_id=1,
        name="Room 101",
        building="A",
        capacity=40,
        room_type="lecture",
        is_active=True,
        version=1,
    )
    conflict = SectionScheduleModel(
        id=999,
        tenant_id=1,
        section_id=2209,
        time_slot_id=301,
        classroom_id=401,
        day_of_week=DayOfWeek.MONDAY,
        version=1,
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=section),
        ExecuteResult(scalar_one_or_none=slot),
        ExecuteResult(scalar_one_or_none=room),
        ExecuteResult(scalar_one_or_none=conflict),
    ]

    request = SectionScheduleCreateSchema(
        time_slot_id=301,
        classroom_id=401,
        day_of_week=DayOfWeek.MONDAY,
    )

    with pytest.raises(DomainValidationError):
        run_async(service.schedule_section(tenant_id=1, section_id=1101, request=request, actor_id="owner@example.com"))


def test_reschedule_section_optimistic_lock_conflict(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    section = CourseSectionModel(
        id=1101,
        tenant_id=1,
        course_id=701,
        term_id=1,
        section_code="A-01",
        instructor_id="inst@example.com",
        max_capacity=30,
        status=SectionStatus.SCHEDULED,
        version=2,
        created_at=datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC),
    )
    schedule = SectionScheduleModel(
        id=2201,
        tenant_id=1,
        section_id=1101,
        time_slot_id=301,
        classroom_id=401,
        day_of_week=DayOfWeek.MONDAY,
        version=5,
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=section),
        ExecuteResult(scalar_one_or_none=schedule),
    ]

    request = SectionRescheduleSchema(
        time_slot_id=302,
        classroom_id=402,
        day_of_week=DayOfWeek.TUESDAY,
        expected_version=1,
    )

    with pytest.raises(OptimisticLockConflictError):
        run_async(service.reschedule_section(tenant_id=1, section_id=1101, request=request, actor_id="owner@example.com"))


def test_detect_schedule_conflicts_reports_room_and_instructor(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    section = CourseSectionModel(
        id=1101,
        tenant_id=1,
        course_id=701,
        term_id=1,
        section_code="A-01",
        instructor_id="inst@example.com",
        max_capacity=30,
        status=SectionStatus.SCHEDULED,
        version=1,
        created_at=datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 3, 24, 15, 0, 0, tzinfo=UTC),
    )
    slot = TimeSlotModel(
        id=301,
        tenant_id=1,
        day_of_week=DayOfWeek.MONDAY,
        start_time=time(9, 0),
        end_time=time(10, 0),
        is_active=True,
    )
    room_conflict = SectionScheduleModel(
        id=2202,
        tenant_id=1,
        section_id=2209,
        time_slot_id=301,
        classroom_id=401,
        day_of_week=DayOfWeek.MONDAY,
        version=1,
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=section),
        ExecuteResult(scalar_one_or_none=slot),
        ExecuteResult(scalar_one_or_none=room_conflict),
        ExecuteResult(rows=[("inst@example.com",)]),
        ExecuteResult(rows=[(2209, DayOfWeek.MONDAY, time(9, 30), time(10, 30))]),
    ]

    result = run_async(
        service.detect_schedule_conflicts(
            tenant_id=1,
            section_id=1101,
            time_slot_id=301,
            classroom_id=401,
            day_of_week=DayOfWeek.MONDAY,
        )
    )

    assert result.has_room_conflict is True
    assert result.room_conflict_section_id == 2209
    assert len(result.instructor_conflicts) == 1
    assert result.instructor_conflicts[0]["section_id"] == 2209


def test_get_student_schedule_returns_tenant_scoped_rows(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    student = MagicMock(id=501, tenant_id=1)
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=student),
        ExecuteResult(
            rows=[
                (1101, 701, 1, DayOfWeek.MONDAY, time(9, 0), time(10, 0), 401, "Room 101"),
            ]
        ),
    ]

    result = run_async(service.get_student_schedule(tenant_id=1, student_id=501))

    assert len(result) == 1
    assert result[0].student_profile_id == 501
    assert result[0].section_id == 1101
    assert result[0].classroom_name == "Room 101"
    assert result[0].start_time == "09:00:00"


def test_get_instructor_schedule_returns_rows(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    db_session.execute.return_value = ExecuteResult(
        rows=[
            (1101, 701, 1, DayOfWeek.TUESDAY, time(11, 0), time(12, 15), 402, "Lab 2"),
        ]
    )

    result = run_async(service.get_instructor_schedule(tenant_id=1, instructor_id="inst@example.com"))

    assert len(result) == 1
    assert result[0].instructor_id == "inst@example.com"
    assert result[0].classroom_id == 402
    assert result[0].end_time == "12:15:00"


def test_get_room_schedule_returns_rows(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    classroom = ClassroomModel(
        id=401,
        tenant_id=1,
        name="Room 101",
        building="A",
        capacity=40,
        room_type="lecture",
        is_active=True,
        version=1,
    )
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=classroom),
        ExecuteResult(
            rows=[
                (401, 1101, 701, 1, DayOfWeek.WEDNESDAY, time(13, 0), time(14, 0), "inst@example.com"),
            ]
        ),
    ]

    result = run_async(service.get_room_schedule(tenant_id=1, classroom_id=401))

    assert len(result) == 1
    assert result[0].classroom_id == 401
    assert result[0].section_id == 1101
    assert result[0].instructor_id == "inst@example.com"


def test_get_room_schedule_rejects_cross_tenant_classroom(run_async, db_session) -> None:
    service = SchedulingService(db_session)

    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

    with pytest.raises(TenantResourceNotFoundError):
        run_async(service.get_room_schedule(tenant_id=1, classroom_id=999))
