from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.alumni.schemas import (
    AlumniRecordCreateSchema,
    AlumniRecordItemResponseSchema,
    AlumniRecordListResponseSchema,
    AlumniStatus,
    AlumniRecordStatusUpdateSchema,
)
import app.modules.alumni.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/alumni", tags=["alumni"])


@router.get("", response_model=AlumniRecordListResponseSchema)
def list_alumni_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("alumni.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: AlumniStatus | None = None,
    student_id: int | None = None,
) -> AlumniRecordListResponseSchema:
    items = _svc.list_alumni_records(int(tenant["id"]), status=status, student_id=student_id)
    return AlumniRecordListResponseSchema(items=items)


@router.post("", response_model=AlumniRecordItemResponseSchema)
def create_alumni_endpoint(
    payload: AlumniRecordCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("alumni.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AlumniRecordItemResponseSchema:
    try:
        item = _svc.create_alumni_record(int(tenant["id"]), payload, actor)
        return AlumniRecordItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{record_id}/status", response_model=AlumniRecordItemResponseSchema)
def update_alumni_status_endpoint(
    record_id: int,
    payload: AlumniRecordStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("alumni.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AlumniRecordItemResponseSchema:
    try:
        item = _svc.update_alumni_status(int(tenant["id"]), record_id, payload, actor)
        return AlumniRecordItemResponseSchema(item=item)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/brain-context")
def get_alumni_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("alumni.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return _svc.get_alumni_brain_context(int(tenant["id"]))
