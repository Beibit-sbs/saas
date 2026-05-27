"""FastAPI router for Student Services / Welfare / Support runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_services_support import permissions, schemas, service
from app.modules.student_services_support.dependencies import get_student_services_support_db, require_student_services_support_tenant


router = APIRouter(prefix="/api/admin/student-services", tags=["student-services-support"])

_Actor = Annotated[str, Depends(get_actor)]
_Tenant = Annotated[int, Depends(require_student_services_support_tenant)]
_DB = Annotated[Session, Depends(get_student_services_support_db)]


def _handle(exc: Exception) -> None:
    if isinstance(exc, TenantResourceNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, DomainValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    raise exc


@router.post("/requests", response_model=schemas.ServiceRequestItemResponse, status_code=201)
def create_service_request_endpoint(
    payload: schemas.ServiceRequestCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ServiceRequestItemResponse:
    try:
        return service.create_service_request(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.get("/requests", response_model=schemas.ServiceRequestListResponse)
def list_service_requests_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ServiceRequestListResponse:
    try:
        del actor
        return service.list_service_requests(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/requests/{request_id}", response_model=schemas.ServiceRequestItemResponse)
def get_service_request_endpoint(
    request_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ServiceRequestItemResponse:
    try:
        del actor
        return service.get_service_request(db, tenant_id, request_id)
    except Exception as exc:
        _handle(exc)


@router.patch("/requests/{request_id}/assign", response_model=schemas.ServiceRequestItemResponse)
def assign_service_request_endpoint(
    request_id: int,
    payload: schemas.ServiceRequestAssignRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ASSIGN))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ServiceRequestItemResponse:
    try:
        return service.assign_service_request(db, tenant_id, request_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.patch("/requests/{request_id}/status", response_model=schemas.ServiceRequestItemResponse)
def update_service_request_status_endpoint(
    request_id: int,
    payload: schemas.ServiceRequestStatusUpdateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ServiceRequestItemResponse:
    try:
        return service.update_service_request_status(db, tenant_id, request_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/cases", response_model=schemas.SupportCaseItemResponse, status_code=201)
def create_support_case_endpoint(
    payload: schemas.SupportCaseCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SupportCaseItemResponse:
    try:
        return service.create_support_case(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.get("/cases", response_model=schemas.SupportCaseListResponse)
def list_support_cases_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SupportCaseListResponse:
    try:
        del actor
        return service.list_support_cases(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/cases/{case_id}", response_model=schemas.SupportCaseItemResponse)
def get_support_case_endpoint(
    case_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SupportCaseItemResponse:
    try:
        del actor
        return service.get_support_case(db, tenant_id, case_id)
    except Exception as exc:
        _handle(exc)


@router.post("/cases/{case_id}/notes", response_model=schemas.SupportCaseNoteItemResponse, status_code=201)
def add_support_case_note_endpoint(
    case_id: int,
    payload: schemas.SupportCaseNoteCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SupportCaseNoteItemResponse:
    try:
        return service.add_support_case_note(db, tenant_id, case_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/cases/{case_id}/evidence", response_model=schemas.SupportEvidenceItemResponse, status_code=201)
def attach_support_evidence_endpoint(
    case_id: int,
    payload: schemas.SupportEvidenceCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SupportEvidenceItemResponse:
    try:
        return service.attach_support_evidence_metadata(db, tenant_id, case_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/hardship", response_model=schemas.HardshipReadinessItemResponse, status_code=201)
def create_hardship_support_request_endpoint(
    payload: schemas.HardshipSupportCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.HardshipReadinessItemResponse:
    try:
        return service.create_hardship_support_request(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/accommodations", response_model=schemas.AccommodationReadinessItemResponse, status_code=201)
def create_disability_accommodation_request_endpoint(
    payload: schemas.DisabilityAccommodationCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.AccommodationReadinessItemResponse:
    try:
        return service.create_disability_accommodation_request(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/complaints", response_model=schemas.ComplaintItemResponse, status_code=201)
def create_student_complaint_endpoint(
    payload: schemas.StudentComplaintCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ComplaintItemResponse:
    try:
        return service.create_student_complaint(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/escalations", response_model=schemas.EscalationItemResponse, status_code=201)
def escalate_support_case_endpoint(
    payload: schemas.SupportEscalationCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ESCALATE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.EscalationItemResponse:
    try:
        return service.escalate_support_case(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard/summary", response_model=schemas.DashboardSummaryResponse)
def dashboard_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.DashboardSummaryResponse:
    try:
        return service.compute_student_support_dashboard_summary(db, tenant_id, actor)
    except Exception as exc:
        _handle(exc)
