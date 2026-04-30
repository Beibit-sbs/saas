"""Phase VI-VI3: Campus SLA router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.campus_sla.schemas import (
    CampusSlaRecordCreatePayload,
    CampusSlaRecordItemResponse,
    CampusSlaRecordListResponse,
    CampusSlaBrainContextResponse,
)
import app.modules.campus_sla.service as _svc

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
        records=_svc.list_sla_records(int(tenant["id"]), status=status, service_type=service_type)
    )


@router.post("/sla-records", response_model=CampusSlaRecordItemResponse, status_code=201)
def create_sla_record_endpoint(
    payload: CampusSlaRecordCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CampusSlaRecordItemResponse:
    try:
        return CampusSlaRecordItemResponse(
            record=_svc.create_sla_record(payload.model_dump(), int(tenant["id"]))
        )
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/brain-context", response_model=CampusSlaBrainContextResponse)
def get_campus_sla_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> CampusSlaBrainContextResponse:
    return CampusSlaBrainContextResponse.model_validate(
        _svc.get_campus_sla_brain_context(int(tenant["id"]))
    )
