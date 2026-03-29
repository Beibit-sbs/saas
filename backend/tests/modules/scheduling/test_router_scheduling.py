from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.rbac import service as rbac_service
from app.modules.scheduling import service as scheduling_service
from app.modules.scheduling.dependencies import get_scheduling_db
from app.modules.scheduling.models import DayOfWeek, SectionStatus
from app.modules.scheduling.schemas import (
    ConflictReportSchema,
    CourseSectionReadSchema,
    InstructorScheduleItemSchema,
    RoomScheduleItemSchema,
    StudentScheduleItemSchema,
)
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client


@pytest.fixture(autouse=True)
def _enable_scheduling_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"scheduling.read", "scheduling.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.scheduling@example.com": [],
        },
    )


@pytest.fixture
def override_scheduling_db() -> MagicMock:
    session = MagicMock()
    app.dependency_overrides[get_scheduling_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_scheduling_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.scheduling@example.com", [])


def _section_schema() -> CourseSectionReadSchema:
    now = datetime(2026, 3, 24, 16, 0, 0, tzinfo=UTC)
    return CourseSectionReadSchema(
        id=1101,
        tenant_id=1,
        course_id=701,
        term_id=1,
        section_code="A-01",
        instructor_id="inst@example.com",
        max_capacity=30,
        status=SectionStatus.PLANNED,
        created_at=now,
        updated_at=now,
        version=1,
    )


def test_create_section_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_course_section(self, tenant_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert actor_id == "owner@example.com"
        return _section_schema()

    monkeypatch.setattr(scheduling_service.SchedulingService, "create_course_section", fake_create_course_section)

    response = client.post(
        "/api/admin/scheduling/sections",
        headers=admin_headers,
        json={
            "course_id": 701,
            "term_id": 1,
            "section_code": "A-01",
            "instructor_id": "inst@example.com",
            "max_capacity": 30,
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["id"] == 1101


def test_create_section_requires_permission(student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/admin/scheduling/sections",
        headers=student_headers,
        json={
            "course_id": 701,
            "term_id": 1,
            "section_code": "A-01",
            "max_capacity": 30,
        },
    )
    assert response.status_code == 403, response.text


def test_detect_conflicts_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_detect_schedule_conflicts(
        self,
        tenant_id: int,
        *,
        section_id: int,
        time_slot_id: int,
        classroom_id: int,
        day_of_week: DayOfWeek,
    ):
        assert tenant_id == 1
        assert section_id == 1101
        assert day_of_week == DayOfWeek.MONDAY
        return ConflictReportSchema(
            has_room_conflict=True,
            room_conflict_section_id=2209,
            instructor_conflicts=[{"section_id": 2209}],
        )

    monkeypatch.setattr(scheduling_service.SchedulingService, "detect_schedule_conflicts", fake_detect_schedule_conflicts)

    response = client.get(
        "/api/admin/scheduling/sections/1101/conflicts?time_slot_id=301&classroom_id=401&day_of_week=monday",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["has_room_conflict"] is True
    assert payload["room_conflict_section_id"] == 2209


def test_get_student_schedule_requires_read_permission(
    override_scheduling_db: MagicMock,
    student_headers: dict[str, str],
) -> None:
    response = client.get("/api/admin/scheduling/schedules/students/501", headers=student_headers)
    assert response.status_code == 403, response.text


def test_get_student_schedule_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_student_schedule(self, tenant_id: int, *, student_id: int):
        assert tenant_id == 1
        assert student_id == 501
        return [
            StudentScheduleItemSchema(
                student_profile_id=501,
                section_id=1101,
                course_id=701,
                term_id=1,
                day_of_week=DayOfWeek.MONDAY,
                start_time="09:00:00",
                end_time="10:00:00",
                classroom_id=401,
                classroom_name="Room 101",
            )
        ]

    monkeypatch.setattr(scheduling_service.SchedulingService, "get_student_schedule", fake_get_student_schedule)

    response = client.get("/api/admin/scheduling/schedules/students/501", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()[0]["student_profile_id"] == 501


def test_get_instructor_schedule_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_instructor_schedule(self, tenant_id: int, *, instructor_id: str):
        assert tenant_id == 1
        assert instructor_id == "inst@example.com"
        return [
            InstructorScheduleItemSchema(
                instructor_id="inst@example.com",
                section_id=1101,
                course_id=701,
                term_id=1,
                day_of_week=DayOfWeek.TUESDAY,
                start_time="11:00:00",
                end_time="12:15:00",
                classroom_id=402,
                classroom_name="Lab 2",
            )
        ]

    monkeypatch.setattr(
        scheduling_service.SchedulingService,
        "get_instructor_schedule",
        fake_get_instructor_schedule,
    )

    response = client.get(
        "/api/admin/scheduling/schedules/instructors/inst@example.com",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()[0]["instructor_id"] == "inst@example.com"


def test_get_room_schedule_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_room_schedule(self, tenant_id: int, *, classroom_id: int):
        assert tenant_id == 1
        assert classroom_id == 401
        return [
            RoomScheduleItemSchema(
                classroom_id=401,
                section_id=1101,
                course_id=701,
                term_id=1,
                day_of_week=DayOfWeek.WEDNESDAY,
                start_time="13:00:00",
                end_time="14:00:00",
                instructor_id="inst@example.com",
            )
        ]

    monkeypatch.setattr(scheduling_service.SchedulingService, "get_room_schedule", fake_get_room_schedule)

    response = client.get("/api/admin/scheduling/schedules/rooms/401", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()[0]["classroom_id"] == 401
