from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
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
from app.modules.billing.service import assert_billing_write_allowed
from app.modules.courses.models import CourseModel
from app.modules.enrollments.models import EnrollmentModel, EnrollmentStatus
from app.modules.scheduling.business_rules import SchedulingRules
from app.modules.scheduling.models import (
    ClassroomModel,
    CourseSectionModel,
    DayOfWeek,
    DisciplineModel,
    InstructorAssignmentModel,
    LessonAttendanceModel,
    LessonInstanceModel,
    LessonTopicModel,
    LessonStatus,
    SectionScheduleModel,
    SectionStatus,
    StudentTopicProgressModel,
    TimeSlotModel,
)
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
    SchedulingConsistencyIssueSchema,
    SchedulingConsistencyReportSchema,
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

    def _load_lesson_instance(self, tenant_id: int, lesson_instance_id: int) -> LessonInstanceModel:
        lesson = self.db.execute(
            select(LessonInstanceModel).where(
                and_(
                    LessonInstanceModel.id == lesson_instance_id,
                    LessonInstanceModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            lesson,
            tenant_id,
            resource_name="Lesson instance",
            resource_id=lesson_instance_id,
        )
        return lesson

    def _load_discipline(self, tenant_id: int, discipline_id: int) -> DisciplineModel:
        discipline = self.db.execute(
            select(DisciplineModel).where(
                and_(
                    DisciplineModel.id == discipline_id,
                    DisciplineModel.tenant_id == tenant_id,
                    DisciplineModel.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            discipline,
            tenant_id,
            resource_name="Discipline",
            resource_id=discipline_id,
        )
        return discipline

    def _load_lesson_topic(self, tenant_id: int, topic_id: int) -> LessonTopicModel:
        topic = self.db.execute(
            select(LessonTopicModel).where(
                and_(
                    LessonTopicModel.id == topic_id,
                    LessonTopicModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(topic, tenant_id, resource_name="Lesson topic", resource_id=topic_id)
        return topic

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
        assert_billing_write_allowed(tenant_id, action="scheduling.section.create")
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

    async def create_lesson_instance(
        self,
        tenant_id: int,
        *,
        section_id: int,
        request: LessonInstanceCreateSchema,
        actor_id: str,
    ) -> LessonInstanceReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        assert_billing_write_allowed(tenant_id, action="scheduling.lesson.create")
        section = self._load_course_section(tenant_id, section_id)
        if section.status == SectionStatus.CANCELLED:
            raise DomainValidationError("cannot create lessons for cancelled section")

        lesson = LessonInstanceModel(
            tenant_id=tenant_id,
            section_id=section_id,
            scheduled_date=request.scheduled_date,
            actual_date=None,
            topic_title=request.topic_title,
            status=LessonStatus.PLANNED,
            notes=request.notes,
            metadata_json=request.metadata_json,
            created_by=actor_id,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            version=1,
        )
        self.db.add(lesson)
        self.db.flush()
        self.db.refresh(lesson)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create lesson instance due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "lesson_instance", "created"),
            f"/internal/scheduling/sections/{section_id}/lessons/{lesson.id}",
            {
                "section_id": section_id,
                "lesson_instance_id": lesson.id,
                "scheduled_date": str(lesson.scheduled_date),
                "topic_title": lesson.topic_title,
            },
            tenant_id,
        )
        return LessonInstanceReadSchema.model_validate(lesson)

    async def list_lesson_instances(
        self,
        tenant_id: int,
        *,
        section_id: int,
        page: int,
        page_size: int,
        status: LessonStatus | None = None,
    ) -> LessonInstanceListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_course_section(tenant_id, section_id)

        filters = [
            LessonInstanceModel.tenant_id == tenant_id,
            LessonInstanceModel.section_id == section_id,
        ]
        if status is not None:
            filters.append(LessonInstanceModel.status == status)

        total = self.db.execute(
            select(func.count()).select_from(LessonInstanceModel).where(and_(*filters))
        ).scalar_one()

        rows = self.db.execute(
            select(LessonInstanceModel)
            .where(and_(*filters))
            .order_by(LessonInstanceModel.scheduled_date.desc(), LessonInstanceModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return LessonInstanceListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[LessonInstanceReadSchema.model_validate(row) for row in rows],
        )

    async def upsert_lesson_attendance(
        self,
        tenant_id: int,
        *,
        lesson_instance_id: int,
        request: LessonAttendanceUpsertSchema,
        actor_id: str,
    ) -> LessonAttendanceReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        lesson = self._load_lesson_instance(tenant_id, lesson_instance_id)

        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == request.student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            student,
            tenant_id,
            resource_name="Student profile",
            resource_id=request.student_profile_id,
        )

        attendance = self.db.execute(
            select(LessonAttendanceModel).where(
                and_(
                    LessonAttendanceModel.tenant_id == tenant_id,
                    LessonAttendanceModel.lesson_instance_id == lesson_instance_id,
                    LessonAttendanceModel.student_profile_id == request.student_profile_id,
                )
            )
        ).scalar_one_or_none()

        now = _utc_now()
        if attendance is None:
            attendance = LessonAttendanceModel(
                tenant_id=tenant_id,
                lesson_instance_id=lesson_instance_id,
                student_profile_id=request.student_profile_id,
                attendance_status=request.attendance_status,
                marked_by=actor_id,
                marked_at=now,
                created_at=now,
                updated_at=now,
                version=1,
            )
            self.db.add(attendance)
        else:
            attendance.attendance_status = request.attendance_status
            attendance.marked_by = actor_id
            attendance.marked_at = now
            attendance.updated_at = now
            attendance.version += 1

        if lesson.status == LessonStatus.PLANNED:
            lesson.status = LessonStatus.COMPLETED
            lesson.actual_date = lesson.actual_date or now.date()
            lesson.updated_at = now
            lesson.version += 1

        self.db.flush()
        self.db.refresh(attendance)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to record attendance due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "lesson_attendance", "upserted"),
            f"/internal/scheduling/lessons/{lesson_instance_id}/attendance/{attendance.id}",
            {
                "lesson_instance_id": lesson_instance_id,
                "student_profile_id": request.student_profile_id,
                "attendance_status": request.attendance_status.value,
            },
            tenant_id,
        )
        return LessonAttendanceReadSchema.model_validate(attendance)

    async def list_lesson_attendance(
        self,
        tenant_id: int,
        *,
        lesson_instance_id: int,
    ) -> LessonAttendanceListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_lesson_instance(tenant_id, lesson_instance_id)

        rows = self.db.execute(
            select(LessonAttendanceModel)
            .where(
                and_(
                    LessonAttendanceModel.tenant_id == tenant_id,
                    LessonAttendanceModel.lesson_instance_id == lesson_instance_id,
                )
            )
            .order_by(LessonAttendanceModel.id.asc())
        ).scalars().all()

        return LessonAttendanceListResponseSchema(
            total=len(rows),
            items=[LessonAttendanceReadSchema.model_validate(row) for row in rows],
        )

    async def create_discipline(
        self,
        tenant_id: int,
        *,
        request: DisciplineCreateSchema,
        actor_id: str,
    ) -> DisciplineReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        assert_billing_write_allowed(tenant_id, action="scheduling.discipline.create")

        discipline = DisciplineModel(
            tenant_id=tenant_id,
            unique_code=request.unique_code,
            title=request.title,
            description=request.description,
            credits=request.credits,
            prerequisites_json=request.prerequisites_json,
            learning_outcomes_json=request.learning_outcomes_json,
            is_active=True,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            version=1,
        )
        self.db.add(discipline)
        self.db.flush()
        self.db.refresh(discipline)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create discipline due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "discipline", "created"),
            f"/internal/scheduling/disciplines/{discipline.id}",
            {
                "discipline_id": discipline.id,
                "unique_code": discipline.unique_code,
            },
            tenant_id,
        )
        return DisciplineReadSchema.model_validate(discipline)

    async def list_disciplines(
        self,
        tenant_id: int,
        *,
        include_inactive: bool = False,
    ) -> DisciplineListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [DisciplineModel.tenant_id == tenant_id]
        if not include_inactive:
            filters.append(DisciplineModel.is_active.is_(True))

        rows = self.db.execute(
            select(DisciplineModel)
            .where(and_(*filters))
            .order_by(DisciplineModel.title.asc(), DisciplineModel.id.asc())
        ).scalars().all()

        return DisciplineListResponseSchema(
            total=len(rows),
            items=[DisciplineReadSchema.model_validate(row) for row in rows],
        )

    async def create_lesson_topic(
        self,
        tenant_id: int,
        *,
        discipline_id: int,
        request: LessonTopicCreateSchema,
        actor_id: str,
    ) -> LessonTopicReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        assert_billing_write_allowed(tenant_id, action="scheduling.topic.create")
        self._load_discipline(tenant_id, discipline_id)

        topic = LessonTopicModel(
            tenant_id=tenant_id,
            discipline_id=discipline_id,
            module_num=request.module_num,
            topic_num=request.topic_num,
            title=request.title,
            description=request.description,
            difficulty_level=request.difficulty_level,
            recommended_materials_json=request.recommended_materials_json,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            version=1,
        )
        self.db.add(topic)
        self.db.flush()
        self.db.refresh(topic)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create lesson topic due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "lesson_topic", "created"),
            f"/internal/scheduling/disciplines/{discipline_id}/topics/{topic.id}",
            {
                "discipline_id": discipline_id,
                "topic_id": topic.id,
                "module_num": topic.module_num,
                "topic_num": topic.topic_num,
            },
            tenant_id,
        )
        return LessonTopicReadSchema.model_validate(topic)

    async def list_lesson_topics(
        self,
        tenant_id: int,
        *,
        discipline_id: int,
    ) -> LessonTopicListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_discipline(tenant_id, discipline_id)

        rows = self.db.execute(
            select(LessonTopicModel)
            .where(
                and_(
                    LessonTopicModel.tenant_id == tenant_id,
                    LessonTopicModel.discipline_id == discipline_id,
                )
            )
            .order_by(LessonTopicModel.module_num.asc(), LessonTopicModel.topic_num.asc(), LessonTopicModel.id.asc())
        ).scalars().all()

        return LessonTopicListResponseSchema(
            total=len(rows),
            items=[LessonTopicReadSchema.model_validate(row) for row in rows],
        )

    async def upsert_student_topic_progress(
        self,
        tenant_id: int,
        *,
        topic_id: int,
        student_profile_id: int,
        request: StudentTopicProgressUpsertSchema,
        actor_id: str,
    ) -> StudentTopicProgressReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            student,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )

        topic = self._load_lesson_topic(tenant_id, topic_id)
        if topic.discipline_id != request.discipline_id:
            raise DomainValidationError(
                "Topic does not belong to provided discipline"
            )

        self._load_discipline(tenant_id, request.discipline_id)

        progress = self.db.execute(
            select(StudentTopicProgressModel).where(
                and_(
                    StudentTopicProgressModel.tenant_id == tenant_id,
                    StudentTopicProgressModel.student_profile_id == student_profile_id,
                    StudentTopicProgressModel.topic_id == topic_id,
                )
            )
        ).scalar_one_or_none()

        now = _utc_now()
        if progress is None:
            progress = StudentTopicProgressModel(
                tenant_id=tenant_id,
                student_profile_id=student_profile_id,
                topic_id=topic_id,
                discipline_id=request.discipline_id,
                first_seen_date=request.first_seen_date,
                last_reviewed_date=request.last_reviewed_date,
                status=request.status,
                materials_opened=request.materials_opened,
                materials_completed=request.materials_completed,
                quiz_attempts=request.quiz_attempts,
                quiz_best_score=request.quiz_best_score,
                created_at=now,
                updated_at=now,
                version=1,
            )
            self.db.add(progress)
        else:
            progress.discipline_id = request.discipline_id
            progress.first_seen_date = request.first_seen_date
            progress.last_reviewed_date = request.last_reviewed_date
            progress.status = request.status
            progress.materials_opened = request.materials_opened
            progress.materials_completed = request.materials_completed
            progress.quiz_attempts = request.quiz_attempts
            progress.quiz_best_score = request.quiz_best_score
            progress.updated_at = now
            progress.version += 1

        self.db.flush()
        self.db.refresh(progress)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to upsert student topic progress due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("scheduling", "student_topic_progress", "upserted"),
            f"/internal/scheduling/topics/{topic_id}/progress/{student_profile_id}",
            {
                "topic_id": topic_id,
                "student_profile_id": student_profile_id,
                "status": request.status.value,
            },
            tenant_id,
        )

        return StudentTopicProgressReadSchema.model_validate(progress)

    async def list_student_topic_progress(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        discipline_id: int | None = None,
    ) -> StudentTopicProgressListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            student,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )

        filters = [
            StudentTopicProgressModel.tenant_id == tenant_id,
            StudentTopicProgressModel.student_profile_id == student_profile_id,
        ]
        if discipline_id is not None:
            self._load_discipline(tenant_id, discipline_id)
            filters.append(StudentTopicProgressModel.discipline_id == discipline_id)

        rows = self.db.execute(
            select(StudentTopicProgressModel)
            .where(and_(*filters))
            .order_by(StudentTopicProgressModel.updated_at.desc(), StudentTopicProgressModel.id.desc())
        ).scalars().all()

        return StudentTopicProgressListResponseSchema(
            total=len(rows),
            items=[StudentTopicProgressReadSchema.model_validate(row) for row in rows],
        )

    async def list_tenant_scheduling_consistency_report(
        self, tenant_id: int
    ) -> SchedulingConsistencyReportSchema:
        validate_tenant_id_provided(tenant_id)
        issues: list[SchedulingConsistencyIssueSchema] = []

        # All non-cancelled sections
        sections = self.db.execute(
            select(CourseSectionModel).where(
                and_(
                    CourseSectionModel.tenant_id == tenant_id,
                    CourseSectionModel.status.in_(
                        [SectionStatus.PLANNED, SectionStatus.SCHEDULED]
                    ),
                )
            )
        ).scalars().all()
        section_ids = {s.id for s in sections}

        # Sections missing a schedule record
        scheduled_section_ids = set(
            self.db.execute(
                select(SectionScheduleModel.section_id).where(
                    SectionScheduleModel.tenant_id == tenant_id
                )
            ).scalars().all()
        )
        for sec in sections:
            if sec.id not in scheduled_section_ids:
                issues.append(
                    SchedulingConsistencyIssueSchema(
                        issue_type="section_without_schedule",
                        section_id=sec.id,
                    )
                )

        # Sections missing an instructor assignment
        assigned_section_ids = set(
            self.db.execute(
                select(InstructorAssignmentModel.section_id).where(
                    InstructorAssignmentModel.tenant_id == tenant_id
                )
            ).scalars().all()
        )
        for sec in sections:
            if sec.id not in assigned_section_ids:
                issues.append(
                    SchedulingConsistencyIssueSchema(
                        issue_type="section_without_instructor",
                        section_id=sec.id,
                    )
                )

        # Attendance records pointing to non-existent student profiles
        attendances = self.db.execute(
            select(LessonAttendanceModel).where(
                LessonAttendanceModel.tenant_id == tenant_id
            )
        ).scalars().all()

        student_ids = set(
            self.db.execute(
                select(StudentProfileModel.id).where(
                    StudentProfileModel.tenant_id == tenant_id
                )
            ).scalars().all()
        )
        for att in attendances:
            if att.student_profile_id not in student_ids:
                issues.append(
                    SchedulingConsistencyIssueSchema(
                        issue_type="attendance_orphaned_student",
                        lesson_attendance_id=att.id,
                        student_profile_id=att.student_profile_id,
                    )
                )

        return SchedulingConsistencyReportSchema(
            section_count=len(sections),
            attendance_count=len(attendances),
            issue_count=len(issues),
            issues=issues,
        )
