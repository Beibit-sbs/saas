"""
ERP-QA-84 – Scheduling router endpoint tests.

Covers 18 endpoints under /api/admin/scheduling:
  POST   /sections                                  (scheduling.write)
  POST   /sections/{id}/schedule                    (scheduling.write)
  POST   /sections/{id}/instructors                 (scheduling.write)
  PATCH  /sections/{id}/reschedule                  (scheduling.write)
  PATCH  /sections/{id}/cancel                      (scheduling.write)
  POST   /sections/{id}/lessons                     (scheduling.write)
  GET    /sections/{id}/lessons                     (scheduling.read)
  GET    /consistency                               (scheduling.read)
  PUT    /lessons/{id}/attendance                   (scheduling.write)
  GET    /lessons/{id}/attendance                   (scheduling.read)
  GET    /schedules/students/{id}                   (scheduling.read)
  GET    /schedules/instructors/{id}                (scheduling.read)
  GET    /schedules/rooms/{id}                      (scheduling.read)
  GET    /sections/{id}/conflicts                   (scheduling.read)
  POST   /disciplines                               (scheduling.write)
  GET    /disciplines                               (scheduling.read)
  POST   /disciplines/{id}/topics                   (scheduling.write)
  GET    /disciplines/{id}/topics                   (scheduling.read)
  PUT    /topics/{id}/progress/{sid}                (scheduling.write)
  GET    /students/{sid}/topic-progress             (scheduling.read)
"""

from __future__ import annotations

from datetime import date, datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.main import app
from app.modules.scheduling.dependencies import get_scheduling_db

BASE = "/api/admin/scheduling"

VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)


@pytest.fixture(autouse=True)
def _override_scheduling_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_scheduling_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_scheduling_db, None)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_SECTION_PAYLOAD = {
    "course_id": 1,
    "term_id": 1,
    "section_code": "SEC-01",
    "instructor_id": "instr1@example.com",
    "max_capacity": 30,
}

_SCHEDULE_PAYLOAD = {
    "time_slot_id": 1,
    "classroom_id": 1,
    "day_of_week": "monday",
}

_RESCHEDULE_PAYLOAD = {
    "time_slot_id": 2,
    "classroom_id": 2,
    "day_of_week": "tuesday",
    "expected_version": 1,
}

_CANCEL_PAYLOAD = {"expected_version": 1}

_INSTRUCTOR_ASSIGN_PAYLOAD = {
    "instructor_id": "instr2@example.com",
    "role": "primary",
}

_LESSON_PAYLOAD = {
    "scheduled_date": "2026-04-20",
    "topic_title": "Introduction",
    "notes": "First session",
    "metadata_json": {},
}

_ATTENDANCE_PAYLOAD = {
    "student_profile_id": 1,
    "attendance_status": "present",
}

_DISCIPLINE_PAYLOAD = {
    "unique_code": "DISC-01",
    "title": "Mathematics",
    "description": "Core math",
    "credits": 3,
    "prerequisites_json": {},
    "learning_outcomes_json": [],
}

_TOPIC_PAYLOAD = {
    "module_num": 1,
    "topic_num": 1,
    "title": "Algebra Basics",
    "description": "Intro to algebra",
    "difficulty_level": "beginner",
    "recommended_materials_json": [],
}

_PROGRESS_PAYLOAD = {
    "discipline_id": 1,
    "status": "in_progress",
    "materials_opened": 5,
    "materials_completed": 2,
    "quiz_attempts": 1,
    "quiz_best_score": 85.0,
}


_now = datetime(2026, 4, 20, 10, 0, 0, tzinfo=UTC)
_today = date(2026, 4, 20)


def _mock_section():
    s = MagicMock()
    s.id = 1
    s.tenant_id = 1
    s.course_id = 1
    s.term_id = 1
    s.section_code = "SEC-01"
    s.instructor_id = "instr1@example.com"
    s.max_capacity = 30
    s.status = "planned"
    s.version = 1
    s.created_by = "owner@example.com"
    s.updated_by = "owner@example.com"
    s.created_at = _now
    s.updated_at = _now
    s.metadata_json = {}
    return s


def _mock_schedule():
    s = MagicMock()
    s.id = 1
    s.tenant_id = 1
    s.section_id = 1
    s.time_slot_id = 1
    s.classroom_id = 1
    s.day_of_week = "monday"
    s.version = 1
    s.created_at = _now
    s.updated_at = _now
    return s


def _mock_lesson():
    m = MagicMock()
    m.id = 1
    m.tenant_id = 1
    m.section_id = 1
    m.scheduled_date = _today
    m.actual_date = None
    m.topic_title = "Introduction"
    m.status = "planned"
    m.notes = "First session"
    m.metadata_json = {}
    m.created_by = "owner@example.com"
    m.updated_by = "owner@example.com"
    m.created_at = _now
    m.updated_at = _now
    m.version = 1
    return m


def _mock_attendance():
    a = MagicMock()
    a.id = 1
    a.tenant_id = 1
    a.lesson_instance_id = 1
    a.student_profile_id = 1
    a.attendance_status = "present"
    a.marked_by = "owner@example.com"
    a.marked_at = _now
    a.created_at = _now
    a.updated_at = _now
    a.version = 1
    return a


def _mock_discipline():
    d = MagicMock()
    d.id = 1
    d.tenant_id = 1
    d.unique_code = "DISC-01"
    d.title = "Mathematics"
    d.description = "Core math"
    d.credits = 3
    d.prerequisites_json = {}
    d.learning_outcomes_json = []
    d.is_active = True
    d.created_by = "owner@example.com"
    d.updated_by = "owner@example.com"
    d.created_at = _now
    d.updated_at = _now
    d.version = 1
    return d


def _mock_topic():
    t = MagicMock()
    t.id = 1
    t.tenant_id = 1
    t.discipline_id = 1
    t.module_num = 1
    t.topic_num = 1
    t.title = "Algebra Basics"
    t.description = "Intro to algebra"
    t.difficulty_level = "beginner"
    t.recommended_materials_json = []
    t.created_at = _now
    t.updated_at = _now
    t.version = 1
    return t


def _mock_progress():
    p = MagicMock()
    p.id = 1
    p.tenant_id = 1
    p.student_profile_id = 1
    p.topic_id = 1
    p.discipline_id = 1
    p.first_seen_date = _today
    p.last_reviewed_date = _today
    p.status = "in_progress"
    p.materials_opened = 5
    p.materials_completed = 2
    p.quiz_attempts = 1
    p.quiz_best_score = 85.0
    p.version = 1
    p.created_at = _now
    p.updated_at = _now
    return p


SVC = "app.modules.scheduling.service.SchedulingService"


# ---------------------------------------------------------------------------
# POST /sections – create course section
# ---------------------------------------------------------------------------


class TestCreateSection:
    def test_create_section_happy(self):
        with patch(f"{SVC}.create_course_section", new_callable=AsyncMock, return_value=_mock_section()):
            r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_section_viewer_forbidden(self):
        r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403

    def test_create_section_no_auth(self):
        r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD)
        assert r.status_code in (401, 403)

    def test_create_section_invalid_payload(self):
        r = client.post(f"{BASE}/sections", json={"course_id": -1}, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_section_integrity_error(self):
        with patch(
            f"{SVC}.create_course_section",
            new_callable=AsyncMock,
            side_effect=IntegrityError("dup", {}, Exception()),
        ):
            r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code in (400, 409)

    def test_create_section_value_error(self):
        with patch(
            f"{SVC}.create_course_section",
            new_callable=AsyncMock,
            side_effect=ValueError("bad data"),
        ):
            r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /sections/{id}/schedule
# ---------------------------------------------------------------------------


class TestScheduleSection:
    def test_schedule_happy(self):
        with patch(f"{SVC}.schedule_section", new_callable=AsyncMock, return_value=_mock_schedule()):
            r = client.post(f"{BASE}/sections/1/schedule", json=_SCHEDULE_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_schedule_viewer_forbidden(self):
        r = client.post(f"{BASE}/sections/1/schedule", json=_SCHEDULE_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403

    def test_schedule_value_error(self):
        with patch(
            f"{SVC}.schedule_section",
            new_callable=AsyncMock,
            side_effect=ValueError("section already scheduled"),
        ):
            r = client.post(f"{BASE}/sections/1/schedule", json=_SCHEDULE_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /sections/{id}/instructors
# ---------------------------------------------------------------------------


class TestAssignInstructor:
    def test_assign_happy(self):
        result = MagicMock()
        with patch(f"{SVC}.assign_instructor", new_callable=AsyncMock, return_value=result):
            r = client.post(f"{BASE}/sections/1/instructors", json=_INSTRUCTOR_ASSIGN_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_assign_viewer_forbidden(self):
        r = client.post(f"{BASE}/sections/1/instructors", json=_INSTRUCTOR_ASSIGN_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /sections/{id}/reschedule
# ---------------------------------------------------------------------------


class TestRescheduleSection:
    def test_reschedule_happy(self):
        with patch(f"{SVC}.reschedule_section", new_callable=AsyncMock, return_value=_mock_schedule()):
            r = client.patch(f"{BASE}/sections/1/reschedule", json=_RESCHEDULE_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_reschedule_viewer_forbidden(self):
        r = client.patch(f"{BASE}/sections/1/reschedule", json=_RESCHEDULE_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /sections/{id}/cancel
# ---------------------------------------------------------------------------


class TestCancelSection:
    def test_cancel_happy(self):
        with patch(f"{SVC}.cancel_section", new_callable=AsyncMock, return_value=_mock_section()):
            r = client.patch(f"{BASE}/sections/1/cancel", json=_CANCEL_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_cancel_viewer_forbidden(self):
        r = client.patch(f"{BASE}/sections/1/cancel", json=_CANCEL_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /sections/{id}/lessons – create lesson instance
# ---------------------------------------------------------------------------


class TestCreateLesson:
    def test_create_lesson_happy(self):
        with patch(f"{SVC}.create_lesson_instance", new_callable=AsyncMock, return_value=_mock_lesson()):
            r = client.post(f"{BASE}/sections/1/lessons", json=_LESSON_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_lesson_viewer_forbidden(self):
        r = client.post(f"{BASE}/sections/1/lessons", json=_LESSON_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /sections/{id}/lessons – list lesson instances
# ---------------------------------------------------------------------------


class TestListLessons:
    def test_list_happy(self):
        ret = MagicMock()
        ret.total = 1
        ret.page = 1
        ret.page_size = 20
        ret.items = [_mock_lesson()]
        with patch(f"{SVC}.list_lesson_instances", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/sections/1/lessons", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_with_status_filter(self):
        ret = MagicMock()
        ret.total = 0
        ret.page = 1
        ret.page_size = 20
        ret.items = []
        with patch(f"{SVC}.list_lesson_instances", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/sections/1/lessons?status=completed", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}/sections/1/lessons", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /consistency
# ---------------------------------------------------------------------------


class TestConsistencyReport:
    def test_consistency_happy(self):
        report = MagicMock()
        report.issues = []
        report.summary = {}
        with patch(f"{SVC}.list_tenant_scheduling_consistency_report", new_callable=AsyncMock, return_value=report):
            r = client.get(f"{BASE}/consistency", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_consistency_viewer_forbidden(self):
        r = client.get(f"{BASE}/consistency", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PUT /lessons/{id}/attendance
# ---------------------------------------------------------------------------


class TestUpsertAttendance:
    def test_upsert_happy(self):
        with patch(f"{SVC}.upsert_lesson_attendance", new_callable=AsyncMock, return_value=_mock_attendance()):
            r = client.put(f"{BASE}/lessons/1/attendance", json=_ATTENDANCE_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_upsert_viewer_forbidden(self):
        r = client.put(f"{BASE}/lessons/1/attendance", json=_ATTENDANCE_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /lessons/{id}/attendance
# ---------------------------------------------------------------------------


class TestListAttendance:
    def test_list_happy(self):
        ret = MagicMock()
        ret.total = 1
        ret.items = [_mock_attendance()]
        with patch(f"{SVC}.list_lesson_attendance", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/lessons/1/attendance", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}/lessons/1/attendance", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /schedules/students/{id}
# ---------------------------------------------------------------------------


class TestStudentSchedule:
    def test_happy(self):
        with patch(f"{SVC}.get_student_schedule", new_callable=AsyncMock, return_value=[]):
            r = client.get(f"{BASE}/schedules/students/1", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_viewer_forbidden(self):
        r = client.get(f"{BASE}/schedules/students/1", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /schedules/instructors/{id}
# ---------------------------------------------------------------------------


class TestInstructorSchedule:
    def test_happy(self):
        with patch(f"{SVC}.get_instructor_schedule", new_callable=AsyncMock, return_value=[]):
            r = client.get(f"{BASE}/schedules/instructors/instr1", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_viewer_forbidden(self):
        r = client.get(f"{BASE}/schedules/instructors/instr1", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /schedules/rooms/{id}
# ---------------------------------------------------------------------------


class TestRoomSchedule:
    def test_happy(self):
        with patch(f"{SVC}.get_room_schedule", new_callable=AsyncMock, return_value=[]):
            r = client.get(f"{BASE}/schedules/rooms/1", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_viewer_forbidden(self):
        r = client.get(f"{BASE}/schedules/rooms/1", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /sections/{id}/conflicts
# ---------------------------------------------------------------------------


class TestDetectConflicts:
    def test_happy_no_conflicts(self):
        report = MagicMock()
        report.has_room_conflict = False
        report.instructor_conflicts = []
        with patch(f"{SVC}.detect_schedule_conflicts", new_callable=AsyncMock, return_value=report):
            r = client.get(
                f"{BASE}/sections/1/conflicts?time_slot_id=1&classroom_id=1&day_of_week=monday",
                headers=ADMIN_HEADERS,
            )
        assert r.status_code == 200

    def test_conflicts_detected_emits_metric(self):
        report = MagicMock()
        report.has_room_conflict = True
        report.instructor_conflicts = []
        with patch(f"{SVC}.detect_schedule_conflicts", new_callable=AsyncMock, return_value=report), \
             patch("app.modules.scheduling.router.observe_scheduling_conflict") as mock_metric:
            r = client.get(
                f"{BASE}/sections/1/conflicts?time_slot_id=1&classroom_id=1&day_of_week=monday",
                headers=ADMIN_HEADERS,
            )
        assert r.status_code == 200
        mock_metric.assert_called_once()

    def test_missing_required_params(self):
        r = client.get(f"{BASE}/sections/1/conflicts", headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_viewer_forbidden(self):
        r = client.get(
            f"{BASE}/sections/1/conflicts?time_slot_id=1&classroom_id=1&day_of_week=monday",
            headers=VIEWER_HEADERS,
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /disciplines
# ---------------------------------------------------------------------------


class TestCreateDiscipline:
    def test_create_happy(self):
        with patch(f"{SVC}.create_discipline", new_callable=AsyncMock, return_value=_mock_discipline()):
            r = client.post(f"{BASE}/disciplines", json=_DISCIPLINE_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_viewer_forbidden(self):
        r = client.post(f"{BASE}/disciplines", json=_DISCIPLINE_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403

    def test_create_invalid_empty_code(self):
        payload = {**_DISCIPLINE_PAYLOAD, "unique_code": ""}
        r = client.post(f"{BASE}/disciplines", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_integrity_error(self):
        with patch(
            f"{SVC}.create_discipline",
            new_callable=AsyncMock,
            side_effect=IntegrityError("dup", {}, Exception()),
        ):
            r = client.post(f"{BASE}/disciplines", json=_DISCIPLINE_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code in (400, 409)


# ---------------------------------------------------------------------------
# GET /disciplines
# ---------------------------------------------------------------------------


class TestListDisciplines:
    def test_list_happy(self):
        ret = MagicMock()
        ret.total = 1
        ret.items = [_mock_discipline()]
        with patch(f"{SVC}.list_disciplines", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/disciplines", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_with_inactive(self):
        ret = MagicMock()
        ret.total = 0
        ret.items = []
        with patch(f"{SVC}.list_disciplines", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/disciplines?include_inactive=true", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}/disciplines", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /disciplines/{id}/topics
# ---------------------------------------------------------------------------


class TestCreateTopic:
    def test_create_happy(self):
        with patch(f"{SVC}.create_lesson_topic", new_callable=AsyncMock, return_value=_mock_topic()):
            r = client.post(f"{BASE}/disciplines/1/topics", json=_TOPIC_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_viewer_forbidden(self):
        r = client.post(f"{BASE}/disciplines/1/topics", json=_TOPIC_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /disciplines/{id}/topics
# ---------------------------------------------------------------------------


class TestListTopics:
    def test_list_happy(self):
        ret = MagicMock()
        ret.total = 1
        ret.items = [_mock_topic()]
        with patch(f"{SVC}.list_lesson_topics", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/disciplines/1/topics", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}/disciplines/1/topics", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PUT /topics/{id}/progress/{sid}
# ---------------------------------------------------------------------------


class TestUpsertTopicProgress:
    def test_upsert_happy(self):
        with patch(f"{SVC}.upsert_student_topic_progress", new_callable=AsyncMock, return_value=_mock_progress()):
            r = client.put(f"{BASE}/topics/1/progress/1", json=_PROGRESS_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_upsert_viewer_forbidden(self):
        r = client.put(f"{BASE}/topics/1/progress/1", json=_PROGRESS_PAYLOAD, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /students/{sid}/topic-progress
# ---------------------------------------------------------------------------


class TestListTopicProgress:
    def test_list_happy(self):
        ret = MagicMock()
        ret.total = 0
        ret.items = []
        with patch(f"{SVC}.list_student_topic_progress", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/students/1/topic-progress", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_with_discipline_filter(self):
        ret = MagicMock()
        ret.total = 0
        ret.items = []
        with patch(f"{SVC}.list_student_topic_progress", new_callable=AsyncMock, return_value=ret):
            r = client.get(f"{BASE}/students/1/topic-progress?discipline_id=1", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}/students/1/topic-progress", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# _raise_scheduling_http_error edge cases
# ---------------------------------------------------------------------------


class TestRaiseSchedulingHttpError:
    def test_permission_error(self):
        with patch(
            f"{SVC}.create_course_section",
            new_callable=AsyncMock,
            side_effect=PermissionError("forbidden"),
        ):
            r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_generic_exception_becomes_400(self):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        with patch(
            f"{SVC}.create_course_section",
            new_callable=AsyncMock,
            side_effect=TenantResourceNotFoundError("not found"),
        ):
            r = client.post(f"{BASE}/sections", json=_SECTION_PAYLOAD, headers=ADMIN_HEADERS)
        assert r.status_code == 404
