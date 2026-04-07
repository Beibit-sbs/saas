from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import (
    integrity_error_to_http,
    permission_error_to_http,
    tenant_not_found_to_http,
    validation_error_to_http,
)
from app.core.tenant import get_current_tenant
from app.modules.admissions.dependencies import get_admissions_db
from app.modules.admissions.schemas import (
    ApplicantCreateSchema,
    ApplicantListResponseSchema,
    ApplicantReadSchema,
    ApplicantUpdateSchema,
    ApplicationCreateSchema,
    ApplicationDecisionReadSchema,
    ApplicationListResponseSchema,
    ApplicationReadSchema,
    ApplicationStage,
    ApplicationSubmitRequestSchema,
    DecisionMakeRequestSchema,
    DocumentAttachRequestSchema,
    DocumentReadSchema,
    StageTransitionRequestSchema,
    StageTransitionResponseSchema,
)
from app.modules.admissions.service import (
    ApplicantService,
    ApplicationService,
    DecisionService,
    DocumentService,
    StageTransitionService,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/admissions", tags=["admissions"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _map_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))

    if isinstance(exc, IntegrityError):
        return HTTPException(status_code=409, detail="resource conflict")

    detail = str(exc)
    lowered = detail.lower()

    if "version mismatch" in lowered or "already exists" in lowered or "already exists for application" in lowered:
        return HTTPException(status_code=409, detail=detail)
    if "not found" in lowered or "does not belong to tenant" in lowered or "no decision found" in lowered:
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor = Annotated[str, Depends(get_actor)]
AdmissionsDb = Annotated[Session, Depends(get_admissions_db)]


@router.post(
    "/applicants",
    response_model=ApplicantReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_applicant_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicantReadSchema:
    request_model = _parse_payload(ApplicantCreateSchema, payload)
    service = ApplicantService(db)
    try:
        return await service.create_applicant(int(tenant["id"]), request_model, actor)
    except PermissionError as exc:
        raise permission_error_to_http(exc) from exc
    except IntegrityError as exc:
        raise integrity_error_to_http(exc) from exc
    except ValueError as exc:
        lowered = str(exc).lower()
        if "not found" in lowered or "does not belong to tenant" in lowered:
            raise tenant_not_found_to_http(exc) from exc
        raise validation_error_to_http(exc) from exc


@router.get(
    "/applicants",
    response_model=ApplicantListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_applicants_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admissions.read"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
    program_id: int | None = None,
    application_year: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ApplicantListResponseSchema:
    service = ApplicantService(db)
    return await service.list_applicants(
        tenant_id=int(tenant["id"]),
        program_id=program_id,
        application_year=application_year,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/applicants/{applicant_id}",
    response_model=ApplicantReadSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_applicant_endpoint(
    applicant_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admissions.read"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicantReadSchema:
    service = ApplicantService(db)
    try:
        return await service.get_applicant(int(tenant["id"]), applicant_id)
    except (PermissionError, ValueError) as exc:
        raise _map_service_error(exc) from exc


@router.patch(
    "/applicants/{applicant_id}",
    response_model=ApplicantReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def update_applicant_endpoint(
    applicant_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicantReadSchema:
    request_model = _parse_payload(ApplicantUpdateSchema, payload)
    service = ApplicantService(db)
    try:
        return await service.update_applicant(int(tenant["id"]), applicant_id, request_model, actor)
    except (PermissionError, ValueError) as exc:
        raise _map_service_error(exc) from exc


@router.post(
    "/applications",
    response_model=ApplicationReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_application_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicationReadSchema:
    request_model = _parse_payload(ApplicationCreateSchema, payload)
    service = ApplicationService(db)
    try:
        return await service.create_application(int(tenant["id"]), request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _map_service_error(exc) from exc


@router.get(
    "/applications",
    response_model=ApplicationListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_applications_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admissions.read"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
    program_id: int | None = None,
    stage: ApplicationStage | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ApplicationListResponseSchema:
    service = ApplicationService(db)
    return await service.list_applications(
        tenant_id=int(tenant["id"]),
        program_id=program_id,
        stage=stage,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationReadSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_application_endpoint(
    application_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admissions.read"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicationReadSchema:
    service = ApplicationService(db)
    try:
        return await service.get_application(int(tenant["id"]), application_id)
    except (PermissionError, ValueError) as exc:
        raise _map_service_error(exc) from exc


@router.post(
    "/applications/{application_id}/documents",
    response_model=DocumentReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def attach_document_endpoint(
    application_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.documents.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> DocumentReadSchema:
    request_model = _parse_payload(DocumentAttachRequestSchema, payload)
    service = DocumentService(db)
    try:
        return await service.attach_document(int(tenant["id"]), application_id, request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _map_service_error(exc) from exc


@router.post(
    "/applications/{application_id}/submit",
    response_model=ApplicationReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
)
async def submit_application_endpoint(
    application_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicationReadSchema:
    """Submit an application (transition from NEW → RECEIVED) and start workflow.
    
    - Requires admissions.write permission
    - Tenant ID from trusted context header (X-Tenant-ID)
    - Accepts expected_version for optimistic locking
    - Triggers admissions workflow start
    - Fail-closed: tenant validation, version mismatch raise HTTP 409
    """
    request_model = _parse_payload(ApplicationSubmitRequestSchema, payload)
    service = ApplicationService(db)
    try:
        return await service.submit_application(
            tenant_id=int(tenant["id"]),
            application_id=application_id,
            actor=actor,
            expected_version=request_model.expected_version,
        )
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _map_service_error(exc) from exc


@router.post(
    "/applications/{application_id}/stage-transition",
    response_model=StageTransitionResponseSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def transition_stage_endpoint(
    application_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("admissions.write"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> StageTransitionResponseSchema:
    request_model = _parse_payload(StageTransitionRequestSchema, payload)
    service = StageTransitionService(db)
    try:
        return await service.transition_stage(int(tenant["id"]), application_id, request_model, actor)
    except (PermissionError, ValueError) as exc:
        raise _map_service_error(exc) from exc


@router.post(
    "/applications/{application_id}/decision",
    response_model=ApplicationDecisionReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def make_decision_endpoint(
    application_id: int,
    payload: dict[str, Any] = Body(...),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admissions.decide"))] = None,
    tenant: TrustedTenant = None,
    db: AdmissionsDb = None,
) -> ApplicationDecisionReadSchema:
    request_model = _parse_payload(DecisionMakeRequestSchema, payload)
    service = DecisionService(db)
    try:
        return await service.make_decision(int(tenant["id"]), application_id, request_model)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _map_service_error(exc) from exc