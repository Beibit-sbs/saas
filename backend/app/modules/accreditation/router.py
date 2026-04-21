from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.accreditation.schemas import (
    AccreditationCreateSchema,
    AccreditationItemResponseSchema,
    AccreditationListResponseSchema,
    AccreditationStandardType,
    AccreditationStatus,
    AccreditationStatusUpdateSchema,
)
from app.modules.accreditation.service import (
    create_accreditation_record,
    get_accreditation_record,
    list_accreditation_records,
    update_accreditation_status,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/accreditation-compliance", tags=["accreditation-compliance"])


@router.get("", response_model=AccreditationListResponseSchema)
def list_accreditation_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.records.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: AccreditationStatus | None = None,
    standard_type: AccreditationStandardType | None = None,
) -> AccreditationListResponseSchema:
    items = list_accreditation_records(int(tenant["id"]), status=status, standard_type=standard_type)
    return AccreditationListResponseSchema(items=items)


@router.get("/{record_id}", response_model=AccreditationItemResponseSchema)
def get_accreditation_endpoint(
    record_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.records.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AccreditationItemResponseSchema:
    try:
        item = get_accreditation_record(int(tenant["id"]), record_id)
        return AccreditationItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=AccreditationItemResponseSchema)
def create_accreditation_endpoint(
    payload: AccreditationCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.records.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AccreditationItemResponseSchema:
    try:
        item = create_accreditation_record(int(tenant["id"]), payload, actor)
        return AccreditationItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{record_id}/status", response_model=AccreditationItemResponseSchema)
def update_accreditation_status_endpoint(
    record_id: int,
    payload: AccreditationStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.records.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AccreditationItemResponseSchema:
    try:
        item = update_accreditation_status(int(tenant["id"]), record_id, payload, actor)
        return AccreditationItemResponseSchema(item=item)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
