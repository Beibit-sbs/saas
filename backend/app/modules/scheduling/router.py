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
from app.modules.scheduling.models import DayOfWeek, LessonStatus
from app.modules.scheduling.schemas import (
    ConflictReportSchema,
    CourseSectionCreateSchema,
    CourseSectionReadSchema,
    DisciplineCreateSchema,
    DisciplineListResponseSchema,
    DisciplineReadSchema,
    InstructorAssignmentSchema,
    InstructorScheduleItemSchema,
    LessonAttendanceListResponseSchema,
    LessonAttendanceReadSchema,
    LessonAttendanceUpsertSchema,
    LessonInstanceCreateSchema,
    LessonInstanceListResponseSchema,
    LessonInstanceReadSchema,
    LessonTopicCreateSchema,
    LessonTopicListResponseSchema,
    LessonTopicReadSchema,
    RoomScheduleItemSchema,
    SectionCancelSchema,
    SectionRescheduleSchema,
    SectionScheduleCreateSchema,
    SectionScheduleReadSchema,
    StudentTopicProgressListResponseSchema,
    StudentTopicProgressReadSchema,
    StudentTopicProgressUpsertSchema,
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


@router.post(
    "/sections/{section_id}/lessons",
    response_model=LessonInstanceReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson_instance(
    section_id: int,
    request: LessonInstanceCreateSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.create_lesson_instance(
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


@router.get("/sections/{section_id}/lessons", response_model=LessonInstanceListResponseSchema)
async def list_lesson_instances(
    section_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: LessonStatus | None = Query(None),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.list_lesson_instances(
            tenant_id=int(tenant["id"]),
            section_id=section_id,
            page=page,
            page_size=page_size,
            status=status,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.put(
    "/lessons/{lesson_instance_id}/attendance",
    response_model=LessonAttendanceReadSchema,
)
async def upsert_lesson_attendance(
    lesson_instance_id: int,
    request: LessonAttendanceUpsertSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.upsert_lesson_attendance(
            tenant_id=int(tenant["id"]),
            lesson_instance_id=lesson_instance_id,
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


@router.get(
    "/lessons/{lesson_instance_id}/attendance",
    response_model=LessonAttendanceListResponseSchema,
)
async def list_lesson_attendance(
    lesson_instance_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.list_lesson_attendance(
            tenant_id=int(tenant["id"]),
            lesson_instance_id=lesson_instance_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
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


@router.post(
    "/disciplines",
    response_model=DisciplineReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_discipline(
    request: DisciplineCreateSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.create_discipline(
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


@router.get("/disciplines", response_model=DisciplineListResponseSchema)
async def list_disciplines(
    include_inactive: bool = Query(False),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.list_disciplines(
            tenant_id=int(tenant["id"]),
            include_inactive=include_inactive,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.post(
    "/disciplines/{discipline_id}/topics",
    response_model=LessonTopicReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson_topic(
    discipline_id: int,
    request: LessonTopicCreateSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.create_lesson_topic(
            tenant_id=int(tenant["id"]),
            discipline_id=discipline_id,
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


@router.get("/disciplines/{discipline_id}/topics", response_model=LessonTopicListResponseSchema)
async def list_lesson_topics(
    discipline_id: int,
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.list_lesson_topics(
            tenant_id=int(tenant["id"]),
            discipline_id=discipline_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc


@router.put(
    "/topics/{topic_id}/progress/{student_profile_id}",
    response_model=StudentTopicProgressReadSchema,
)
async def upsert_student_topic_progress(
    topic_id: int,
    student_profile_id: int,
    request: StudentTopicProgressUpsertSchema,
    actor: Actor = None,
    _: Annotated[None, Depends(permission_dependency("scheduling.write"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.upsert_student_topic_progress(
            tenant_id=int(tenant["id"]),
            topic_id=topic_id,
            student_profile_id=student_profile_id,
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


@router.get(
    "/students/{student_profile_id}/topic-progress",
    response_model=StudentTopicProgressListResponseSchema,
)
async def list_student_topic_progress(
    student_profile_id: int,
    discipline_id: int | None = Query(None, ge=1),
    _: Actor = None,
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))] = None,
    tenant: TrustedTenant = None,
    db: SchedulingDb = None,
):
    service = SchedulingService(db)
    try:
        return await service.list_student_topic_progress(
            tenant_id=int(tenant["id"]),
            student_profile_id=student_profile_id,
            discipline_id=discipline_id,
        )
    except (PermissionError, ValueError, TenantResourceNotFoundError, DomainValidationError) as exc:
        raise _raise_scheduling_http_error(exc) from exc
