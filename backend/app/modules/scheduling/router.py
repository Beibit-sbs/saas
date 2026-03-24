from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
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
from app.modules.observability.metrics import observe_scheduling_conflict
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.scheduling.dependencies import get_scheduling_db
from app.modules.scheduling.models import DayOfWeek
from app.modules.scheduling.schemas import (
    ConflictReportSchema,
    CourseSectionCreateSchema,
    CourseSectionReadSchema,
    InstructorAssignmentSchema,
    InstructorScheduleItemSchema,
    RoomScheduleItemSchema,
    SectionCancelSchema,
    SectionRescheduleSchema,
    SectionScheduleCreateSchema,
    SectionScheduleReadSchema,
    StudentScheduleItemSchema,
)
from app.modules.scheduling.service import SchedulingService


class ErrorDetailResponse(BaseModel):
    detail: Any


TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
Actor = Annotated[str, Depends(get_actor)]
SchedulingDb = Annotated[Session, Depends(get_scheduling_db)]


def _raise_scheduling_http_error(exc: Exception) -> HTTPException:
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
    return HTTPException(status_code=400, detail=str(exc))


router = APIRouter(prefix="/api/admin/scheduling", tags=["scheduling"])


@router.post("/sections", response_model=CourseSectionReadSchema, status_code=status.HTTP_201_CREATED)
async def create_course_section(
    request: CourseSectionCreateSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.create_course_section(
            tenant_id=int(tenant["id"]),
            request=request,
            actor_id=actor,
        )
    except (
        PermissionError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.post(
    "/sections/{section_id}/schedule",
    response_model=SectionScheduleReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_section(
    section_id: int,
    request: SectionScheduleCreateSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.schedule_section(
            tenant_id=int(tenant["id"]),
            section_id=section_id,
            request=request,
            actor_id=actor,
        )
    except (
        PermissionError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.post("/sections/{section_id}/instructors", status_code=status.HTTP_201_CREATED)
async def assign_instructor(
    section_id: int,
    request: InstructorAssignmentSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.assign_instructor(
            tenant_id=int(tenant["id"]),
            section_id=section_id,
            request=request,
            actor_id=actor,
        )
    except (
        PermissionError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.patch("/sections/{section_id}/reschedule", response_model=SectionScheduleReadSchema)
async def reschedule_section(
    section_id: int,
    request: SectionRescheduleSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.reschedule_section(
            tenant_id=int(tenant["id"]),
            section_id=section_id,
            request=request,
            actor_id=actor,
        )
    except (
        PermissionError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.patch("/sections/{section_id}/cancel", response_model=CourseSectionReadSchema)
async def cancel_section(
    section_id: int,
    request: SectionCancelSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.cancel_section(
            tenant_id=int(tenant["id"]),
            section_id=section_id,
            request=request,
            actor_id=actor,
        )
    except (
        PermissionError,
        ValueError,
        IntegrityError,
        TenantResourceNotFoundError,
        DomainValidationError,
        OptimisticLockConflictError,
    ) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.get("/schedules/students/{student_id}", response_model=list[StudentScheduleItemSchema])
async def get_student_schedule(
    student_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.get_student_schedule(tenant_id=int(tenant["id"]), student_id=student_id)
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.get("/schedules/instructors/{instructor_id}", response_model=list[InstructorScheduleItemSchema])
async def get_instructor_schedule(
    instructor_id: str,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.get_instructor_schedule(tenant_id=int(tenant["id"]), instructor_id=instructor_id)
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.get("/schedules/rooms/{classroom_id}", response_model=list[RoomScheduleItemSchema])
async def get_room_schedule(
    classroom_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.get_room_schedule(tenant_id=int(tenant["id"]), classroom_id=classroom_id)
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.get("/sections/{section_id}/conflicts", response_model=ConflictReportSchema)
async def detect_schedule_conflicts(
    section_id: int,
    time_slot_id: int = Query(..., ge=1),
    classroom_id: int = Query(..., ge=1),
    day_of_week: DayOfWeek = Query(...),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        conflict_report = await service.detect_schedule_conflicts(
            tenant_id=int(tenant["id"]),
            section_id=section_id,
            time_slot_id=time_slot_id,
            classroom_id=classroom_id,
            day_of_week=day_of_week,
        )
        has_conflict = bool(
            getattr(conflict_report, "has_room_conflict", False)
            or getattr(conflict_report, "instructor_conflicts", [])
        )
        if has_conflict:
            observe_scheduling_conflict()
        return conflict_report
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc
