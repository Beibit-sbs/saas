from __future__ import annotations

from typing import Annotated, Any, TypeAlias

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
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
from app.modules.grades.dependencies import get_grades_db
from app.modules.grades.schemas import (
    GradeChangeSchema,
    GradeEnrollmentConsistencyReportSchema,
    GradeListResponseSchema,
    GradeMutationResponse,
    GradeReadSchema,
    GradeSubmitSchema,
)
from app.modules.grades.service import GradeLifecycleService
from app.modules.observability.metrics import observe_grade_submission
from app.modules.rbac.security import get_actor, permission_dependency


class ErrorDetailResponse(BaseModel):
    detail: Any


TrustedTenant: TypeAlias = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor: TypeAlias = Annotated[str, Depends(get_actor)]
GradesDb: TypeAlias = Annotated[Session, Depends(get_grades_db)]


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    return schema_cls.model_validate(payload)


def _raise_grades_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        return integrity_error_to_http(exc)
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=exc.errors())
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


router = APIRouter(prefix="/api/admin", tags=["grades"])


@router.post(
    "/grades/submit",
    summary="Submit grade for enrollment",
    description="Creates a grade submission and updates enrollment grade placeholders.",
    response_model=GradeMutationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def submit_grade_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("grades.write"))] = None,
    tenant: TrustedTenant = None,
    db: GradesDb = None,
) -> GradeMutationResponse:
    try:
        request_model = _parse_payload(GradeSubmitSchema, payload)
        service = GradeLifecycleService(db)
        result = await service.submit_grade(
            tenant_id=int(tenant["id"]),
            request=request_model,
            actor_id=actor,
        )
        if not result.idempotent_replay:
            observe_grade_submission()
        return GradeMutationResponse(
            grade=result.entity,
            idempotent_replay=result.idempotent_replay,
        )
    except (
        PermissionError,
        ValidationError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_grades_http_error(exc) from exc


@router.patch(
    "/grades/change",
    summary="Change submitted grade",
    description="Changes a previously submitted grade with optimistic locking.",
    response_model=GradeMutationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def change_grade_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("grades.write"))] = None,
    tenant: TrustedTenant = None,
    db: GradesDb = None,
) -> GradeMutationResponse:
    try:
        request_model = _parse_payload(GradeChangeSchema, payload)
        service = GradeLifecycleService(db)
        result = await service.change_grade(
            tenant_id=int(tenant["id"]),
            request=request_model,
            actor_id=actor,
        )
        return GradeMutationResponse(
            grade=result.entity,
            idempotent_replay=result.idempotent_replay,
        )
    except (
        PermissionError,
        ValidationError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_grades_http_error(exc) from exc


@router.get(
    "/courses/{course_id}/grades",
    summary="List grades for course",
    description="Returns paginated grade submissions for a course and optional term.",
    response_model=GradeListResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def list_course_grades_endpoint(
    course_id: int = Path(..., gt=0),
    actor: Actor = None,
    __: Annotated[None, Depends(permission_dependency("grades.read"))] = None,
    tenant: TrustedTenant = None,
    db: GradesDb = None,
    term_id: int | None = Query(None, gt=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> GradeListResponseSchema:
    service = GradeLifecycleService(db)
    try:
        return await service.list_course_grades(
            tenant_id=int(tenant["id"]),
            course_id=course_id,
            term_id=term_id,
            page=page,
            page_size=page_size,
            actor_id=actor,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_grades_http_error(exc) from exc


@router.get(
    "/grades/consistency",
    summary="Get tenant grade-enrollment consistency report",
    description="Read-only reconciliation summary between enrollments and grade submissions.",
    response_model=GradeEnrollmentConsistencyReportSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
    },
)
async def get_grade_enrollment_consistency_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("grades.read"))] = None,
    tenant: TrustedTenant = None,
    db: GradesDb = None,
) -> GradeEnrollmentConsistencyReportSchema:
    service = GradeLifecycleService(db)
    try:
        return await service.list_tenant_grade_enrollment_consistency_report(tenant_id=int(tenant["id"]))
    except (PermissionError, ValueError, DomainValidationError) as exc:
        raise _raise_grades_http_error(exc) from exc
