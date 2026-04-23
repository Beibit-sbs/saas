from __future__ import annotations
from typing import Annotated, Any, TypeAlias

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
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.students.dependencies import get_students_db
from app.modules.students.models import StudentStatus
from app.modules.students.schemas import (
    StudentProfileCreateSchema,
    StudentProfileListResponseSchema,
    StudentProfileMutationResponse,
    StudentProfileReadSchema,
    StudentProgramBindingConsistencyIssueSchema,
    StudentProgramBindingCreateSchema,
    StudentProgramBindingMutationResponse,
    StudentProgramBindingReadSchema,
    StudentStatusChangeSchema,
)
from app.modules.students.service import (
    StudentLifecycleService,
    get_student_risk_context,
)


router = APIRouter(prefix="/api/admin/students", tags=["students"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise_students_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        return integrity_error_to_http(exc)
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


TrustedTenant: TypeAlias = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor: TypeAlias = Annotated[str, Depends(get_actor)]
StudentsDb: TypeAlias = Annotated[Session, Depends(get_students_db)]


@router.post(
    "",
    response_model=StudentProfileMutationResponse,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_student_profile_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("students.write"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
) -> StudentProfileMutationResponse:
    request_model = _parse_payload(StudentProfileCreateSchema, payload)
    service = StudentLifecycleService(db)
    try:
        result = await service.create_student_profile(
            tenant_id=int(tenant["id"]),
            request=request_model,
            created_by=actor,
        )
        return StudentProfileMutationResponse(
            student=result.entity,
            idempotent_replay=result.idempotent_replay,
        )
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_students_http_error(exc) from exc


@router.get(
    "/{student_id}",
    response_model=StudentProfileReadSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_student_profile_endpoint(
    student_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("students.read"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
) -> StudentProfileReadSchema:
    service = StudentLifecycleService(db)
    try:
        return await service.get_student_profile(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError) as exc:
        raise _raise_students_http_error(exc) from exc


@router.get(
    "",
    response_model=StudentProfileListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_students_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("students.read"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
    page: int = 1,
    page_size: int = 20,
    status: StudentStatus | None = None,
) -> StudentProfileListResponseSchema:
    service = StudentLifecycleService(db)
    return await service.list_student_profiles(
        tenant_id=int(tenant["id"]),
        page=page,
        page_size=page_size,
        status=status,
    )


@router.patch(
    "/{student_id}/status",
    response_model=StudentProfileMutationResponse,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def change_student_status_endpoint(
    student_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("students.write"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
) -> StudentProfileMutationResponse:
    request_model = _parse_payload(StudentStatusChangeSchema, payload)
    service = StudentLifecycleService(db)
    try:
        result = await service.change_student_status(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
            request=request_model,
            actor_id=actor,
        )
        return StudentProfileMutationResponse(
            student=result.entity,
            idempotent_replay=result.idempotent_replay,
        )
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_students_http_error(exc) from exc


@router.post(
    "/{student_id}/program-bindings",
    response_model=StudentProgramBindingMutationResponse,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
    status_code=status.HTTP_201_CREATED,
)
async def bind_student_to_program_endpoint(
    student_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("students.write"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
) -> StudentProgramBindingMutationResponse:
    request_model = _parse_payload(StudentProgramBindingCreateSchema, payload)
    request_model = request_model.model_copy(update={"student_profile_id": student_id})

    service = StudentLifecycleService(db)
    try:
        result = await service.bind_student_to_program(
            tenant_id=int(tenant["id"]),
            request=request_model,
            actor_id=actor,
        )
        return StudentProgramBindingMutationResponse(
            binding=result.entity,
            idempotent_replay=result.idempotent_replay,
        )
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_students_http_error(exc) from exc


@router.get(
    "/{student_id}/program",
    response_model=StudentProgramBindingReadSchema | None,
    responses={403: {"model": ErrorDetailResponse}},
)
async def get_active_primary_program_endpoint(
    student_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("students.read"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
) -> StudentProgramBindingReadSchema | None:
    service = StudentLifecycleService(db)
    try:
        return await service.get_active_primary_program(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError) as exc:
        raise _raise_students_http_error(exc) from exc


@router.get(
    "/consistency/program-bindings",
    response_model=list[StudentProgramBindingConsistencyIssueSchema],
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_program_binding_consistency_issues_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("students.read"))] = None,
    tenant: TrustedTenant = None,
    db: StudentsDb = None,
) -> list[StudentProgramBindingConsistencyIssueSchema]:
    service = StudentLifecycleService(db)
    try:
        return await service.list_program_binding_consistency_issues(tenant_id=int(tenant["id"]))
    except (PermissionError, ValueError, TenantResourceNotFoundError) as exc:
        raise _raise_students_http_error(exc) from exc


# Backward-compatible alias consumed by app bootstrap imports.
legacy_router = router


@router.get(
    "/{student_id}/risk-context",
    response_model=dict,
    responses={403: {"model": ErrorDetailResponse}},
    tags=["students", "brain-core"],
)
async def get_student_risk_context_endpoint(
    student_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("students.read"))] = None,
    tenant: TrustedTenant = None,
) -> dict:
    """Return Brain Core risk context for a specific student.

    Used by Brain Core context builder (student_success context source) to enrich
    decisions with student-level risk indicators: open interventions, advising history,
    risk flags.
    """
    return get_student_risk_context(int(tenant["id"]), student_id)


