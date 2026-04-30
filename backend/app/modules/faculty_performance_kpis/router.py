"""Phase X-X1: Faculty performance KPI router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.faculty_performance_kpis.schemas import (
    FacultyKpiCreateSchema,
    FacultyKpiItemResponseSchema,
    FacultyKpiListResponseSchema,
    FacultyKpiStatus,
    FacultyKpiStatusUpdateSchema,
)
import app.modules.faculty_performance_kpis.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/faculty-performance-kpis", tags=["faculty-performance-kpis"])


@router.get("", response_model=FacultyKpiListResponseSchema)
def list_faculty_kpis_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    department_id: str | None = None,
    status: FacultyKpiStatus | None = None,
) -> FacultyKpiListResponseSchema:
    items = _svc.list_faculty_kpis(int(tenant["id"]), department_id=department_id, status=status)
    return FacultyKpiListResponseSchema(items=items)


@router.post("", response_model=FacultyKpiItemResponseSchema)
def create_faculty_kpi_endpoint(
    payload: FacultyKpiCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyKpiItemResponseSchema:
    try:
        item = _svc.create_faculty_kpi(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FacultyKpiItemResponseSchema(item=item)


@router.get("/{kpi_id}", response_model=FacultyKpiItemResponseSchema)
def get_faculty_kpi_endpoint(
    kpi_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyKpiItemResponseSchema:
    item = _svc.get_faculty_kpi(int(tenant["id"]), kpi_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Faculty KPI record not found")
    return FacultyKpiItemResponseSchema(item=item)


@router.patch("/{kpi_id}/status", response_model=FacultyKpiItemResponseSchema)
def update_faculty_kpi_status_endpoint(
    kpi_id: int,
    payload: FacultyKpiStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyKpiItemResponseSchema:
    item = _svc.update_faculty_kpi_status(int(tenant["id"]), kpi_id, payload, actor)
    if item is None:
        raise HTTPException(status_code=404, detail="Faculty KPI record not found")
    return FacultyKpiItemResponseSchema(item=item)
