"""Tests for Phase XXXVIII — LMS Content Module."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.lms_content.service import (
    CONTENT_TYPES,
    FALLING_BEHIND_THRESHOLD,
    SUBMISSION_STATES,
    add_lesson,
    check_falling_behind,
    complete_lesson,
    create_course,
    get_course_progress,
    grade_submission,
    list_submissions,
    return_submission,
    submit_assignment,
)

TENANT = 1

# ─── helpers ──────────────────────────────────────────────────────────────────

def _sub(id_="sub1", assignment_id="a1", student_id="st1", status="SUBMITTED"):
    return {"id": id_, "assignment_id": assignment_id, "student_id": student_id, "status": status}


def _lesson(id_="l1", course_id="c1"):
    return {"id": id_, "course_id": course_id, "title": "Lesson 1", "content_type": "VIDEO"}


def _progress(lesson_id="l1", student_id="st1", status="COMPLETED"):
    return {"lesson_id": lesson_id, "student_id": student_id, "status": status}


# ─── constants ────────────────────────────────────────────────────────────────

def test_submission_states():
    assert SUBMISSION_STATES == {"DRAFT", "SUBMITTED", "GRADED", "RETURNED"}


def test_content_types_exist():
    assert "VIDEO" in CONTENT_TYPES
    assert "TEXT" in CONTENT_TYPES
    assert "ASSIGNMENT" in CONTENT_TYPES


def test_falling_behind_threshold():
    assert FALLING_BEHIND_THRESHOLD == 0.50


# ─── create_course ────────────────────────────────────────────────────────────

def test_create_course_success():
    with patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "c1"}):
        result = create_course(TENANT, title="Python 101", instructor_id="prof1")
    assert result["course_id"] == "c1"
    assert result["title"] == "Python 101"


def test_create_course_missing_title():
    with pytest.raises(ValueError, match="title"):
        create_course(TENANT, title="", instructor_id="prof1")


def test_create_course_invalid_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        create_course(0, title="Math", instructor_id="prof1")


# ─── add_lesson ───────────────────────────────────────────────────────────────

def test_add_lesson_success():
    with patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "l1"}):
        result = add_lesson(TENANT, course_id="c1", title="Intro", content_type="VIDEO")
    assert result["lesson_id"] == "l1"
    assert result["content_type"] == "VIDEO"


def test_add_lesson_invalid_content_type():
    with pytest.raises(ValueError, match="Invalid content_type"):
        add_lesson(TENANT, course_id="c1", title="Intro", content_type="PODCAST")


def test_add_lesson_missing_course_id():
    with pytest.raises(ValueError, match="course_id"):
        add_lesson(TENANT, course_id="", title="Intro", content_type="TEXT")


# ─── complete_lesson ──────────────────────────────────────────────────────────

def test_complete_lesson_fires_event():
    with (
        patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "p1"}),
        patch("app.modules.lms_content.service.EventPublisher") as mock_pub,
    ):
        result = complete_lesson(TENANT, lesson_id="l1", student_id="st1")
    assert result["status"] == "COMPLETED"
    assert result["progress_id"] == "p1"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "lms.lesson.completed"


def test_complete_lesson_missing_student():
    with pytest.raises(ValueError, match="student_id"):
        complete_lesson(TENANT, lesson_id="l1", student_id="")


# ─── submit_assignment ────────────────────────────────────────────────────────

def test_submit_assignment_fires_event():
    with (
        patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "sub1"}),
        patch("app.modules.lms_content.service.EventPublisher") as mock_pub,
    ):
        result = submit_assignment(TENANT, assignment_id="a1", student_id="st1", content="My answer")
    assert result["status"] == "SUBMITTED"
    assert result["submission_id"] == "sub1"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "lms.assignment.submitted"


def test_submit_assignment_missing_content():
    with pytest.raises(ValueError, match="content"):
        submit_assignment(TENANT, assignment_id="a1", student_id="st1", content="")


def test_submit_assignment_missing_assignment_id():
    with pytest.raises(ValueError, match="assignment_id"):
        submit_assignment(TENANT, assignment_id="", student_id="st1", content="answer")


# ─── grade_submission ─────────────────────────────────────────────────────────

def test_grade_submission_success():
    sub = _sub(status="SUBMITTED")
    with (
        patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=[sub]),
        patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "g1"}),
        patch("app.modules.lms_content.service.EventPublisher") as mock_pub,
    ):
        result = grade_submission(TENANT, submission_id="sub1", grade=85.0, feedback="Good job")
    assert result["grade"] == 85.0
    assert result["status"] == "GRADED"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "lms.grade.posted"


def test_grade_submission_invalid_grade_over_100():
    with pytest.raises(ValueError, match="grade must be between"):
        grade_submission(TENANT, submission_id="sub1", grade=150.0)


def test_grade_submission_invalid_grade_negative():
    with pytest.raises(ValueError, match="grade must be between"):
        grade_submission(TENANT, submission_id="sub1", grade=-5.0)


def test_grade_submission_wrong_status():
    sub = _sub(status="GRADED")
    with patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=[sub]):
        with pytest.raises(ValueError, match="only SUBMITTED"):
            grade_submission(TENANT, submission_id="sub1", grade=90.0)


def test_grade_submission_not_found():
    with patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=[]):
        with pytest.raises(LookupError):
            grade_submission(TENANT, submission_id="nonexistent", grade=80.0)


# ─── return_submission ────────────────────────────────────────────────────────

def test_return_submission_success():
    sub = _sub(status="GRADED")
    with (
        patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=[sub]),
        patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "ret1"}),
    ):
        result = return_submission(TENANT, submission_id="sub1", feedback="Please revise section 2")
    assert result["status"] == "RETURNED"
    assert result["returned_id"] == "ret1"


def test_return_submission_wrong_status():
    sub = _sub(status="SUBMITTED")
    with patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=[sub]):
        with pytest.raises(ValueError, match="only GRADED"):
            return_submission(TENANT, submission_id="sub1", feedback="Feedback")


def test_return_submission_missing_feedback():
    with pytest.raises(ValueError, match="feedback"):
        return_submission(TENANT, submission_id="sub1", feedback="")


# ─── get_course_progress ──────────────────────────────────────────────────────

def test_get_course_progress_all_completed():
    lessons = [_lesson(id_=f"l{i}") for i in range(4)]
    progress = [_progress(lesson_id=f"l{i}") for i in range(4)]

    def mock_list(entity_type, tenant_id):
        if entity_type == "lms_lessons":
            return lessons
        return progress

    with patch("app.modules.lms_content.service.list_entities_for_tenant", side_effect=mock_list):
        result = get_course_progress(TENANT, course_id="c1", student_id="st1")
    assert result["completion_pct"] == 1.0
    assert result["falling_behind"] is False


def test_get_course_progress_falling_behind():
    lessons = [_lesson(id_=f"l{i}") for i in range(4)]
    # Only 1 of 4 completed → 25% < 50%
    progress = [_progress(lesson_id="l0")]

    def mock_list(entity_type, tenant_id):
        if entity_type == "lms_lessons":
            return lessons
        return progress

    with patch("app.modules.lms_content.service.list_entities_for_tenant", side_effect=mock_list):
        result = get_course_progress(TENANT, course_id="c1", student_id="st1")
    assert result["falling_behind"] is True
    assert result["completion_pct"] == 0.25


def test_get_course_progress_no_lessons():
    def mock_list(entity_type, tenant_id):
        return []

    with patch("app.modules.lms_content.service.list_entities_for_tenant", side_effect=mock_list):
        result = get_course_progress(TENANT, course_id="c1", student_id="st1")
    assert result["total_lessons"] == 0
    assert result["completion_pct"] == 1.0
    assert result["falling_behind"] is False


# ─── check_falling_behind ─────────────────────────────────────────────────────

def test_check_falling_behind_fires_event():
    lessons = [_lesson(id_=f"l{i}") for i in range(4)]
    progress = [_progress(lesson_id="l0")]  # 25% < 50%

    def mock_list(entity_type, tenant_id):
        if entity_type == "lms_lessons":
            return lessons
        return progress

    with (
        patch("app.modules.lms_content.service.list_entities_for_tenant", side_effect=mock_list),
        patch("app.modules.lms_content.service.create_entity_for_tenant", return_value={"id": "risk1"}),
        patch("app.modules.lms_content.service.EventPublisher") as mock_pub,
    ):
        result = check_falling_behind(TENANT, course_id="c1", student_id="st1")
    assert result["event_fired"] is True
    assert result["risk_record_id"] == "risk1"
    call_kwargs = mock_pub.return_value.publish_event.call_args[1]
    assert call_kwargs["event_type"] == "lms.student.falling_behind"


def test_check_falling_behind_no_event_when_ok():
    lessons = [_lesson(id_=f"l{i}") for i in range(4)]
    progress = [_progress(lesson_id=f"l{i}") for i in range(4)]  # 100%

    def mock_list(entity_type, tenant_id):
        if entity_type == "lms_lessons":
            return lessons
        return progress

    with (
        patch("app.modules.lms_content.service.list_entities_for_tenant", side_effect=mock_list),
        patch("app.modules.lms_content.service.EventPublisher") as mock_pub,
    ):
        result = check_falling_behind(TENANT, course_id="c1", student_id="st1")
    assert result["event_fired"] is False
    mock_pub.return_value.publish_event.assert_not_called()


# ─── list_submissions ─────────────────────────────────────────────────────────

def test_list_submissions_unfiltered():
    subs = [_sub(id_="s1"), _sub(id_="s2", assignment_id="a2")]
    with patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=subs):
        result = list_submissions(TENANT)
    assert len(result) == 2


def test_list_submissions_by_assignment():
    subs = [_sub(id_="s1", assignment_id="a1"), _sub(id_="s2", assignment_id="a2")]
    with patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=subs):
        result = list_submissions(TENANT, assignment_id="a1")
    assert len(result) == 1
    assert result[0]["id"] == "s1"


def test_list_submissions_by_student():
    subs = [_sub(id_="s1", student_id="st1"), _sub(id_="s2", student_id="st2")]
    with patch("app.modules.lms_content.service.list_entities_for_tenant", return_value=subs):
        result = list_submissions(TENANT, student_id="st2")
    assert len(result) == 1
    assert result[0]["id"] == "s2"
