from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.syllabus_governance.schemas import (
    SyllabusCreateSchema,
    SyllabusDashboardSummarySchema,
    SyllabusItemResponseSchema,
    SyllabusListResponseSchema,
    SyllabusUpdateSchema,
)
import app.modules.syllabus_governance.service as _svc


router = APIRouter(prefix="/api/admin/syllabus-governance", tags=["syllabus-governance"])


@router.get("/dashboard/summary", response_model=SyllabusDashboardSummarySchema)
def get_dashboard_summary(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("syllabus.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SyllabusDashboardSummarySchema:
    data = _svc.get_syllabus_dashboard_summary(int(tenant["id"]))
    return SyllabusDashboardSummarySchema(**data)


@router.get("", response_model=SyllabusListResponseSchema)
def list_syllabi_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("syllabus.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    department_id: str | None = None,
) -> SyllabusListResponseSchema:
    items = _svc.list_syllabi(int(tenant["id"]), status=status, department_id=department_id)
    return SyllabusListResponseSchema(items=items)


@router.post("", response_model=SyllabusItemResponseSchema)
def create_syllabus_endpoint(
    payload: SyllabusCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("syllabus.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SyllabusItemResponseSchema:
    try:
        item = _svc.create_syllabus(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SyllabusItemResponseSchema(item=item)


@router.get("/{syllabus_id}", response_model=SyllabusItemResponseSchema)
def get_syllabus_endpoint(
    syllabus_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("syllabus.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SyllabusItemResponseSchema:
    items = _svc.list_syllabi(int(tenant["id"]))
    item = next((i for i in items if i.id == syllabus_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    return SyllabusItemResponseSchema(item=item)


@router.put("/{syllabus_id}", response_model=SyllabusItemResponseSchema)
def update_syllabus_endpoint(
    syllabus_id: int,
    payload: SyllabusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("syllabus.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SyllabusItemResponseSchema:
    try:
        item = _svc.update_syllabus(int(tenant["id"]), syllabus_id, payload, actor)
        return SyllabusItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{syllabus_id}/approval-workflow")
def get_approval_workflow_endpoint(
    syllabus_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("syllabus.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    try:
        return _svc.get_approval_workflow(int(tenant["id"]), syllabus_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
