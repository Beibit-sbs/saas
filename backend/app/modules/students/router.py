from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
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
    StudentCreatePayload,
    StudentDeleteResponse,
    StudentItemResponse,
    StudentListResponse,
    StudentProfileCreateSchema,
    StudentProfileListResponseSchema,
    StudentProfileReadSchema,
    StudentProgramBindingCreateSchema,
    StudentProgramBindingReadSchema,
    StudentStatusChangeSchema,
    StudentUpdatePayload,
)
from app.modules.students.service import (
    StudentLifecycleService,
    create_student,
    delete_student,
    list_students,
    update_student,
)


router = APIRouter(prefix="/api/admin/students", tags=["students"])
legacy_router = APIRouter(prefix="/api/admin/university/students", tags=["students"])


logger = logging.getLogger("app.students")


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


def _raise_legacy_students_http_error(exc: ValueError) -> HTTPException:
    if "not found" in str(exc).lower():
        return HTTPException(status_code=404, detail=str(exc))
    return _raise_students_http_error(exc)


TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor = Annotated[str, Depends(get_actor)]
StudentsDb = Annotated[Session, Depends(get_students_db)]


def _mark_legacy_students_usage(response: Response, tenant: dict[str, object], actor: str | None) -> None:
    # Expose explicit deprecation metadata so clients can migrate to /api/admin/students.
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Fri, 31 Jul 2026 00:00:00 GMT"
    response.headers["Link"] = '</api/admin/students>; rel="successor-version"'
    response.headers["Warning"] = '299 - "Deprecated API: use /api/admin/students"'
    logger.warning(
        "legacy students endpoint used; tenant_id=%s actor=%s",
        tenant.get("id"),
        actor,
    )


@router.post(
    "",
    response_model=StudentProfileReadSchema,
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
) -> StudentProfileReadSchema:
    request_model = _parse_payload(StudentProfileCreateSchema, payload)
    service = StudentLifecycleService(db)
    try:
        return await service.create_student_profile(
            tenant_id=int(tenant["id"]),
            request=request_model,
            created_by=actor,
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
    response_model=StudentProfileReadSchema,
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
) -> StudentProfileReadSchema:
    request_model = _parse_payload(StudentStatusChangeSchema, payload)
    service = StudentLifecycleService(db)
    try:
        return await service.change_student_status(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_id,
            request=request_model,
            actor_id=actor,
        )
    except (PermissionError, ValueError, IntegrityError, TenantResourceNotFoundError, OptimisticLockConflictError) as exc:
        raise _raise_students_http_error(exc) from exc


@router.post(
    "/{student_id}/program-bindings",
    response_model=StudentProgramBindingReadSchema,
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
) -> StudentProgramBindingReadSchema:
    request_model = _parse_payload(StudentProgramBindingCreateSchema, payload)
    request_model = request_model.model_copy(update={"student_profile_id": student_id})

    service = StudentLifecycleService(db)
    try:
        return await service.bind_student_to_program(
            tenant_id=int(tenant["id"]),
            request=request_model,
            actor_id=actor,
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


@legacy_router.get(
    "",
    response_model=StudentListResponse,
    responses={403: {"model": ErrorDetailResponse}},
)
async def legacy_list_students_endpoint(
    response: Response,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admin.students.read"))] = None,
    tenant: TrustedTenant = None,
) -> StudentListResponse:
    _mark_legacy_students_usage(response, tenant, _)
    return StudentListResponse(students=list_students(int(tenant["id"])))


@legacy_router.post(
    "",
    response_model=StudentItemResponse,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}},
)
async def legacy_create_student_endpoint(
    response: Response,
    payload: dict[str, Any] = Body(...),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admin.students.write"))] = None,
    tenant: TrustedTenant = None,
) -> StudentItemResponse:
    _mark_legacy_students_usage(response, tenant, _)
    request_model = _parse_payload(StudentCreatePayload, payload)
    return StudentItemResponse(student=create_student(request_model.model_dump(), int(tenant["id"])))


@legacy_router.put(
    "/{student_id}",
    response_model=StudentItemResponse,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def legacy_update_student_endpoint(
    response: Response,
    student_id: int,
    payload: dict[str, Any] = Body(...),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admin.students.write"))] = None,
    tenant: TrustedTenant = None,
) -> StudentItemResponse:
    _mark_legacy_students_usage(response, tenant, _)
    request_model = _parse_payload(StudentUpdatePayload, payload)
    try:
        return StudentItemResponse(
            student=update_student(student_id, request_model.model_dump(), int(tenant["id"]))
        )
    except ValueError as exc:
        raise _raise_legacy_students_http_error(exc) from exc


@legacy_router.delete(
    "/{student_id}",
    response_model=StudentDeleteResponse,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def legacy_delete_student_endpoint(
    response: Response,
    student_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("admin.students.write"))] = None,
    tenant: TrustedTenant = None,
) -> StudentDeleteResponse:
    _mark_legacy_students_usage(response, tenant, _)
    try:
        return StudentDeleteResponse(
            deleted=True,
            student=delete_student(student_id, int(tenant["id"])),
        )
    except ValueError as exc:
        raise _raise_legacy_students_http_error(exc) from exc
