"""Phase XII-XII1: Faculty Copilot router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.faculty_copilot.schemas import (
    FacultyQnARequestSchema,
    LessonPlanRequestSchema,
    MaterialPackRequestSchema,
)
import app.modules.faculty_copilot.service as _svc
from app.platform.ai.schemas import CopilotAnswerReadSchema
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/faculty-copilot", tags=["faculty-copilot"])


@router.get("/health")
def health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty_copilot.read"))],
) -> dict[str, str]:
    return {"status": "ok", "module": "faculty_copilot", "phase": "xii1"}


@router.post("/lesson-plan", response_model=CopilotAnswerReadSchema)
def lesson_plan_endpoint(
    payload: LessonPlanRequestSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty_copilot.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CopilotAnswerReadSchema:
    try:
        answer = _svc.generate_lesson_plan(tenant_id=int(tenant["id"]), actor_id=actor, payload=payload)
        return CopilotAnswerReadSchema.model_validate(answer)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/materials", response_model=CopilotAnswerReadSchema)
def materials_endpoint(
    payload: MaterialPackRequestSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty_copilot.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CopilotAnswerReadSchema:
    try:
        answer = _svc.generate_material_pack(tenant_id=int(tenant["id"]), actor_id=actor, payload=payload)
        return CopilotAnswerReadSchema.model_validate(answer)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/qna", response_model=CopilotAnswerReadSchema)
def qna_endpoint(
    payload: FacultyQnARequestSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty_copilot.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CopilotAnswerReadSchema:
    try:
        answer = _svc.answer_faculty_question(tenant_id=int(tenant["id"]), actor_id=actor, payload=payload)
        return CopilotAnswerReadSchema.model_validate(answer)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
