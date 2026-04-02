from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import and_, desc, func, select
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
from app.modules.audit.service import log_data_access_event
from app.modules.courses.models import CourseModel
from app.modules.enrollments.models import AcademicTermModel, EnrollmentModel
from app.modules.grades.business_rules import GradeLifecycleRules
from app.modules.grades.models import (
    GradeHistoryModel,
    GradeSubmissionModel,
    GradingScaleItemModel,
    GradingScaleModel,
)
from app.modules.grades.schemas import (
    GradeChangeSchema,
    GradeListResponseSchema,
    GradeReadSchema,
    GradeSubmitSchema,
    StudentTranscriptSchema,
    TranscriptItemSchema,
)
from app.modules.rbac.abac import (
    validate_grade_submission,
    validate_grade_modification,
    validate_grade_ownership,
)
from app.modules.students.models import StudentProfileModel
from app.platform.events.publisher import EventPublisher


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _audit(
    *,
    actor: str,
    action: str,
    path: str,
    entity: str,
    metadata: dict,
    tenant_id: int,
) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


class GradeLifecycleService:
    """Lifecycle service for grade submissions, changes, and transcripts."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _load_enrollment(self, tenant_id: int, enrollment_id: int) -> EnrollmentModel:
        enrollment = self.db.execute(
            select(EnrollmentModel).where(
                and_(
                    EnrollmentModel.id == enrollment_id,
                    EnrollmentModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            enrollment,
            tenant_id,
            resource_name="Enrollment",
            resource_id=enrollment_id,
        )
        return enrollment

    def _load_student(self, tenant_id: int, student_profile_id: int) -> StudentProfileModel:
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
        return student

    def _load_course(self, tenant_id: int, course_id: int) -> CourseModel:
        course = self.db.execute(select(CourseModel).where(CourseModel.id == course_id)).scalar_one_or_none()
        if course is None:
            raise TenantResourceNotFoundError(
                f"Course {course_id} not found or does not belong to tenant {tenant_id}"
            )
        raw_tenant = getattr(course, "tenant_id", None)
        if raw_tenant is not None:
            try:
                normalized = int(raw_tenant)
            except (TypeError, ValueError):
                raise TenantResourceNotFoundError(
                    f"Course {course_id} not found or does not belong to tenant {tenant_id}"
                ) from None
            if normalized != tenant_id:
                raise TenantResourceNotFoundError(
                    f"Course {course_id} not found or does not belong to tenant {tenant_id}"
                )
        return course

    def _load_grading_scale(self, tenant_id: int, grading_scale_id: int) -> GradingScaleModel:
        scale = self.db.execute(
            select(GradingScaleModel).where(
                and_(
                    GradingScaleModel.id == grading_scale_id,
                    GradingScaleModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            scale,
            tenant_id,
            resource_name="Grading scale",
            resource_id=grading_scale_id,
        )
        if not bool(scale.is_active):
            raise DomainValidationError(f"Grading scale {grading_scale_id} is not active")
        return scale

    def _load_scale_items(self, tenant_id: int, grading_scale_id: int) -> list[GradingScaleItemModel]:
        items = self.db.execute(
            select(GradingScaleItemModel)
            .where(
                and_(
                    GradingScaleItemModel.tenant_id == tenant_id,
                    GradingScaleItemModel.scale_id == grading_scale_id,
                )
            )
            .order_by(GradingScaleItemModel.max_percentage.desc(), GradingScaleItemModel.id)
        ).scalars().all()
        if not items:
            raise DomainValidationError(f"Grading scale {grading_scale_id} has no scale items")
        return items

    def _load_grade_submission(self, tenant_id: int, enrollment_id: int) -> GradeSubmissionModel | None:
        return self.db.execute(
            select(GradeSubmissionModel).where(
                and_(
                    GradeSubmissionModel.tenant_id == tenant_id,
                    GradeSubmissionModel.enrollment_id == enrollment_id,
                )
            )
        ).scalar_one_or_none()

    def _append_grade_history(
        self,
        *,
        tenant_id: int,
        enrollment_id: int,
        previous_grade_code: str | None,
        new_grade_code: str,
        previous_grade_points: Decimal | None,
        new_grade_points: Decimal,
        changed_by: str,
        reason: str | None,
        version: int,
    ) -> None:
        self.db.add(
            GradeHistoryModel(
                tenant_id=tenant_id,
                enrollment_id=enrollment_id,
                previous_grade_code=previous_grade_code,
                new_grade_code=new_grade_code,
                previous_grade_points=previous_grade_points,
                new_grade_points=new_grade_points,
                changed_by=changed_by,
                changed_at=_utc_now(),
                reason=reason,
                version=version,
            )
        )

    @staticmethod
    def _quantize(points: Decimal) -> Decimal:
        return points.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def submit_grade(
        self,
        tenant_id: int,
        request: GradeSubmitSchema,
        actor_id: str,
    ) -> GradeReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        enrollment = self._load_enrollment(tenant_id, request.enrollment_id)
        
        # ABAC: Verify actor is authorized to submit grades for this course
        self._load_course(tenant_id, enrollment.course_id)
        await validate_grade_submission(
            actor_id=actor_id,
            course_id=enrollment.course_id,
            tenant_id=tenant_id,
        )
        
        GradeLifecycleRules.validate_grade_submission_allowed(enrollment)

        existing = self._load_grade_submission(tenant_id, request.enrollment_id)
        if existing is not None:
            raise DomainValidationError(
                f"Grade already submitted for enrollment {request.enrollment_id}; use change_grade"
            )

        self._load_grading_scale(tenant_id, request.grading_scale_id)
        scale_items = self._load_scale_items(tenant_id, request.grading_scale_id)
        resolved_points = GradeLifecycleRules.validate_grade_points_match_scale(
            request.grade_code,
            scale_items,
            request.grade_points,
        )
        resolved_points = self._quantize(resolved_points)

        previous_grade_code = enrollment.grade_code
        previous_grade_points = enrollment.grade_points

        submission = GradeSubmissionModel(
            tenant_id=tenant_id,
            enrollment_id=request.enrollment_id,
            grade_code=request.grade_code,
            grade_points=resolved_points,
            grading_scale_id=request.grading_scale_id,
            submitted_by=actor_id,
            submitted_at=_utc_now(),
            metadata_json=request.metadata_json,
        )
        self.db.add(submission)
        self.db.flush()

        enrollment.grade_code = request.grade_code
        enrollment.grade_points = resolved_points
        enrollment.version += 1
        enrollment.updated_by = actor_id

        self._append_grade_history(
            tenant_id=tenant_id,
            enrollment_id=request.enrollment_id,
            previous_grade_code=previous_grade_code,
            new_grade_code=request.grade_code,
            previous_grade_points=previous_grade_points,
            new_grade_points=resolved_points,
            changed_by=actor_id,
            reason="initial_grade_submission",
            version=submission.version,
        )

        self.db.flush()
        self.db.refresh(submission)

        EventPublisher(db_session=self.db).publish_event(
            tenant_id=tenant_id,
            event_type="grade.submitted",
            aggregate_type="grade_submission",
            aggregate_id=submission.id,
            payload_json={
                "submission_id": submission.id,
                "enrollment_id": submission.enrollment_id,
                "student_profile_id": enrollment.student_profile_id,
                "grade_code": submission.grade_code,
                "grade_points": str(resolved_points),
                "submitted_by": actor_id,
            },
        )

        _audit(
            actor=actor_id,
            action=build_audit_action("grades", "grade", "submitted"),
            path=f"/internal/grades/enrollments/{request.enrollment_id}/submit",
            entity="grade",
            metadata={
                "resource_id": str(submission.id),
                "enrollment_id": request.enrollment_id,
                "grade_code": request.grade_code,
                "grade_points": str(resolved_points),
                "version": submission.version,
            },
            tenant_id=tenant_id,
        )
        log_data_access_event(
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource="grade",
            resource_id=submission.id,
            action="write",
            result="success",
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to submit grade due to constraint violation") from exc

        return GradeReadSchema.model_validate(submission)

    async def change_grade(
        self,
        tenant_id: int,
        request: GradeChangeSchema,
        actor_id: str,
    ) -> GradeReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        GradeLifecycleRules.validate_grade_change_allowed(actor_id)

        enrollment = self._load_enrollment(tenant_id, request.enrollment_id)
        GradeLifecycleRules.validate_grade_submission_allowed(enrollment)

        submission = self._load_grade_submission(tenant_id, request.enrollment_id)
        assert_resource_belongs_to_tenant(
            submission,
            tenant_id,
            resource_name="Grade submission",
            resource_id=request.enrollment_id,
        )
        
        # ABAC: Only original submitter or admin can modify grade
        await validate_grade_modification(
            actor_id=actor_id,
            grade_id=submission.id,
            submitted_by=submission.submitted_by,
            tenant_id=tenant_id,
        )

        validate_version_match(submission.version, request.expected_version)

        self._load_grading_scale(tenant_id, request.grading_scale_id)
        scale_items = self._load_scale_items(tenant_id, request.grading_scale_id)
        resolved_points = GradeLifecycleRules.validate_grade_points_match_scale(
            request.new_grade_code,
            scale_items,
            request.new_grade_points,
        )
        resolved_points = self._quantize(resolved_points)

        prev_code = submission.grade_code
        prev_points = submission.grade_points

        if prev_code == request.new_grade_code and Decimal(str(prev_points)) == resolved_points:
            raise DomainValidationError("grade change must modify grade_code or grade_points")

        submission.grade_code = request.new_grade_code
        submission.grade_points = resolved_points
        submission.grading_scale_id = request.grading_scale_id
        submission.submitted_by = actor_id
        submission.submitted_at = _utc_now()
        submission.metadata_json = request.metadata_json
        submission.version += 1

        enrollment.grade_code = request.new_grade_code
        enrollment.grade_points = resolved_points
        enrollment.version += 1
        enrollment.updated_by = actor_id

        self._append_grade_history(
            tenant_id=tenant_id,
            enrollment_id=request.enrollment_id,
            previous_grade_code=prev_code,
            new_grade_code=request.new_grade_code,
            previous_grade_points=prev_points,
            new_grade_points=resolved_points,
            changed_by=actor_id,
            reason=request.reason or "grade_change",
            version=submission.version,
        )

        self.db.flush()
        self.db.refresh(submission)

        _audit(
            actor=actor_id,
            action=build_audit_action("grades", "grade", "changed"),
            path=f"/internal/grades/enrollments/{request.enrollment_id}/change",
            entity="grade",
            metadata={
                "resource_id": str(submission.id),
                "enrollment_id": request.enrollment_id,
                "previous_grade_code": prev_code,
                "new_grade_code": request.new_grade_code,
                "version": submission.version,
            },
            tenant_id=tenant_id,
        )
        log_data_access_event(
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource="grade",
            resource_id=submission.id,
            action="update",
            result="success",
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to change grade due to constraint violation") from exc

        return GradeReadSchema.model_validate(submission)

    async def get_enrollment_grade(
        self,
        tenant_id: int,
        enrollment_id: int,
        actor_id: str | None = None,
    ) -> GradeReadSchema | None:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_enrollment(tenant_id, enrollment_id)

        grade = self._load_grade_submission(tenant_id, enrollment_id)
        if grade is None:
            return None
        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="grade",
                resource_id=grade.id,
                action="read",
                result="success",
            )
        return GradeReadSchema.model_validate(grade)

    async def list_course_grades(
        self,
        tenant_id: int,
        *,
        course_id: int,
        term_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
        actor_id: str | None = None,
    ) -> GradeListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_course(tenant_id, course_id)
        
        # ABAC: Verify actor is authorized to view grades for this course
        if actor_id:
            await validate_grade_ownership(
                actor_id=actor_id,
                grade_id=0,  # Not checking specific grade, just course access
                course_id=course_id,
                student_id="",
                submitted_by="",
                tenant_id=tenant_id,
            )

        filters = [
            EnrollmentModel.tenant_id == tenant_id,
            EnrollmentModel.course_id == course_id,
        ]
        if term_id is not None:
            filters.append(EnrollmentModel.term_id == term_id)

        total = self.db.execute(
            select(func.count())
            .select_from(GradeSubmissionModel)
            .join(
                EnrollmentModel,
                and_(
                    GradeSubmissionModel.tenant_id == EnrollmentModel.tenant_id,
                    GradeSubmissionModel.enrollment_id == EnrollmentModel.id,
                ),
            )
            .where(and_(*filters))
        ).scalar_one()

        items = self.db.execute(
            select(GradeSubmissionModel)
            .join(
                EnrollmentModel,
                and_(
                    GradeSubmissionModel.tenant_id == EnrollmentModel.tenant_id,
                    GradeSubmissionModel.enrollment_id == EnrollmentModel.id,
                ),
            )
            .where(and_(*filters))
            .order_by(desc(GradeSubmissionModel.submitted_at), desc(GradeSubmissionModel.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="grade",
                resource_id=course_id,
                action="read",
                result="success",
            )

        return GradeListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[GradeReadSchema.model_validate(item) for item in items],
        )

    async def calculate_student_gpa(self, tenant_id: int, *, student_profile_id: int) -> Decimal | None:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_student(tenant_id, student_profile_id)

        rows = self.db.execute(
            select(EnrollmentModel.grade_points, CourseModel.credits, CourseModel.tenant_id)
            .join(CourseModel, CourseModel.id == EnrollmentModel.course_id)
            .where(
                and_(
                    EnrollmentModel.tenant_id == tenant_id,
                    EnrollmentModel.student_profile_id == student_profile_id,
                    EnrollmentModel.grade_points.is_not(None),
                )
            )
        ).all()

        weighted_sum = Decimal("0")
        credits_sum = Decimal("0")
        for grade_points, credits, course_tenant in rows:
            if course_tenant is not None:
                try:
                    normalized_course_tenant = int(course_tenant)
                except (TypeError, ValueError):
                    continue
                if normalized_course_tenant != tenant_id:
                    continue

            if grade_points is None:
                continue
            credits_value = Decimal(str(credits or 0))
            if credits_value <= 0:
                continue
            weighted_sum += Decimal(str(grade_points)) * credits_value
            credits_sum += credits_value

        if credits_sum == 0:
            return None

        gpa = weighted_sum / credits_sum
        return self._quantize(gpa)

    async def get_student_transcript(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
    ) -> StudentTranscriptSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_student(tenant_id, student_profile_id)

        rows = self.db.execute(
            select(
                EnrollmentModel.term_id,
                AcademicTermModel.term_code,
                AcademicTermModel.term_name,
                EnrollmentModel.course_id,
                CourseModel.course_code,
                CourseModel.title,
                CourseModel.credits,
                CourseModel.tenant_id,
                EnrollmentModel.grade_code,
                EnrollmentModel.grade_points,
                AcademicTermModel.start_date,
            )
            .join(
                AcademicTermModel,
                and_(
                    AcademicTermModel.id == EnrollmentModel.term_id,
                    AcademicTermModel.tenant_id == EnrollmentModel.tenant_id,
                ),
                isouter=True,
            )
            .join(CourseModel, CourseModel.id == EnrollmentModel.course_id)
            .where(
                and_(
                    EnrollmentModel.tenant_id == tenant_id,
                    EnrollmentModel.student_profile_id == student_profile_id,
                )
            )
            .order_by(AcademicTermModel.start_date, CourseModel.course_code, EnrollmentModel.id)
        ).all()

        items: list[TranscriptItemSchema] = []
        total_credits = 0
        for row in rows:
            (
                term_id,
                term_code,
                term_name,
                course_id,
                course_code,
                course_title,
                credits,
                course_tenant,
                grade_code,
                grade_points,
                _start_date,
            ) = row

            if course_tenant is not None:
                try:
                    normalized_course_tenant = int(course_tenant)
                except (TypeError, ValueError):
                    continue
                if normalized_course_tenant != tenant_id:
                    continue

            credits_value = int(credits or 0)
            total_credits += max(credits_value, 0)

            items.append(
                TranscriptItemSchema(
                    term_id=term_id,
                    term_code=term_code,
                    term_name=term_name,
                    course_id=course_id,
                    course_code=course_code,
                    course_title=course_title,
                    credits=credits_value,
                    grade_code=grade_code,
                    grade_points=grade_points,
                )
            )

        gpa = await self.calculate_student_gpa(tenant_id, student_profile_id=student_profile_id)

        return StudentTranscriptSchema(
            student_profile_id=student_profile_id,
            total_credits=total_credits,
            gpa=gpa,
            items=items,
        )
