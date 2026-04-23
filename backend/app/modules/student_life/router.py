from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_life.schemas import (
    AccessibilitySupportCreateSchema,
    AccessibilitySupportItemResponseSchema,
    AccessibilitySupportListResponseSchema,
    CounselingCaseCreateSchema,
    CounselingCaseItemResponseSchema,
    CounselingCaseListResponseSchema,
    DisciplinaryCaseCreateSchema,
    DisciplinaryCaseItemResponseSchema,
    DisciplinaryCaseListResponseSchema,
    StudentLifeHealthResponseSchema,
    WellbeingCheckinCreateSchema,
    WellbeingCheckinItemResponseSchema,
    WellbeingCheckinListResponseSchema,
)
from app.modules.student_life.service import (
    create_accessibility_support,
    create_counseling_case,
    create_disciplinary_case,
    create_wellbeing_checkin,
    get_student_life_health_snapshot,
    list_accessibility_supports,
    list_counseling_cases,
    list_disciplinary_cases,
    list_wellbeing_checkins,
)


router = APIRouter(prefix="/api/admin/student-life", tags=["student_life"])


@router.get("/health", response_model=StudentLifeHealthResponseSchema)
def get_student_life_health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_life.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> StudentLifeHealthResponseSchema:
    item = get_student_life_health_snapshot(int(tenant["id"]))
    return StudentLifeHealthResponseSchema(item=item)


@router.get("/counseling-cases", response_model=CounselingCaseListResponseSchema)
def list_counseling_cases_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_life.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CounselingCaseListResponseSchema:
    return CounselingCaseListResponseSchema(items=list_counseling_cases(int(tenant["id"])))


@router.post("/counseling-cases", response_model=CounselingCaseItemResponseSchema)
def create_counseling_case_endpoint(
    payload: CounselingCaseCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("student_life.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CounselingCaseItemResponseSchema:
    try:
        item = create_counseling_case(int(tenant["id"]), payload, actor)
        return CounselingCaseItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/wellbeing-checkins", response_model=WellbeingCheckinListResponseSchema)
def list_wellbeing_checkins_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_life.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WellbeingCheckinListResponseSchema:
    return WellbeingCheckinListResponseSchema(items=list_wellbeing_checkins(int(tenant["id"])))


@router.post("/wellbeing-checkins", response_model=WellbeingCheckinItemResponseSchema)
def create_wellbeing_checkin_endpoint(
    payload: WellbeingCheckinCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("student_life.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> WellbeingCheckinItemResponseSchema:
    try:
        item = create_wellbeing_checkin(int(tenant["id"]), payload, actor)
        return WellbeingCheckinItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/accessibility-supports", response_model=AccessibilitySupportListResponseSchema)
def list_accessibility_supports_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_life.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AccessibilitySupportListResponseSchema:
    return AccessibilitySupportListResponseSchema(items=list_accessibility_supports(int(tenant["id"])))


@router.post("/accessibility-supports", response_model=AccessibilitySupportItemResponseSchema)
def create_accessibility_support_endpoint(
    payload: AccessibilitySupportCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("student_life.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AccessibilitySupportItemResponseSchema:
    try:
        item = create_accessibility_support(int(tenant["id"]), payload, actor)
        return AccessibilitySupportItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/disciplinary-cases", response_model=DisciplinaryCaseListResponseSchema)
def list_disciplinary_cases_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("student_life.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DisciplinaryCaseListResponseSchema:
    return DisciplinaryCaseListResponseSchema(items=list_disciplinary_cases(int(tenant["id"])))


@router.post("/disciplinary-cases", response_model=DisciplinaryCaseItemResponseSchema)
def create_disciplinary_case_endpoint(
    payload: DisciplinaryCaseCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("student_life.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DisciplinaryCaseItemResponseSchema:
    try:
        item = create_disciplinary_case(int(tenant["id"]), payload, actor)
        return DisciplinaryCaseItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc