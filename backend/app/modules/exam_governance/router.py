from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.exam_governance.schemas import (
    ExamCreateSchema,
    ExamDashboardSummarySchema,
    ExamItemResponseSchema,
    ExamListResponseSchema,
    ExamStatisticsSchema,
    ExamUpdateSchema,
)
from app.modules.exam_governance.service import (
    create_exam,
    get_exam_dashboard_summary,
    get_exam_statistics,
    list_exams,
    update_exam,
)


router = APIRouter(prefix="/api/admin/exam-governance", tags=["exam-governance"])


@router.get("/dashboard/summary", response_model=ExamDashboardSummarySchema)
def get_dashboard_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("exams.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExamDashboardSummarySchema:
    data = get_exam_dashboard_summary(int(tenant["id"]))
    return ExamDashboardSummarySchema(**data)


@router.get("", response_model=ExamListResponseSchema)
def list_exams_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("exams.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    term_id: str | None = None,
) -> ExamListResponseSchema:
    items = list_exams(int(tenant["id"]), status=status, term_id=term_id)
    return ExamListResponseSchema(items=items)


@router.post("", response_model=ExamItemResponseSchema)
def create_exam_endpoint(
    payload: ExamCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("exams.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExamItemResponseSchema:
    try:
        item = create_exam(int(tenant["id"]), payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ExamItemResponseSchema(item=item)


@router.get("/{exam_id}", response_model=ExamItemResponseSchema)
def get_exam_endpoint(
    exam_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("exams.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExamItemResponseSchema:
    items = list_exams(int(tenant["id"]))
    item = next((i for i in items if i.id == exam_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    return ExamItemResponseSchema(item=item)


@router.put("/{exam_id}", response_model=ExamItemResponseSchema)
def update_exam_endpoint(
    exam_id: int,
    payload: ExamUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("exams.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExamItemResponseSchema:
    try:
        item = update_exam(int(tenant["id"]), exam_id, payload, actor)
        return ExamItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{exam_id}/statistics", response_model=ExamStatisticsSchema)
def get_exam_statistics_endpoint(
    exam_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("exams.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ExamStatisticsSchema:
    try:
        data = get_exam_statistics(int(tenant["id"]), exam_id)
        return ExamStatisticsSchema(**data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
