"""FastAPI router for Admissions CRM Batch 1."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.admissions_crm import permissions, schemas, service
from app.modules.admissions_crm.dependencies import get_admissions_crm_db, require_admissions_crm_tenant
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/admissions-crm", tags=["admissions-crm"])

_Actor = Annotated[str, Depends(get_actor)]
_Tenant = Annotated[int, Depends(require_admissions_crm_tenant)]
_DB = Annotated[Session, Depends(get_admissions_crm_db)]


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


@router.post("/leads", response_model=schemas.LeadItemResponse, status_code=201)
def create_lead_endpoint(
    payload: schemas.LeadCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.LeadItemResponse:
    try:
        return service.create_lead(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.get("/leads", response_model=schemas.LeadListResponse)
def list_leads_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.LeadListResponse:
    try:
        del actor
        return service.list_leads(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/leads/{lead_id}", response_model=schemas.LeadItemResponse)
def get_lead_endpoint(
    lead_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.LeadItemResponse:
    try:
        del actor
        return service.get_lead(db, tenant_id, lead_id)
    except Exception as exc:
        _handle(exc)


@router.post("/leads/{lead_id}/qualify", response_model=schemas.LeadItemResponse)
def qualify_lead_endpoint(
    lead_id: int,
    payload: schemas.LeadQualifyRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.QUALIFY))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.LeadItemResponse:
    try:
        return service.qualify_lead(db, tenant_id, lead_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/leads/{lead_id}/convert-to-applicant", response_model=schemas.ApplicantItemResponse)
def convert_lead_to_applicant_endpoint(
    lead_id: int,
    payload: schemas.LeadConvertRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CONVERT))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicantItemResponse:
    try:
        lead = service.get_lead(db, tenant_id, lead_id).item
        request = schemas.ApplicantCreateRequest(
            lead_id=lead_id,
            applicant_ref=payload.applicant_ref,
            full_name=lead.full_name,
            email=lead.email,
            metadata={},
        )
        return service.create_applicant(db, tenant_id, actor, request)
    except Exception as exc:
        _handle(exc)


@router.post("/applicants", response_model=schemas.ApplicantItemResponse, status_code=201)
def create_applicant_endpoint(
    payload: schemas.ApplicantCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicantItemResponse:
    try:
        return service.create_applicant(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.get("/applicants", response_model=schemas.ApplicantListResponse)
def list_applicants_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicantListResponse:
    try:
        del actor
        return service.list_applicants(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/applicants/{applicant_id}", response_model=schemas.ApplicantItemResponse)
def get_applicant_endpoint(
    applicant_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicantItemResponse:
    try:
        del actor
        return service.get_applicant(db, tenant_id, applicant_id)
    except Exception as exc:
        _handle(exc)


@router.post("/applications", response_model=schemas.ApplicationItemResponse, status_code=201)
def create_application_endpoint(
    payload: schemas.ApplicationCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.WRITE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicationItemResponse:
    try:
        return service.create_application(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.get("/applications", response_model=schemas.ApplicationListResponse)
def list_applications_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicationListResponse:
    try:
        del actor
        return service.list_applications(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/applications/{application_id}", response_model=schemas.ApplicationItemResponse)
def get_application_endpoint(
    application_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicationItemResponse:
    try:
        del actor
        return service.get_application(db, tenant_id, application_id)
    except Exception as exc:
        _handle(exc)


@router.post("/applications/{application_id}/submit", response_model=schemas.ApplicationItemResponse)
def submit_application_endpoint(
    application_id: int,
    payload: schemas.ApplicationSubmitRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUBMIT))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.ApplicationItemResponse:
    try:
        return service.submit_application(db, tenant_id, application_id, actor, payload)
    except Exception as exc:
        _handle(exc)
