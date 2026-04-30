"""Phase XII-XII1: Faculty Copilot service."""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty_copilot.schemas import (
    FacultyQnARequestSchema,
    LessonPlanRequestSchema,
    MaterialPackRequestSchema,
)
from app.modules.university_core.tenant_entity_service import list_entities_for_tenant
from app.platform.ai import service as ai_service


_FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES: frozenset[str] = frozenset({"active"})


def _check_faculty_has_active_contract_for_copilot(
    *,
    tenant_id: int,
    faculty_id: str,
) -> None:
    """W129: block faculty copilot access unless faculty has an active contract.

    A faculty copilot request from terminated, resigned, or otherwise inactive
    faculty creates phantom AI activity, distorts usage analytics, and may expose
    academic content generation to non-employees.

    Fail-closed: any faculty_contracts lookup failure blocks copilot access.
    """
    normalized_id = faculty_id.strip()

    try:
        contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise DomainValidationError(
            f"Faculty copilot blocked: faculty_contracts lookup failed for faculty '{normalized_id}': {exc}"
        ) from exc

    faculty_contracts = [
        contract
        for contract in contracts
        if str(contract.get("faculty_id") or "").strip() == normalized_id
        or str(contract.get("employee_id") or "").strip() == normalized_id
    ]

    if not faculty_contracts:
        raise DomainValidationError(
            f"Faculty copilot blocked: no faculty contract records found for faculty '{normalized_id}'"
        )

    active_contract = next(
        (
            contract
            for contract in faculty_contracts
            if str(contract.get("status") or "").strip().lower()
            in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES
            or str(contract.get("contract_status") or "").strip().lower()
            in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES
        ),
        None,
    )

    if active_contract is None:
        raise DomainValidationError(
            f"Faculty copilot blocked: no active contract for faculty '{normalized_id}' "
            f"- terminated or resigned faculty cannot use faculty copilot"
        )


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
    _check_faculty_has_active_contract_for_copilot(
        tenant_id=tenant_id,
        faculty_id=payload.faculty_id,
    )
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
    _check_faculty_has_active_contract_for_copilot(
        tenant_id=tenant_id,
        faculty_id=payload.faculty_id,
    )
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
    _check_faculty_has_active_contract_for_copilot(
        tenant_id=tenant_id,
        faculty_id=payload.faculty_id,
    )
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
