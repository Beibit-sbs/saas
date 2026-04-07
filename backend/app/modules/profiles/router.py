from __future__ import annotations

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
from app.core.module_helpers.service_validation import (
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.profiles.dependencies import get_profiles_db
from app.modules.profiles.schemas import (
    DepartmentCreateSchema,
    DepartmentListResponseSchema,
    DepartmentReadSchema,
    FacultyCreateSchema,
    FacultyReadSchema,
    PersonCreateSchema,
    PersonListResponseSchema,
    PersonReadSchema,
    PersonUpdateSchema,
    ProgramCreateSchema,
    ProgramReadSchema,
    StudentCreateSchema,
    StudentReadSchema,
)
from app.modules.profiles.service import (
    DepartmentService,
    FacultyService,
    PersonService,
    ProgramService,
    StudentService,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/profiles", tags=["profiles"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _raise_profile_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return permission_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        return integrity_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        return tenant_not_found_to_http(exc)
    if isinstance(exc, ValueError):
        return validation_error_to_http(exc)
    raise HTTPException(status_code=400, detail=str(exc))


TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor = Annotated[str, Depends(get_actor)]
ProfilesDb = Annotated[Session, Depends(get_profiles_db)]


@router.post(
    "/people",
    response_model=PersonReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_person_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("profiles.write"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> PersonReadSchema:
    request_model = _parse_payload(PersonCreateSchema, payload)
    service = PersonService(db)
    try:
        return await service.create_person(int(tenant["id"]), request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _raise_profile_http_error(exc) from exc


@router.get(
    "/people",
    response_model=PersonListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_people_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("profiles.read"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PersonListResponseSchema:
    service = PersonService(db)
    return await service.list_persons(
        tenant_id=int(tenant["id"]),
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get(
    "/people/{person_id}",
    response_model=PersonReadSchema,
    responses={403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
)
async def get_person_endpoint(
    person_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("profiles.read"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> PersonReadSchema:
    service = PersonService(db)
    try:
        return await service.get_person(int(tenant["id"]), person_id)
    except (PermissionError, ValueError) as exc:
        raise _raise_profile_http_error(exc) from exc


@router.patch(
    "/people/{person_id}",
    response_model=PersonReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
)
async def update_person_endpoint(
    person_id: int,
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("profiles.write"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> PersonReadSchema:
    request_model = _parse_payload(PersonUpdateSchema, payload)
    service = PersonService(db)
    try:
        return await service.update_person(int(tenant["id"]), person_id, request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _raise_profile_http_error(exc) from exc


@router.post(
    "/departments",
    response_model=DepartmentReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_department_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("profiles.write"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> DepartmentReadSchema:
    request_model = _parse_payload(DepartmentCreateSchema, payload)
    service = DepartmentService(db)
    try:
        return await service.create_department(int(tenant["id"]), request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _raise_profile_http_error(exc) from exc


@router.get(
    "/departments",
    response_model=DepartmentListResponseSchema,
    responses={403: {"model": ErrorDetailResponse}},
)
async def list_departments_endpoint(
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("profiles.read"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
    page: int = 1,
    page_size: int = 50,
    unit_type: str | None = None,
) -> DepartmentListResponseSchema:
    service = DepartmentService(db)
    return await service.list_departments(
        tenant_id=int(tenant["id"]),
        page=page,
        page_size=page_size,
        unit_type=unit_type,
    )


@router.post(
    "/programs",
    response_model=ProgramReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_program_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("profiles.write"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> ProgramReadSchema:
    request_model = _parse_payload(ProgramCreateSchema, payload)
    service = ProgramService(db)
    try:
        return await service.create_program(int(tenant["id"]), request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _raise_profile_http_error(exc) from exc


@router.post(
    "/students",
    response_model=StudentReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_student_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("profiles.write"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> StudentReadSchema:
    request_model = _parse_payload(StudentCreateSchema, payload)
    service = StudentService(db)
    try:
        return await service.create_student(int(tenant["id"]), request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _raise_profile_http_error(exc) from exc


@router.post(
    "/faculty",
    response_model=FacultyReadSchema,
    responses={400: {"model": ErrorDetailResponse}, 403: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}, 409: {"model": ErrorDetailResponse}},
    status_code=status.HTTP_201_CREATED,
)
async def create_faculty_endpoint(
    payload: dict[str, Any] = Body(...),
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("profiles.write"))] = None,
    tenant: TrustedTenant = None,
    db: ProfilesDb = None,
) -> FacultyReadSchema:
    request_model = _parse_payload(FacultyCreateSchema, payload)
    service = FacultyService(db)
    try:
        return await service.create_faculty(int(tenant["id"]), request_model, actor)
    except (PermissionError, ValueError, IntegrityError) as exc:
        raise _raise_profile_http_error(exc) from exc