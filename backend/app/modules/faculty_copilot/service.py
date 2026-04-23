"""Phase XII-XII1: Faculty Copilot service."""
from __future__ import annotations

from app.modules.faculty_copilot.schemas import (
    FacultyQnARequestSchema,
    LessonPlanRequestSchema,
    MaterialPackRequestSchema,
)
from app.platform.ai import service as ai_service


def _format_objectives(objectives: list[str]) -> str:
    if not objectives:
        return "No explicit objectives provided; infer 3 practical learning outcomes."
    return "; ".join(item.strip() for item in objectives if item.strip())


def generate_lesson_plan(
    *,
    tenant_id: int,
    actor_id: str,
    payload: LessonPlanRequestSchema,
) -> dict[str, object]:
    question = (
        f"Create a faculty lesson plan for course '{payload.course_title}' on topic '{payload.topic}'. "
        f"Duration: {payload.duration_minutes} minutes. "
        f"Student level: {payload.student_level or 'mixed'}. "
        f"Learning objectives: {_format_objectives(payload.learning_objectives)}."
    )
    context = {
        "faculty_id": payload.faculty_id,
        "course_title": payload.course_title,
        "topic": payload.topic,
        "duration_minutes": payload.duration_minutes,
        "student_level": payload.student_level,
        "learning_objectives": payload.learning_objectives,
        "mode": "lesson_plan",
    }
    return ai_service.answer_question(
        tenant_id=tenant_id,
        actor_id=actor_id,
        question=question,
        context=context,
    )


def generate_material_pack(
    *,
    tenant_id: int,
    actor_id: str,
    payload: MaterialPackRequestSchema,
) -> dict[str, object]:
    question = (
        f"Create teaching materials for course '{payload.course_title}', topic '{payload.topic}'. "
        f"Material type: {payload.material_type}. "
        f"Constraints: {payload.constraints or 'none'}."
    )
    context = {
        "faculty_id": payload.faculty_id,
        "course_title": payload.course_title,
        "topic": payload.topic,
        "material_type": payload.material_type,
        "constraints": payload.constraints,
        "mode": "materials",
    }
    return ai_service.answer_question(
        tenant_id=tenant_id,
        actor_id=actor_id,
        question=question,
        context=context,
    )


def answer_faculty_question(
    *,
    tenant_id: int,
    actor_id: str,
    payload: FacultyQnARequestSchema,
) -> dict[str, object]:
    question = payload.question.strip()
    context = {
        "faculty_id": payload.faculty_id,
        "course_title": payload.course_title,
        "mode": "faculty_qna",
    }
    return ai_service.answer_question(
        tenant_id=tenant_id,
        actor_id=actor_id,
        question=question,
        context=context,
    )
