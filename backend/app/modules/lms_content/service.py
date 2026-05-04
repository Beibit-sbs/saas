"""LMS Content module service — XXXVIII.

Состояния сдачи задания (Submission FSM):
  DRAFT → SUBMITTED → GRADED → RETURNED

Состояния урока:
  NOT_STARTED → IN_PROGRESS → COMPLETED

Операции:
  create_course(tenant_id, *, title, instructor_id)
  add_lesson(tenant_id, *, course_id, title, content_type)
  complete_lesson(tenant_id, *, lesson_id, student_id)
  submit_assignment(tenant_id, *, assignment_id, student_id, content)
  grade_submission(tenant_id, *, submission_id, grade, feedback="")
  return_submission(tenant_id, *, submission_id, feedback)
  get_course_progress(tenant_id, *, course_id, student_id)
  check_falling_behind(tenant_id, *, course_id, student_id)
  list_submissions(tenant_id, *, assignment_id=None, student_id=None)

Константы:
  FALLING_BEHIND_THRESHOLD = 0.50  (50% completion)

События:
  lms.lesson.completed
  lms.assignment.submitted
  lms.grade.posted
  lms.student.falling_behind
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

SUBMISSION_STATES = frozenset({"DRAFT", "SUBMITTED", "GRADED", "RETURNED"})
LESSON_STATES = frozenset({"NOT_STARTED", "IN_PROGRESS", "COMPLETED"})
CONTENT_TYPES = frozenset({"VIDEO", "TEXT", "QUIZ", "ASSIGNMENT", "DOCUMENT"})
FALLING_BEHIND_THRESHOLD: float = 0.50

_SUBMISSION_FSM: dict[str, str] = {
    "DRAFT": "SUBMITTED",
    "SUBMITTED": "GRADED",
    "GRADED": "RETURNED",
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        EventPublisher().publish_event(
            tenant_id=int(tenant_id),
            event_type=event_type,
            aggregate_type="lms_content",
            aggregate_id=str(
                payload.get("submission_id")
                or payload.get("progress_id")
                or payload.get("risk_record_id")
                or payload.get("grade_record_id")
                or ""
            ),
            payload_json=payload,
        )
    except Exception:
        pass


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _audit(tenant_id: int, actor: str, action: str, path: str, metadata: dict) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=path,
            client_ip="service",
            entity="lms_content",
            metadata=metadata,
            tenant_id=tenant_id,
        )
    except Exception:
        pass


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        pass


def _record_outcome(record_id: str, outcome_type: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            record_id,
            payload={
                "outcome_type": outcome_type,
                "source_module": "lms_content",
                "record_id": record_id,
            },
            actor=actor,
        )
    except Exception:
        pass


# ─── create_course ────────────────────────────────────────────────────────────

def create_course(
    tenant_id: int,
    *,
    title: str,
    instructor_id: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not title:
        raise ValueError("title is required")
    if not instructor_id:
        raise ValueError("instructor_id is required")

    course = create_entity_for_tenant(
        "lms_courses",
        tenant_id=tenant_id,
        data={
            "title": title,
            "instructor_id": instructor_id,
            "created_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )
    return {"course_id": course.get("id"), "title": title, "instructor_id": instructor_id}


# ─── add_lesson ───────────────────────────────────────────────────────────────

def add_lesson(
    tenant_id: int,
    *,
    course_id: str,
    title: str,
    content_type: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not course_id:
        raise ValueError("course_id is required")
    if not title:
        raise ValueError("title is required")
    if content_type not in CONTENT_TYPES:
        raise ValueError(f"Invalid content_type '{content_type}'. Must be one of: {sorted(CONTENT_TYPES)}")

    lesson = create_entity_for_tenant(
        "lms_lessons",
        tenant_id=tenant_id,
        data={
            "course_id": course_id,
            "title": title,
            "content_type": content_type,
            "created_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
    )
    return {"lesson_id": lesson.get("id"), "course_id": course_id, "title": title, "content_type": content_type}


# ─── complete_lesson ──────────────────────────────────────────────────────────

def complete_lesson(
    tenant_id: int,
    *,
    lesson_id: str,
    student_id: str,
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    if not lesson_id:
        raise ValueError("lesson_id is required")
    if not student_id:
        raise ValueError("student_id is required")

    progress = create_entity_for_tenant(
        "lms_lesson_progress",
        {
            "lesson_id": lesson_id,
            "student_id": student_id,
            "status": "COMPLETED",
            "completed_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    _fire(tenant_id, "lms.lesson.completed", {
        "lesson_id": lesson_id,
        "student_id": student_id,
        "progress_id": progress.get("id"),
        "tenant_id": tenant_id,
    })
    _audit(
        tenant_id,
        actor,
        build_audit_action("lms_content", "lesson", "complete"),
        f"/internal/lms-content/lessons/{lesson_id}/complete",
        {"progress_id": progress.get("id"), "student_id": student_id},
    )
    _metric(tenant_id, "lms_lessons_completed", 1)

    return {"progress_id": progress.get("id"), "lesson_id": lesson_id, "student_id": student_id, "status": "COMPLETED"}


# ─── submit_assignment ────────────────────────────────────────────────────────

def submit_assignment(
    tenant_id: int,
    *,
    assignment_id: str,
    student_id: str,
    content: str,
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    if not assignment_id:
        raise ValueError("assignment_id is required")
    if not student_id:
        raise ValueError("student_id is required")
    if not content:
        raise ValueError("content is required")

    submission = create_entity_for_tenant(
        "lms_submissions",
        {
            "assignment_id": assignment_id,
            "student_id": student_id,
            "content": content,
            "status": "SUBMITTED",
            "submitted_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )

    _fire(tenant_id, "lms.assignment.submitted", {
        "assignment_id": assignment_id,
        "student_id": student_id,
        "submission_id": submission.get("id"),
        "tenant_id": tenant_id,
    })
    _audit(
        tenant_id,
        actor,
        build_audit_action("lms_content", "assignment", "submit"),
        f"/internal/lms-content/assignments/{assignment_id}/submit",
        {"submission_id": submission.get("id"), "student_id": student_id},
    )
    _metric(tenant_id, "lms_assignments_submitted", 1)

    return {"submission_id": submission.get("id"), "status": "SUBMITTED"}


# ─── grade_submission ─────────────────────────────────────────────────────────

def grade_submission(
    tenant_id: int,
    *,
    submission_id: str,
    grade: float,
    feedback: str = "",
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    if not submission_id:
        raise ValueError("submission_id is required")
    if grade < 0 or grade > 100:
        raise ValueError("grade must be between 0 and 100")

    submissions = list_entities_for_tenant("lms_submissions", tenant_id)
    sub = next((s for s in submissions if str(s.get("id", "")) == str(submission_id)), None)
    if sub is None:
        raise LookupError(f"Submission {submission_id} not found for tenant {tenant_id}")
    if sub.get("status") != "SUBMITTED":
        raise ValueError(f"Cannot grade submission with status '{sub.get('status')}' — only SUBMITTED can be graded")

    grade_record = create_entity_for_tenant(
        "lms_grades",
        {
            "submission_id": submission_id,
            "student_id": sub.get("student_id"),
            "assignment_id": sub.get("assignment_id"),
            "grade": grade,
            "feedback": feedback,
            "graded_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    update_entity_for_tenant(
        "lms_submissions",
        submission_id,
        {**sub, "status": "GRADED", "graded_at": _utc_now().isoformat()},
        tenant_id,
    )

    _fire(tenant_id, "lms.grade.posted", {
        "submission_id": submission_id,
        "student_id": sub.get("student_id"),
        "grade": grade,
        "grade_record_id": grade_record.get("id"),
        "tenant_id": tenant_id,
    })
    _record_outcome(str(submission_id), "submission_graded", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("lms_content", "submission", "grade"),
        f"/internal/lms-content/submissions/{submission_id}/grade",
        {"submission_id": submission_id, "grade": grade},
    )
    _metric(tenant_id, "lms_submissions_graded", 1)

    return {"grade_record_id": grade_record.get("id"), "submission_id": submission_id, "grade": grade, "status": "GRADED"}


# ─── return_submission ────────────────────────────────────────────────────────

def return_submission(
    tenant_id: int,
    *,
    submission_id: str,
    feedback: str,
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    if not submission_id:
        raise ValueError("submission_id is required")
    if not feedback:
        raise ValueError("feedback is required")

    submissions = list_entities_for_tenant("lms_submissions", tenant_id)
    sub = next((s for s in submissions if str(s.get("id", "")) == str(submission_id)), None)
    if sub is None:
        raise LookupError(f"Submission {submission_id} not found for tenant {tenant_id}")
    if sub.get("status") != "GRADED":
        raise ValueError(f"Cannot return submission with status '{sub.get('status')}' — only GRADED can be returned")

    returned = create_entity_for_tenant(
        "lms_returned_submissions",
        {
            "submission_id": submission_id,
            "student_id": sub.get("student_id"),
            "feedback": feedback,
            "returned_at": _utc_now().isoformat(),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    update_entity_for_tenant(
        "lms_submissions",
        submission_id,
        {**sub, "status": "RETURNED", "returned_at": _utc_now().isoformat()},
        tenant_id,
    )
    _record_outcome(str(submission_id), "submission_returned", actor)
    _audit(
        tenant_id,
        actor,
        build_audit_action("lms_content", "submission", "return"),
        f"/internal/lms-content/submissions/{submission_id}/return",
        {"submission_id": submission_id, "returned_id": returned.get("id")},
    )
    _metric(tenant_id, "lms_submissions_returned", 1)

    return {"returned_id": returned.get("id"), "submission_id": submission_id, "status": "RETURNED"}


# ─── get_course_progress ──────────────────────────────────────────────────────

def get_course_progress(
    tenant_id: int,
    *,
    course_id: str,
    student_id: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not course_id:
        raise ValueError("course_id is required")
    if not student_id:
        raise ValueError("student_id is required")

    lessons = list_entities_for_tenant("lms_lessons", tenant_id)
    course_lessons = [l for l in lessons if str(l.get("course_id", "")) == str(course_id)]

    if not course_lessons:
        return {
            "course_id": course_id,
            "student_id": student_id,
            "total_lessons": 0,
            "completed_lessons": 0,
            "completion_pct": 1.0,
            "falling_behind": False,
        }

    progress_records = list_entities_for_tenant("lms_lesson_progress", tenant_id)
    student_completed = {
        str(p.get("lesson_id", ""))
        for p in progress_records
        if str(p.get("student_id", "")) == str(student_id) and p.get("status") == "COMPLETED"
    }

    total = len(course_lessons)
    completed = sum(1 for l in course_lessons if str(l.get("id", "")) in student_completed)
    pct = completed / total

    return {
        "course_id": course_id,
        "student_id": student_id,
        "total_lessons": total,
        "completed_lessons": completed,
        "completion_pct": round(pct, 4),
        "falling_behind": pct < FALLING_BEHIND_THRESHOLD,
    }


# ─── check_falling_behind ─────────────────────────────────────────────────────

def check_falling_behind(
    tenant_id: int,
    *,
    course_id: str,
    student_id: str,
    actor: str = "system",
) -> dict:
    _validate_tenant(tenant_id)
    progress = get_course_progress(tenant_id, course_id=course_id, student_id=student_id)

    if progress["falling_behind"]:
        risk = create_entity_for_tenant(
            "lms_risk_records",
            {
                "student_id": student_id,
                "course_id": course_id,
                "completion_pct": progress["completion_pct"],
                "threshold": FALLING_BEHIND_THRESHOLD,
                "detected_at": _utc_now().isoformat(),
                "tenant_id": tenant_id,
            },
            tenant_id,
        )

        _fire(tenant_id, "lms.student.falling_behind", {
            "student_id": student_id,
            "course_id": course_id,
            "completion_pct": progress["completion_pct"],
            "threshold": FALLING_BEHIND_THRESHOLD,
            "risk_record_id": risk.get("id"),
            "tenant_id": tenant_id,
        })
        _record_outcome(str(risk.get("id") or ""), "student_falling_behind", actor)
        _audit(
            tenant_id,
            actor,
            build_audit_action("lms_content", "risk", "detect"),
            f"/internal/lms-content/risk/{risk.get('id')}",
            {
                "risk_record_id": risk.get("id"),
                "student_id": student_id,
                "course_id": course_id,
                "completion_pct": progress["completion_pct"],
            },
        )
        _metric(tenant_id, "lms_students_falling_behind", 1)

        return {**progress, "risk_record_id": risk.get("id"), "event_fired": True}

    return {**progress, "event_fired": False}


# ─── list helpers ─────────────────────────────────────────────────────────────

def list_submissions(
    tenant_id: int,
    *,
    assignment_id: str | None = None,
    student_id: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("lms_submissions", tenant_id)
    if assignment_id:
        rows = [r for r in rows if str(r.get("assignment_id", "")) == str(assignment_id)]
    if student_id:
        rows = [r for r in rows if str(r.get("student_id", "")) == str(student_id)]
    return rows
