from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.career_services.schemas import (
    CareerOpportunityCreateSchema,
    CareerOpportunityItemResponseSchema,
    CareerOpportunityListResponseSchema,
    CareerOpportunityStatus,
    CareerOpportunityStatusUpdateSchema,
)
from app.modules.career_services.service import (
    create_career_opportunity,
    list_career_opportunities,
    update_career_opportunity_status,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/career-services", tags=["career-services"])


@router.get("", response_model=CareerOpportunityListResponseSchema)
def list_opportunities_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("career_services.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: CareerOpportunityStatus | None = None,
    student_id: int | None = None,
) -> CareerOpportunityListResponseSchema:
    items = list_career_opportunities(int(tenant["id"]), status=status, student_id=student_id)
    return CareerOpportunityListResponseSchema(items=items)


@router.post("", response_model=CareerOpportunityItemResponseSchema)
def create_opportunity_endpoint(
    payload: CareerOpportunityCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("career_services.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CareerOpportunityItemResponseSchema:
    try:
        item = create_career_opportunity(int(tenant["id"]), payload, actor)
        return CareerOpportunityItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{opportunity_id}/status", response_model=CareerOpportunityItemResponseSchema)
def update_opportunity_status_endpoint(
    opportunity_id: int,
    payload: CareerOpportunityStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("career_services.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CareerOpportunityItemResponseSchema:
    try:
        item = update_career_opportunity_status(int(tenant["id"]), opportunity_id, payload, actor)
        return CareerOpportunityItemResponseSchema(item=item)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
