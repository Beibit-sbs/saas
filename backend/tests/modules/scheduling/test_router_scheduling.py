from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.rbac import service as rbac_service
from app.modules.scheduling import service as scheduling_service
from app.modules.scheduling.dependencies import get_scheduling_db
from app.modules.scheduling.models import AttendanceStatus, DayOfWeek, LessonStatus, SectionStatus
from app.modules.scheduling.schemas import (
    ConflictReportSchema,
    CourseSectionReadSchema,
    DisciplineListResponseSchema,
    DisciplineReadSchema,
    InstructorScheduleItemSchema,
    LessonAttendanceListResponseSchema,
    LessonAttendanceReadSchema,
    LessonInstanceListResponseSchema,
    LessonInstanceReadSchema,
    LessonTopicListResponseSchema,
    LessonTopicReadSchema,
    RoomScheduleItemSchema,
    StudentTopicProgressListResponseSchema,
    StudentTopicProgressReadSchema,
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
def override_scheduling_db() -> Generator[MagicMock, None, None]:
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


def _lesson_schema() -> LessonInstanceReadSchema:
    now = datetime(2026, 4, 5, 8, 0, 0, tzinfo=UTC)
    return LessonInstanceReadSchema(
        id=9001,
        tenant_id=1,
        section_id=1101,
        scheduled_date=datetime(2026, 4, 5, tzinfo=UTC).date(),
        actual_date=None,
        topic_title="Linear equations",
        status=LessonStatus.PLANNED,
        notes=None,
        metadata_json={},
        created_by="owner@example.com",
        created_at=now,
        updated_at=now,
        version=1,
    )


def _discipline_schema() -> DisciplineReadSchema:
    now = datetime(2026, 4, 6, 8, 0, 0, tzinfo=UTC)
    return DisciplineReadSchema(
        id=301,
        tenant_id=1,
        unique_code="CS-101",
        title="Introduction to Programming",
        description="Core programming discipline",
        credits=5,
        prerequisites_json={},
        learning_outcomes_json=["variables", "loops"],
        is_active=True,
        created_at=now,
        updated_at=now,
        version=1,
    )


def _topic_schema() -> LessonTopicReadSchema:
    now = datetime(2026, 4, 6, 8, 5, 0, tzinfo=UTC)
    return LessonTopicReadSchema(
        id=401,
        tenant_id=1,
        discipline_id=301,
        module_num=1,
        topic_num=1,
        title="Variables and Data Types",
        description="Basics",
        difficulty_level="beginner",
        recommended_materials_json=["material-1"],
        created_at=now,
        updated_at=now,
        version=1,
    )


def _progress_schema() -> StudentTopicProgressReadSchema:
    now = datetime(2026, 4, 6, 9, 0, 0, tzinfo=UTC)
    return StudentTopicProgressReadSchema(
        id=501,
        tenant_id=1,
        student_profile_id=777,
        topic_id=401,
        discipline_id=301,
        first_seen_date=datetime(2026, 4, 1, tzinfo=UTC).date(),
        last_reviewed_date=datetime(2026, 4, 6, tzinfo=UTC).date(),
        status="in_progress",
        materials_opened=4,
        materials_completed=2,
        quiz_attempts=1,
        quiz_best_score=78.5,
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


def test_create_lesson_instance_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_lesson_instance(self, tenant_id: int, *, section_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert section_id == 1101
        assert actor_id == "owner@example.com"
        return _lesson_schema()

    monkeypatch.setattr(scheduling_service.SchedulingService, "create_lesson_instance", fake_create_lesson_instance)

    response = client.post(
        "/api/admin/scheduling/sections/1101/lessons",
        headers=admin_headers,
        json={
            "scheduled_date": "2026-04-05",
            "topic_title": "Linear equations",
            "notes": "chapter 1",
            "metadata_json": {},
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["id"] == 9001


def test_list_lesson_instances_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_lesson_instances(self, tenant_id: int, *, section_id: int, page: int, page_size: int, status):
        assert tenant_id == 1
        assert section_id == 1101
        assert page == 1
        assert page_size == 20
        return LessonInstanceListResponseSchema(total=1, page=1, page_size=20, items=[_lesson_schema()])

    monkeypatch.setattr(scheduling_service.SchedulingService, "list_lesson_instances", fake_list_lesson_instances)

    response = client.get("/api/admin/scheduling/sections/1101/lessons", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == 9001


def test_upsert_lesson_attendance_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_upsert_lesson_attendance(self, tenant_id: int, *, lesson_instance_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert lesson_instance_id == 9001
        assert request.student_profile_id == 501
        assert actor_id == "owner@example.com"
        now = datetime(2026, 4, 5, 8, 5, 0, tzinfo=UTC)
        return LessonAttendanceReadSchema(
            id=9101,
            tenant_id=1,
            lesson_instance_id=9001,
            student_profile_id=501,
            attendance_status=AttendanceStatus.PRESENT,
            marked_by="owner@example.com",
            marked_at=now,
            created_at=now,
            updated_at=now,
            version=1,
        )

    monkeypatch.setattr(scheduling_service.SchedulingService, "upsert_lesson_attendance", fake_upsert_lesson_attendance)

    response = client.put(
        "/api/admin/scheduling/lessons/9001/attendance",
        headers=admin_headers,
        json={"student_profile_id": 501, "attendance_status": "present"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["student_profile_id"] == 501


def test_list_lesson_attendance_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_lesson_attendance(self, tenant_id: int, *, lesson_instance_id: int):
        assert tenant_id == 1
        assert lesson_instance_id == 9001
        now = datetime(2026, 4, 5, 8, 5, 0, tzinfo=UTC)
        return LessonAttendanceListResponseSchema(
            total=1,
            items=[
                LessonAttendanceReadSchema(
                    id=9101,
                    tenant_id=1,
                    lesson_instance_id=9001,
                    student_profile_id=501,
                    attendance_status=AttendanceStatus.PRESENT,
                    marked_by="owner@example.com",
                    marked_at=now,
                    created_at=now,
                    updated_at=now,
                    version=1,
                )
            ],
        )

    monkeypatch.setattr(scheduling_service.SchedulingService, "list_lesson_attendance", fake_list_lesson_attendance)

    response = client.get("/api/admin/scheduling/lessons/9001/attendance", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["student_profile_id"] == 501


def test_create_discipline_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_discipline(self, tenant_id: int, *, request, actor_id: str):
        assert tenant_id == 1
        assert actor_id == "owner@example.com"
        assert request.unique_code == "CS-101"
        return _discipline_schema()

    monkeypatch.setattr(scheduling_service.SchedulingService, "create_discipline", fake_create_discipline)

    response = client.post(
        "/api/admin/scheduling/disciplines",
        headers=admin_headers,
        json={
            "unique_code": "CS-101",
            "title": "Introduction to Programming",
            "description": "Core programming discipline",
            "credits": 5,
            "prerequisites_json": {},
            "learning_outcomes_json": ["variables", "loops"],
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["id"] == 301


def test_list_disciplines_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_disciplines(self, tenant_id: int, *, include_inactive: bool):
        assert tenant_id == 1
        assert include_inactive is False
        return DisciplineListResponseSchema(total=1, items=[_discipline_schema()])

    monkeypatch.setattr(scheduling_service.SchedulingService, "list_disciplines", fake_list_disciplines)

    response = client.get("/api/admin/scheduling/disciplines", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["unique_code"] == "CS-101"


def test_create_lesson_topic_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_lesson_topic(self, tenant_id: int, *, discipline_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert discipline_id == 301
        assert actor_id == "owner@example.com"
        assert request.module_num == 1
        return _topic_schema()

    monkeypatch.setattr(scheduling_service.SchedulingService, "create_lesson_topic", fake_create_lesson_topic)

    response = client.post(
        "/api/admin/scheduling/disciplines/301/topics",
        headers=admin_headers,
        json={
            "module_num": 1,
            "topic_num": 1,
            "title": "Variables and Data Types",
            "description": "Basics",
            "difficulty_level": "beginner",
            "recommended_materials_json": ["material-1"],
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["id"] == 401


def test_list_lesson_topics_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_lesson_topics(self, tenant_id: int, *, discipline_id: int):
        assert tenant_id == 1
        assert discipline_id == 301
        return LessonTopicListResponseSchema(total=1, items=[_topic_schema()])

    monkeypatch.setattr(scheduling_service.SchedulingService, "list_lesson_topics", fake_list_lesson_topics)

    response = client.get("/api/admin/scheduling/disciplines/301/topics", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Variables and Data Types"


def test_upsert_student_topic_progress_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_upsert_student_topic_progress(self, tenant_id: int, *, topic_id: int, student_profile_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert topic_id == 401
        assert student_profile_id == 777
        assert actor_id == "owner@example.com"
        assert request.discipline_id == 301
        return _progress_schema()

    monkeypatch.setattr(
        scheduling_service.SchedulingService,
        "upsert_student_topic_progress",
        fake_upsert_student_topic_progress,
    )

    response = client.put(
        "/api/admin/scheduling/topics/401/progress/777",
        headers=admin_headers,
        json={
            "discipline_id": 301,
            "first_seen_date": "2026-04-01",
            "last_reviewed_date": "2026-04-06",
            "status": "in_progress",
            "materials_opened": 4,
            "materials_completed": 2,
            "quiz_attempts": 1,
            "quiz_best_score": 78.5,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["student_profile_id"] == 777


def test_list_student_topic_progress_success(
    monkeypatch: pytest.MonkeyPatch,
    override_scheduling_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_student_topic_progress(self, tenant_id: int, *, student_profile_id: int, discipline_id: int | None):
        assert tenant_id == 1
        assert student_profile_id == 777
        assert discipline_id == 301
        return StudentTopicProgressListResponseSchema(total=1, items=[_progress_schema()])

    monkeypatch.setattr(
        scheduling_service.SchedulingService,
        "list_student_topic_progress",
        fake_list_student_topic_progress,
    )

    response = client.get(
        "/api/admin/scheduling/students/777/topic-progress?discipline_id=301",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["topic_id"] == 401
