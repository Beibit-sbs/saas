from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.housing.schemas import (
    HousingRequestCreateSchema,
    HousingRequestItemResponseSchema,
    HousingRequestListResponseSchema,
    HousingRequestStatus,
    HousingRequestStatusUpdateSchema,
)
from app.modules.housing.service import (
    create_housing_request,
    list_housing_requests,
    update_housing_request_status,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/housing", tags=["housing"])


@router.get("", response_model=HousingRequestListResponseSchema)
def list_requests_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("housing.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: HousingRequestStatus | None = None,
    student_id: int | None = None,
) -> HousingRequestListResponseSchema:
    items = list_housing_requests(int(tenant["id"]), status=status, student_id=student_id)
    return HousingRequestListResponseSchema(items=items)


@router.post("", response_model=HousingRequestItemResponseSchema)
def create_request_endpoint(
    payload: HousingRequestCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("housing.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HousingRequestItemResponseSchema:
    try:
        item = create_housing_request(int(tenant["id"]), payload, actor)
        return HousingRequestItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{request_id}/status", response_model=HousingRequestItemResponseSchema)
def update_request_status_endpoint(
    request_id: int,
    payload: HousingRequestStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("housing.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HousingRequestItemResponseSchema:
    try:
        item = update_housing_request_status(int(tenant["id"]), request_id, payload, actor)
        return HousingRequestItemResponseSchema(item=item)
    except (ValueError, DomainValidationError) as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 422
        raise HTTPException(status_code=status_code, detail=detail) from exc
