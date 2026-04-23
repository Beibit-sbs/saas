"""Phase VI-VI3: Campus SLA router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.campus_sla.schemas import (
    CampusSlaRecordCreatePayload,
    CampusSlaRecordItemResponse,
    CampusSlaRecordListResponse,
    CampusSlaBrainContextResponse,
)
from app.modules.campus_sla.service import (
    create_sla_record,
    get_campus_sla_brain_context,
    list_sla_records,
)

router = APIRouter(prefix="/api/admin/campus-sla", tags=["campus-sla"])


@router.get("/sla-records", response_model=CampusSlaRecordListResponse)
def list_sla_records_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    service_type: str | None = None,
) -> CampusSlaRecordListResponse:
    return CampusSlaRecordListResponse(
        records=list_sla_records(int(tenant["id"]), status=status, service_type=service_type)
    )


@router.post("/sla-records", response_model=CampusSlaRecordItemResponse, status_code=201)
def create_sla_record_endpoint(
    payload: CampusSlaRecordCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CampusSlaRecordItemResponse:
    return CampusSlaRecordItemResponse(
        record=create_sla_record(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=CampusSlaBrainContextResponse)
def get_campus_sla_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CampusSlaBrainContextResponse:
    return CampusSlaBrainContextResponse.model_validate(
        get_campus_sla_brain_context(int(tenant["id"]))
    )
