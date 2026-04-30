from __future__ import annotations
from typing import Annotated, Any, TypeAlias

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request, status
from fastapi.encoders import jsonable_encoder
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
from app.modules.audit.service import log_admin_action
from app.modules.enrollments.dependencies import get_enrollments_db
from app.modules.enrollments.models import EnrollmentStatus
from app.modules.enrollments.schemas import (
    EnrollmentConsistencyReportSchema,
    EnrollmentCreateSchema,
    EnrollmentDropSchema,
    EnrollmentListResponseSchema,
    EnrollmentReadSchema,
    EnrollmentStatusChangeSchema,
)
from app.modules.enrollments.service import (
    EnrollmentLifecycleService,
)
from app.modules.rbac.security import get_actor, permission_dependency


class ErrorDetailResponse(BaseModel):
    detail: Any


TrustedTenant: TypeAlias = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor: TypeAlias = Annotated[str, Depends(get_actor)]
EnrollmentsDb: TypeAlias = Annotated[Session, Depends(get_enrollments_db)]


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    return schema_cls.model_validate(payload)


def _raise_enrollments_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, DomainValidationError):
        return validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        return integrity_error_to_http(exc)
    if isinstance(exc, ValidationError):
        # Validation payload may include datetime values in "input"; encode to JSON-safe types.
        return HTTPException(status_code=400, detail=jsonable_encoder(exc.errors()))
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


def _log_router_call(
    request: Request,
    *,
    endpoint: str,
    actor_id: str,
    tenant_id: int,
) -> None:
    """Best-effort observability hook; must never impact endpoint behavior."""
    try:
        log_admin_action(
            actor=actor_id,
            action="enrollment.router.call",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="enrollments.router",
            metadata={
                "endpoint": endpoint,
                "actor_id": actor_id,
                "tenant_id": tenant_id,
            },
            tenant_id=tenant_id,
        )
    except Exception:
        # Observability must not affect business request flow.
        return


router = APIRouter(prefix="/api/admin", tags=["enrollments"])


@router.post(
    "/enrollments",
    summary="Enroll a student into a course",
    description="Creates a new enrollment linking a student profile to a course in a specific academic term.",
    tags=["enrollments"],
    response_model=EnrollmentReadSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def create_enrollment_endpoint(
    payload: dict[str, Any] = Body(...),
    request: Request = None,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("enrollments.write"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
) -> EnrollmentReadSchema:
    try:
        request_model = _parse_payload(EnrollmentCreateSchema, payload)
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="POST /api/admin/enrollments",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.enroll_student(
            tenant_id=tenant_id,
            request=request_model,
            actor_id=actor,
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
        raise _raise_enrollments_http_error(exc) from exc


@router.get(
    "/enrollments/active",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def get_active_enrollment_endpoint(
    # Keep this static route above "/enrollments/{enrollment_id}" to prevent path conflicts.
    student_profile_id: int = Query(..., gt=0),
    course_id: int = Query(..., gt=0),
    term_id: int = Query(..., gt=0),
    request: Request = None,
    actor: Actor = None,
    __: Annotated[None, Depends(permission_dependency("enrollments.read"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
) -> EnrollmentReadSchema | None:
    try:
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="GET /api/admin/enrollments/active",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.get_active_enrollment_for_student_course_term(
            tenant_id=tenant_id,
            student_profile_id=student_profile_id,
            course_id=course_id,
            term_id=term_id,
            actor_id=actor,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_enrollments_http_error(exc) from exc


@router.get(
    "/enrollments/consistency",
    status_code=status.HTTP_200_OK,
    response_model=EnrollmentConsistencyReportSchema,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
    },
)
async def get_enrollment_consistency_endpoint(
    request: Request = None,
    actor: Actor = None,
    __: Annotated[None, Depends(permission_dependency("enrollments.read"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
) -> EnrollmentConsistencyReportSchema:
    try:
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="GET /api/admin/enrollments/consistency",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.list_tenant_enrollment_consistency_report(
            tenant_id=tenant_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_enrollments_http_error(exc) from exc


@router.get(
    "/enrollments/{enrollment_id}",
    summary="Get enrollment by id",
    description="Returns a single enrollment within the trusted tenant scope.",
    tags=["enrollments"],
    response_model=EnrollmentReadSchema,
    status_code=status.HTTP_200_OK,
    responses={
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def get_enrollment_endpoint(
    enrollment_id: int = Path(..., gt=0),
    request: Request = None,
    actor: Actor = None,
    __: Annotated[None, Depends(permission_dependency("enrollments.read"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
) -> EnrollmentReadSchema:
    try:
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="GET /api/admin/enrollments/{enrollment_id}",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.get_enrollment(
            tenant_id=tenant_id,
            enrollment_id=enrollment_id,
            actor_id=actor,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_enrollments_http_error(exc) from exc


@router.get(
    "/students/{student_id}/enrollments",
    summary="List enrollments for a student",
    description="Returns paginated enrollments for a student profile in the trusted tenant scope.",
    tags=["enrollments"],
    response_model=EnrollmentListResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def list_student_enrollments_endpoint(
    student_id: int = Path(..., gt=0),
    request: Request = None,
    actor: Actor = None,
    __: Annotated[None, Depends(permission_dependency("enrollments.read"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: EnrollmentStatus | None = None,
    term_id: int | None = Query(None, gt=0),
) -> EnrollmentListResponseSchema:
    try:
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="GET /api/admin/students/{student_id}/enrollments",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.list_student_enrollments(
            tenant_id=tenant_id,
            student_profile_id=student_id,
            actor_id=actor,
            page=page,
            page_size=page_size,
            status=status,
            term_id=term_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_enrollments_http_error(exc) from exc


@router.get(
    "/courses/{course_id}/roster",
    summary="List course roster",
    description="Returns paginated enrollment roster for a course in a specific academic term.",
    tags=["enrollments"],
    response_model=EnrollmentListResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
    },
)
async def list_course_roster_endpoint(
    course_id: int = Path(..., gt=0),
    term_id: int = Query(..., gt=0),
    request: Request = None,
    actor: Actor = None,
    __: Annotated[None, Depends(permission_dependency("enrollments.read"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: EnrollmentStatus | None = None,
) -> EnrollmentListResponseSchema:
    try:
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="GET /api/admin/courses/{course_id}/roster",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.list_course_roster(
            tenant_id=tenant_id,
            course_id=course_id,
            term_id=term_id,
            actor_id=actor,
            page=page,
            page_size=page_size,
            status=status,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_enrollments_http_error(exc) from exc


@router.patch(
    "/enrollments/{enrollment_id}/status",
    summary="Change enrollment status",
    description="Applies a lifecycle status transition for the specified enrollment.",
    tags=["enrollments"],
    response_model=EnrollmentReadSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def change_enrollment_status_endpoint(
    enrollment_id: int = Path(..., gt=0),
    payload: dict[str, Any] = Body(...),
    request: Request = None,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("enrollments.write"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
) -> EnrollmentReadSchema:
    try:
        request_model = _parse_payload(EnrollmentStatusChangeSchema, payload)
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="PATCH /api/admin/enrollments/{enrollment_id}/status",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.change_enrollment_status(
            tenant_id=tenant_id,
            enrollment_id=enrollment_id,
            request=request_model,
            actor_id=actor,
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
        raise _raise_enrollments_http_error(exc) from exc


@router.post(
    "/enrollments/{enrollment_id}/drop",
    summary="Drop an enrollment",
    description="Drops the specified enrollment using lifecycle-safe status transition rules.",
    tags=["enrollments"],
    response_model=EnrollmentReadSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorDetailResponse},
        403: {"model": ErrorDetailResponse},
        404: {"model": ErrorDetailResponse},
        409: {"model": ErrorDetailResponse},
    },
)
async def drop_enrollment_endpoint(
    enrollment_id: int = Path(..., gt=0),
    payload: dict[str, Any] = Body(...),
    request: Request = None,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("enrollments.write"))] = None,
    tenant: TrustedTenant = None,
    db: EnrollmentsDb = None,
) -> EnrollmentReadSchema:
    try:
        request_model = _parse_payload(EnrollmentDropSchema, payload)
        tenant_id = int(tenant["id"])
        _log_router_call(
            request,
            endpoint="POST /api/admin/enrollments/{enrollment_id}/drop",
            actor_id=actor,
            tenant_id=tenant_id,
        )
        service = EnrollmentLifecycleService(db)
        return await service.drop_enrollment(
            tenant_id=tenant_id,
            enrollment_id=enrollment_id,
            request=request_model,
            actor_id=actor,
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
        raise _raise_enrollments_http_error(exc) from exc


# Backward-compatible alias consumed by app bootstrap imports.
legacy_router = router


