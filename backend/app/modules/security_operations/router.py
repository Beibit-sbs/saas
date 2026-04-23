"""Phase VI-VI1: Security operations router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.security_operations.schemas import (
    SecurityIncidentCreatePayload,
    SecurityIncidentItemResponse,
    SecurityIncidentListResponse,
    SecurityOperationsBrainContextResponse,
    SecurityVisitorCreatePayload,
    SecurityVisitorItemResponse,
    SecurityVisitorListResponse,
)
from app.modules.security_operations.service import (
    create_security_incident,
    create_security_visitor,
    get_security_operations_brain_context,
    list_security_incidents,
    list_security_visitors,
)


router = APIRouter(prefix="/api/admin/security-operations", tags=["security-operations"])


@router.get("/incidents", response_model=SecurityIncidentListResponse)
def list_security_incidents_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    severity: str | None = None,
    status: str | None = None,
) -> SecurityIncidentListResponse:
    return SecurityIncidentListResponse(
        records=list_security_incidents(int(tenant["id"]), severity=severity, status=status)
    )


@router.post("/incidents", response_model=SecurityIncidentItemResponse, status_code=201)
def create_security_incident_endpoint(
    payload: SecurityIncidentCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SecurityIncidentItemResponse:
    return SecurityIncidentItemResponse(record=create_security_incident(payload.model_dump(), int(tenant["id"])))


@router.get("/visitors", response_model=SecurityVisitorListResponse)
def list_security_visitors_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
    access_status: str | None = None,
) -> SecurityVisitorListResponse:
    return SecurityVisitorListResponse(
        records=list_security_visitors(int(tenant["id"]), status=status, access_status=access_status)
    )


@router.post("/visitors", response_model=SecurityVisitorItemResponse, status_code=201)
def create_security_visitor_endpoint(
    payload: SecurityVisitorCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SecurityVisitorItemResponse:
    return SecurityVisitorItemResponse(record=create_security_visitor(payload.model_dump(), int(tenant["id"])))


@router.get("/brain-context", response_model=SecurityOperationsBrainContextResponse)
def get_security_operations_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SecurityOperationsBrainContextResponse:
    return SecurityOperationsBrainContextResponse.model_validate(
        get_security_operations_brain_context(int(tenant["id"]))
    )
