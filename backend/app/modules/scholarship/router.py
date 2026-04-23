"""Phase VIII-1: Scholarship router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.scholarship.schemas import (
    ScholarshipApplicationCreatePayload,
    ScholarshipApplicationItemResponse,
    ScholarshipApplicationListResponse,
    ScholarshipAwardCreatePayload,
    ScholarshipAwardItemResponse,
    ScholarshipAwardListResponse,
    ScholarshipBrainContextResponse,
)
from app.modules.scholarship.service import (
    create_scholarship_application,
    create_scholarship_award,
    get_scholarship_brain_context,
    list_scholarship_applications,
    list_scholarship_awards,
)

router = APIRouter(prefix="/api/admin/scholarship", tags=["scholarship"])


@router.get("/applications", response_model=ScholarshipApplicationListResponse)
def list_applications_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    scholarship_type: str | None = None,
) -> ScholarshipApplicationListResponse:
    return ScholarshipApplicationListResponse(
        records=list_scholarship_applications(
            int(tenant["id"]), status=status, scholarship_type=scholarship_type
        )
    )


@router.post("/applications", response_model=ScholarshipApplicationItemResponse, status_code=201)
def create_application_endpoint(
    payload: ScholarshipApplicationCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ScholarshipApplicationItemResponse:
    return ScholarshipApplicationItemResponse(
        record=create_scholarship_application(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/awards", response_model=ScholarshipAwardListResponse)
def list_awards_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
) -> ScholarshipAwardListResponse:
    return ScholarshipAwardListResponse(
        records=list_scholarship_awards(int(tenant["id"]), status=status)
    )


@router.post("/awards", response_model=ScholarshipAwardItemResponse, status_code=201)
def create_award_endpoint(
    payload: ScholarshipAwardCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ScholarshipAwardItemResponse:
    return ScholarshipAwardItemResponse(
        record=create_scholarship_award(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=ScholarshipBrainContextResponse)
def brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ScholarshipBrainContextResponse:
    return ScholarshipBrainContextResponse(
        **get_scholarship_brain_context(int(tenant["id"]))
    )
