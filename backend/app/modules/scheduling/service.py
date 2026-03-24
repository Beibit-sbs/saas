from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.courses.models import CourseModel
from app.modules.enrollments.models import EnrollmentModel, EnrollmentStatus
from app.modules.scheduling.business_rules import SchedulingRules
from app.modules.scheduling.models import (
    ClassroomModel,
    CourseSectionModel,
    DayOfWeek,
    InstructorAssignmentModel,
    SectionScheduleModel,
    SectionStatus,
    TimeSlotModel,
)
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
from app.modules.students.models import StudentProfileModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _time_to_str(value) -> str:
    return value.strftime("%H:%M:%S") if value is not None else "00:00:00"


def _audit(actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="scheduling",
        metadata=metadata,
        tenant_id=tenant_id,
    )


class SchedulingService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _load_course_section(self, tenant_id: int, section_id: int) -> CourseSectionModel:
        section = self.db.execute(
            select(CourseSectionModel).where(
                and_(
                    CourseSectionModel.id == section_id,
                    CourseSectionModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(section, tenant_id, resource_name="Course section", resource_id=section_id)
        return section

    def _load_section_schedule(self, tenant_id: int, section_id: int) -> SectionScheduleModel | None:
        return self.db.execute(
            select(SectionScheduleModel).where(
                and_(
                    SectionScheduleModel.tenant_id == tenant_id,
                    SectionScheduleModel.section_id == section_id,
                )
            )
        ).scalar_one_or_none()

    def _load_time_slot(self, tenant_id: int, time_slot_id: int) -> TimeSlotModel:
        slot = self.db.execute(
            select(TimeSlotModel).where(
                and_(
                    TimeSlotModel.id == time_slot_id,
                    TimeSlotModel.tenant_id == tenant_id,
                    TimeSlotModel.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        SchedulingRules.validate_time_slot_exists(slot, tenant_id=tenant_id, time_slot_id=time_slot_id)
        SchedulingRules.validate_time_range(start_time=slot.start_time, end_time=slot.end_time)
        return slot

    def _load_classroom(self, tenant_id: int, classroom_id: int) -> ClassroomModel:
        classroom = self.db.execute(
            select(ClassroomModel).where(
                and_(
                    ClassroomModel.id == classroom_id,
                    ClassroomModel.tenant_id == tenant_id,
                    ClassroomModel.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        SchedulingRules.validate_classroom_exists(classroom, tenant_id=tenant_id, classroom_id=classroom_id)
        return classroom

    def _load_course_placeholder(self, tenant_id: int, course_id: int) -> CourseModel:
        course = self.db.execute(select(CourseModel).where(CourseModel.id == course_id)).scalar_one_or_none()
        if course is None:
            raise TenantResourceNotFoundError(
                f"Course {course_id} not found or does not belong to tenant {tenant_id}"
            )

        raw_tenant = getattr(course, "tenant_id", None)
        if raw_tenant is not None:
            try:
                normalized_tenant = int(raw_tenant)
            except (TypeError, ValueError):
                raise TenantResourceNotFoundError(
                    f"Course {course_id} not found or does not belong to tenant {tenant_id}"
                ) from None
            if normalized_tenant != tenant_id:
                raise TenantResourceNotFoundError(
                    f"Course {course_id} not found or does not belong to tenant {tenant_id}"
                )
        return course

    def _validate_term_exists(self, tenant_id: int, term_id: int) -> None:
        from app.modules.enrollments.models import AcademicTermModel

        term = self.db.execute(
            select(AcademicTermModel).where(
                and_(
                    AcademicTermModel.id == term_id,
                    AcademicTermModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(term, tenant_id, resource_name="Academic term", resource_id=term_id)

    def _get_room_conflict(
        self,
        *,
        tenant_id: int,
        classroom_id: int,
        time_slot_id: int,
        day_of_week: DayOfWeek,
        exclude_section_id: int | None = None,
    ) -> SectionScheduleModel | None:
        filters = [
            SectionScheduleModel.tenant_id == tenant_id,
            SectionScheduleModel.classroom_id == classroom_id,
            SectionScheduleModel.time_slot_id == time_slot_id,
            SectionScheduleModel.day_of_week == day_of_week,
        ]
        if exclude_section_id is not None:
            filters.append(SectionScheduleModel.section_id != exclude_section_id)

        return self.db.execute(select(SectionScheduleModel).where(and_(*filters))).scalar_one_or_none()

    def _find_instructor_conflicts(
        self,
        *,
        tenant_id: int,
        instructor_id: str,
        day_of_week: DayOfWeek,
        start_time,
        end_time,
        exclude_section_id: int | None,
    ) -> list[dict]:
        query = (
            select(
                SectionScheduleModel.section_id,
                SectionScheduleModel.day_of_week,
                TimeSlotModel.start_time,
                TimeSlotModel.end_time,
            )
            .join(
                InstructorAssignmentModel,
                and_(
                    InstructorAssignmentModel.tenant_id == SectionScheduleModel.tenant_id,
                    InstructorAssignmentModel.section_id == SectionScheduleModel.section_id,
                ),
            )
            .join(
                TimeSlotModel,
                and_(
                    TimeSlotModel.tenant_id == SectionScheduleModel.tenant_id,
                    TimeSlotModel.id == SectionScheduleModel.time_slot_id,
                ),
            )
            .where(
                and_(
                    SectionScheduleModel.tenant_id == tenant_id,
                    InstructorAssignmentModel.instructor_id == instructor_id,
                    SectionScheduleModel.day_of_week == day_of_week,
                    TimeSlotModel.start_time < end_time,
                    TimeSlotModel.end_time > start_time,
                )
            )
        )
        if exclude_section_id is not None:
            query = query.where(SectionScheduleModel.section_id != exclude_section_id)

        rows = self.db.execute(query).all()
        return [
            {
                "section_id": row[0],
                "day_of_week": str(row[1]),
                "start_time": _time_to_str(row[2]),
                "end_time": _time_to_str(row[3]),
            }
            for row in rows
        ]

    async def create_course_section(
        self,
        tenant_id: int,
        request: CourseSectionCreateSchema,
        actor_id: str,
    ) -> CourseSectionReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        SchedulingRules.validate_section_capacity(request.max_capacity)
        self._load_course_placeholder(tenant_id, request.course_id)
        self._validate_term_exists(tenant_id, request.term_id)

        section = CourseSectionModel(
            tenant_id=tenant_id,
            course_id=request.course_id,
            term_id=request.term_id,
            section_code=request.section_code,
            instructor_id=request.instructor_id,
            max_capacity=request.max_capacity,
            status=SectionStatus.PLANNED,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            version=1,
        )
        self.db.add(section)
        self.db.flush()
        self.db.refresh(section)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create section due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "section", "created"),
            f"/internal/scheduling/sections/{section.id}",
            {"section_id": section.id, "course_id": request.course_id, "term_id": request.term_id},
            tenant_id,
        )
        return CourseSectionReadSchema.model_validate(section)

    async def schedule_section(
        self,
        tenant_id: int,
        section_id: int,
        request: SectionScheduleCreateSchema,
        actor_id: str,
    ) -> SectionScheduleReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        section = self._load_course_section(tenant_id, section_id)
        if section.status == SectionStatus.CANCELLED:
            raise DomainValidationError("cancelled section cannot be scheduled")

        slot = self._load_time_slot(tenant_id, request.time_slot_id)
        classroom = self._load_classroom(tenant_id, request.classroom_id)

        SchedulingRules.validate_room_capacity(
            section_capacity=section.max_capacity,
            room_capacity=classroom.capacity,
        )

        room_conflict = self._get_room_conflict(
            tenant_id=tenant_id,
            classroom_id=request.classroom_id,
            time_slot_id=request.time_slot_id,
            day_of_week=request.day_of_week,
            exclude_section_id=section_id,
        )
        SchedulingRules.validate_no_room_conflict(
            room_conflict,
            classroom_id=request.classroom_id,
            day_of_week=request.day_of_week.value,
        )

        instructor_ids = [
            row[0]
            for row in self.db.execute(
                select(InstructorAssignmentModel.instructor_id).where(
                    and_(
                        InstructorAssignmentModel.tenant_id == tenant_id,
                        InstructorAssignmentModel.section_id == section_id,
                    )
                )
            ).all()
        ]
        if section.instructor_id and section.instructor_id not in instructor_ids:
            instructor_ids.append(section.instructor_id)

        for instructor_id in instructor_ids:
            conflicts = self._find_instructor_conflicts(
                tenant_id=tenant_id,
                instructor_id=instructor_id,
                day_of_week=request.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                exclude_section_id=section_id,
            )
            SchedulingRules.validate_no_instructor_conflict(
                conflicts,
                instructor_id=instructor_id,
                day_of_week=request.day_of_week.value,
            )

        existing_schedule = self._load_section_schedule(tenant_id, section_id)
        if existing_schedule is not None:
            raise DomainValidationError("section already has a schedule; use reschedule endpoint")

        schedule = SectionScheduleModel(
            tenant_id=tenant_id,
            section_id=section_id,
            time_slot_id=request.time_slot_id,
            classroom_id=request.classroom_id,
            day_of_week=request.day_of_week,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            version=1,
        )
        self.db.add(schedule)

        section.status = SectionStatus.SCHEDULED
        section.updated_at = _utc_now()
        section.version += 1

        self.db.flush()
        self.db.refresh(schedule)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to schedule section due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "section", "scheduled"),
            f"/internal/scheduling/sections/{section_id}/schedule",
            {
                "section_id": section_id,
                "time_slot_id": request.time_slot_id,
                "classroom_id": request.classroom_id,
                "day_of_week": request.day_of_week.value,
            },
            tenant_id,
        )
        return SectionScheduleReadSchema.model_validate(schedule)

    async def assign_instructor(
        self,
        tenant_id: int,
        section_id: int,
        request: InstructorAssignmentSchema,
        actor_id: str,
    ) -> dict:
        tenant_id = validate_tenant_id_provided(tenant_id)
        section = self._load_course_section(tenant_id, section_id)

        assignment = InstructorAssignmentModel(
            tenant_id=tenant_id,
            section_id=section_id,
            instructor_id=request.instructor_id,
            role=request.role,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        self.db.add(assignment)

        if section.instructor_id is None or request.role.value == "primary":
            section.instructor_id = request.instructor_id
            section.updated_at = _utc_now()
            section.version += 1

        self.db.flush()
        self.db.refresh(assignment)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to assign instructor due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "instructor_assignment", "created"),
            f"/internal/scheduling/sections/{section_id}/instructors",
            {
                "section_id": section_id,
                "instructor_id": request.instructor_id,
                "role": request.role.value,
            },
            tenant_id,
        )

        return {
            "id": assignment.id,
            "tenant_id": assignment.tenant_id,
            "section_id": assignment.section_id,
            "instructor_id": assignment.instructor_id,
            "role": assignment.role.value,
        }

    async def reschedule_section(
        self,
        tenant_id: int,
        section_id: int,
        request: SectionRescheduleSchema,
        actor_id: str,
    ) -> SectionScheduleReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        section = self._load_course_section(tenant_id, section_id)
        schedule = self._load_section_schedule(tenant_id, section_id)
        assert_resource_belongs_to_tenant(schedule, tenant_id, resource_name="Section schedule", resource_id=section_id)
        validate_version_match(schedule.version, request.expected_version)

        slot = self._load_time_slot(tenant_id, request.time_slot_id)
        classroom = self._load_classroom(tenant_id, request.classroom_id)
        SchedulingRules.validate_room_capacity(section_capacity=section.max_capacity, room_capacity=classroom.capacity)

        room_conflict = self._get_room_conflict(
            tenant_id=tenant_id,
            classroom_id=request.classroom_id,
            time_slot_id=request.time_slot_id,
            day_of_week=request.day_of_week,
            exclude_section_id=section_id,
        )
        SchedulingRules.validate_no_room_conflict(
            room_conflict,
            classroom_id=request.classroom_id,
            day_of_week=request.day_of_week.value,
        )

        instructor_ids = [
            row[0]
            for row in self.db.execute(
                select(InstructorAssignmentModel.instructor_id).where(
                    and_(
                        InstructorAssignmentModel.tenant_id == tenant_id,
                        InstructorAssignmentModel.section_id == section_id,
                    )
                )
            ).all()
        ]
        if section.instructor_id and section.instructor_id not in instructor_ids:
            instructor_ids.append(section.instructor_id)

        for instructor_id in instructor_ids:
            conflicts = self._find_instructor_conflicts(
                tenant_id=tenant_id,
                instructor_id=instructor_id,
                day_of_week=request.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                exclude_section_id=section_id,
            )
            SchedulingRules.validate_no_instructor_conflict(
                conflicts,
                instructor_id=instructor_id,
                day_of_week=request.day_of_week.value,
            )

        schedule.time_slot_id = request.time_slot_id
        schedule.classroom_id = request.classroom_id
        schedule.day_of_week = request.day_of_week
        schedule.updated_at = _utc_now()
        schedule.version += 1

        section.status = SectionStatus.SCHEDULED
        section.updated_at = _utc_now()
        section.version += 1

        self.db.flush()
        self.db.refresh(schedule)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to reschedule section due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "section", "rescheduled"),
            f"/internal/scheduling/sections/{section_id}/reschedule",
            {
                "section_id": section_id,
                "time_slot_id": request.time_slot_id,
                "classroom_id": request.classroom_id,
                "day_of_week": request.day_of_week.value,
                "version": schedule.version,
            },
            tenant_id,
        )

        return SectionScheduleReadSchema.model_validate(schedule)

    async def cancel_section(
        self,
        tenant_id: int,
        section_id: int,
        request: SectionCancelSchema,
        actor_id: str,
    ) -> CourseSectionReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        section = self._load_course_section(tenant_id, section_id)
        validate_version_match(section.version, request.expected_version)

        section.status = SectionStatus.CANCELLED
        section.updated_at = _utc_now()
        section.version += 1

        self.db.flush()
        self.db.refresh(section)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to cancel section due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "section", "cancelled"),
            f"/internal/scheduling/sections/{section_id}/cancel",
            {
                "section_id": section_id,
                "version": section.version,
            },
            tenant_id,
        )

        return CourseSectionReadSchema.model_validate(section)

    async def get_student_schedule(
        self,
        tenant_id: int,
        *,
        student_id: int,
    ) -> list[StudentScheduleItemSchema]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(student, tenant_id, resource_name="Student profile", resource_id=student_id)

        rows = self.db.execute(
            select(
                CourseSectionModel.id,
                CourseSectionModel.course_id,
                CourseSectionModel.term_id,
                SectionScheduleModel.day_of_week,
                TimeSlotModel.start_time,
                TimeSlotModel.end_time,
                ClassroomModel.id,
                ClassroomModel.name,
            )
            .join(
                EnrollmentModel,
                and_(
                    EnrollmentModel.tenant_id == CourseSectionModel.tenant_id,
                    EnrollmentModel.course_id == CourseSectionModel.course_id,
                    EnrollmentModel.term_id == CourseSectionModel.term_id,
                ),
            )
            .join(
                SectionScheduleModel,
                and_(
                    SectionScheduleModel.tenant_id == CourseSectionModel.tenant_id,
                    SectionScheduleModel.section_id == CourseSectionModel.id,
                ),
            )
            .join(
                TimeSlotModel,
                and_(
                    TimeSlotModel.tenant_id == SectionScheduleModel.tenant_id,
                    TimeSlotModel.id == SectionScheduleModel.time_slot_id,
                ),
            )
            .join(
                ClassroomModel,
                and_(
                    ClassroomModel.tenant_id == SectionScheduleModel.tenant_id,
                    ClassroomModel.id == SectionScheduleModel.classroom_id,
                ),
            )
            .where(
                and_(
                    EnrollmentModel.tenant_id == tenant_id,
                    EnrollmentModel.student_profile_id == student_id,
                    EnrollmentModel.enrollment_status.in_(
                        (
                            EnrollmentStatus.ENROLLED,
                            EnrollmentStatus.PENDING,
                            EnrollmentStatus.WAITLIST,
                            EnrollmentStatus.SUSPENDED,
                        )
                    ),
                    CourseSectionModel.status == SectionStatus.SCHEDULED,
                )
            )
            .order_by(CourseSectionModel.term_id, SectionScheduleModel.day_of_week, TimeSlotModel.start_time)
        ).all()

        return [
            StudentScheduleItemSchema(
                student_profile_id=student_id,
                section_id=row[0],
                course_id=row[1],
                term_id=row[2],
                day_of_week=row[3],
                start_time=_time_to_str(row[4]),
                end_time=_time_to_str(row[5]),
                classroom_id=row[6],
                classroom_name=row[7],
            )
            for row in rows
        ]

    async def get_instructor_schedule(
        self,
        tenant_id: int,
        *,
        instructor_id: str,
    ) -> list[InstructorScheduleItemSchema]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        rows = self.db.execute(
            select(
                CourseSectionModel.id,
                CourseSectionModel.course_id,
                CourseSectionModel.term_id,
                SectionScheduleModel.day_of_week,
                TimeSlotModel.start_time,
                TimeSlotModel.end_time,
                ClassroomModel.id,
                ClassroomModel.name,
            )
            .join(
                InstructorAssignmentModel,
                and_(
                    InstructorAssignmentModel.tenant_id == CourseSectionModel.tenant_id,
                    InstructorAssignmentModel.section_id == CourseSectionModel.id,
                ),
            )
            .join(
                SectionScheduleModel,
                and_(
                    SectionScheduleModel.tenant_id == CourseSectionModel.tenant_id,
                    SectionScheduleModel.section_id == CourseSectionModel.id,
                ),
            )
            .join(
                TimeSlotModel,
                and_(
                    TimeSlotModel.tenant_id == SectionScheduleModel.tenant_id,
                    TimeSlotModel.id == SectionScheduleModel.time_slot_id,
                ),
            )
            .join(
                ClassroomModel,
                and_(
                    ClassroomModel.tenant_id == SectionScheduleModel.tenant_id,
                    ClassroomModel.id == SectionScheduleModel.classroom_id,
                ),
            )
            .where(
                and_(
                    InstructorAssignmentModel.tenant_id == tenant_id,
                    InstructorAssignmentModel.instructor_id == instructor_id,
                    CourseSectionModel.status == SectionStatus.SCHEDULED,
                )
            )
            .order_by(CourseSectionModel.term_id, SectionScheduleModel.day_of_week, TimeSlotModel.start_time)
        ).all()

        return [
            InstructorScheduleItemSchema(
                instructor_id=instructor_id,
                section_id=row[0],
                course_id=row[1],
                term_id=row[2],
                day_of_week=row[3],
                start_time=_time_to_str(row[4]),
                end_time=_time_to_str(row[5]),
                classroom_id=row[6],
                classroom_name=row[7],
            )
            for row in rows
        ]

    async def get_room_schedule(
        self,
        tenant_id: int,
        *,
        classroom_id: int,
    ) -> list[RoomScheduleItemSchema]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_classroom(tenant_id, classroom_id)

        rows = self.db.execute(
            select(
                SectionScheduleModel.classroom_id,
                CourseSectionModel.id,
                CourseSectionModel.course_id,
                CourseSectionModel.term_id,
                SectionScheduleModel.day_of_week,
                TimeSlotModel.start_time,
                TimeSlotModel.end_time,
                CourseSectionModel.instructor_id,
            )
            .join(
                CourseSectionModel,
                and_(
                    CourseSectionModel.tenant_id == SectionScheduleModel.tenant_id,
                    CourseSectionModel.id == SectionScheduleModel.section_id,
                ),
            )
            .join(
                TimeSlotModel,
                and_(
                    TimeSlotModel.tenant_id == SectionScheduleModel.tenant_id,
                    TimeSlotModel.id == SectionScheduleModel.time_slot_id,
                ),
            )
            .where(
                and_(
                    SectionScheduleModel.tenant_id == tenant_id,
                    SectionScheduleModel.classroom_id == classroom_id,
                    CourseSectionModel.status == SectionStatus.SCHEDULED,
                )
            )
            .order_by(CourseSectionModel.term_id, SectionScheduleModel.day_of_week, TimeSlotModel.start_time)
        ).all()

        return [
            RoomScheduleItemSchema(
                classroom_id=row[0],
                section_id=row[1],
                course_id=row[2],
                term_id=row[3],
                day_of_week=row[4],
                start_time=_time_to_str(row[5]),
                end_time=_time_to_str(row[6]),
                instructor_id=row[7],
            )
            for row in rows
        ]

    async def detect_schedule_conflicts(
        self,
        tenant_id: int,
        *,
        section_id: int,
        time_slot_id: int,
        classroom_id: int,
        day_of_week: DayOfWeek,
    ) -> ConflictReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        section = self._load_course_section(tenant_id, section_id)
        slot = self._load_time_slot(tenant_id, time_slot_id)

        room_conflict = self._get_room_conflict(
            tenant_id=tenant_id,
            classroom_id=classroom_id,
            time_slot_id=time_slot_id,
            day_of_week=day_of_week,
            exclude_section_id=section_id,
        )

        instructor_conflicts: list[dict] = []
        instructor_ids = [
            row[0]
            for row in self.db.execute(
                select(InstructorAssignmentModel.instructor_id).where(
                    and_(
                        InstructorAssignmentModel.tenant_id == tenant_id,
                        InstructorAssignmentModel.section_id == section_id,
                    )
                )
            ).all()
        ]
        if section.instructor_id and section.instructor_id not in instructor_ids:
            instructor_ids.append(section.instructor_id)

        for instructor_id in instructor_ids:
            instructor_conflicts.extend(
                self._find_instructor_conflicts(
                    tenant_id=tenant_id,
                    instructor_id=instructor_id,
                    day_of_week=day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    exclude_section_id=section_id,
                )
            )

        return ConflictReportSchema(
            has_room_conflict=room_conflict is not None,
            room_conflict_section_id=room_conflict.section_id if room_conflict is not None else None,
            instructor_conflicts=instructor_conflicts,
        )
