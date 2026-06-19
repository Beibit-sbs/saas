from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import cast

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    MutationResult,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.audit.service import log_data_access_event
from app.modules.billing.service import assert_billing_write_allowed, assert_quota_with_increment
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
    GradeEnrollmentConsistencyIssueSchema,
    GradeEnrollmentConsistencyReportSchema,
    GradeChangeSchema,
    GradeListResponseSchema,
    GradeReadSchema,
    GradeSubmitSchema,
    GradingScaleCreateSchema,
    GradingScaleItemReadSchema,
    GradingScaleListResponseSchema,
    GradingScaleReadSchema,
    StudentTranscriptSchema,
    TranscriptItemSchema,
)
from datetime import timedelta
from app.modules.scheduling.models import CourseSectionModel, SectionStatus

from app.modules.rbac.abac import (
    validate_grade_submission,
    validate_grade_modification,
    validate_grade_ownership,
)
from app.modules.students.models import StudentProfileModel
from app.modules.usage.service import record_usage_event
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


# Institutional late-grade submission grace period after term end_date.
# Grades cannot be submitted after end_date + grace period.
_GRADE_SUBMISSION_GRACE_DAYS: int = 30


class GradeLifecycleService:
    """Lifecycle service for grade submissions, changes, and transcripts."""

    def __init__(self, db_session: Session):
        self.db = db_session

    @staticmethod
    def _derive_grade_risk_level(grade_points: Decimal | None) -> str | None:
        if grade_points is None:
            return None
        if grade_points <= Decimal("1.00"):
            return "high"
        if grade_points <= Decimal("2.00"):
            return "medium"
        return None

    def _load_enrollment(self, tenant_id: int, enrollment_id: int) -> EnrollmentModel:
        enrollment = self.db.execute(
            select(EnrollmentModel).where(
                and_(
                    EnrollmentModel.id == enrollment_id,
                    EnrollmentModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if enrollment is None:
            raise TenantResourceNotFoundError(
                f"Enrollment {enrollment_id} not found or does not belong to tenant {tenant_id}"
            )
        return enrollment

    def _check_term_submission_window_open(self, tenant_id: int, term_id: int) -> None:
        """Cross-entity guard: grades × academic_terms.end_date × utcnow().

        Grade submission is blocked when the term's end_date has passed beyond the
        institutional grace period (_GRADE_SUBMISSION_GRACE_DAYS). This prevents
        retroactive grade submission that would corrupt already-issued transcripts,
        distort financial aid calculations, and violate census-date integrity.

        Safe-skip when no term record found or end_date is None (not all deployments
        configure term end dates — no false-positive block).
        """
        term = self.db.execute(
            select(AcademicTermModel).where(
                and_(
                    AcademicTermModel.id == term_id,
                    AcademicTermModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if term is None or term.end_date is None:
            return
        deadline = term.end_date + timedelta(days=_GRADE_SUBMISSION_GRACE_DAYS)
        # Make deadline timezone-aware for comparison if needed
        now = _utc_now()
        if deadline.tzinfo is None:
            from datetime import timezone as _tz
            deadline = deadline.replace(tzinfo=_tz.utc)
        if now > deadline:
            raise DomainValidationError(
                f"Grade submission is locked: term {term_id} ended on "
                f"{term.end_date.date()} and the {_GRADE_SUBMISSION_GRACE_DAYS}-day "
                f"grade submission window has closed. "
                f"Use a formal grade correction workflow."
            )

    def _check_section_not_cancelled(self, tenant_id: int, enrollment_id: int) -> None:
        """Cross-entity guard: grades × enrollments.section_id × scheduling.section.status.

        Data-model enforcement for W78: grade submission is allowed only when enrollment
        is linked to a concrete section and that section is active for grading.
        """
        enrollment = self._load_enrollment(tenant_id, enrollment_id)
        if enrollment.section_id is None:
            raise DomainValidationError(
                f"Grade submission blocked: enrollment_id={enrollment_id} has no section_id. "
                "Enrollment-section linkage is required."
            )

        section = self.db.execute(
            select(CourseSectionModel).where(
                and_(
                    CourseSectionModel.tenant_id == tenant_id,
                    CourseSectionModel.id == enrollment.section_id,
                )
            )
        ).scalar_one_or_none()
        if section is None:
            raise DomainValidationError(
                f"Grade submission blocked: section_id={enrollment.section_id} not found for "
                f"tenant_id={tenant_id}. enrollment_id={enrollment_id}"
            )

        if section.course_id != enrollment.course_id or section.term_id != enrollment.term_id:
            raise DomainValidationError(
                "Grade submission blocked: enrollment-section mismatch. "
                f"enrollment_id={enrollment_id}, enrollment(course_id={enrollment.course_id}, term_id={enrollment.term_id}) "
                f"!= section(id={section.id}, course_id={section.course_id}, term_id={section.term_id})"
            )

        if section.status != SectionStatus.SCHEDULED:
            raise DomainValidationError(
                "Grade submission blocked: section is not active for grading. "
                f"section_id={section.id}, status={section.status}"
            )

    def _load_student(self, tenant_id: int, student_profile_id: int) -> StudentProfileModel:
        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if student is None:
            raise TenantResourceNotFoundError(
                f"Student profile {student_profile_id} not found or does not belong to tenant {tenant_id}"
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
        scale = cast(GradingScaleModel, scale)
        if not bool(scale.is_active):
            raise DomainValidationError(f"Grading scale {grading_scale_id} is not active")
        return scale

    def _load_scale_items(self, tenant_id: int, grading_scale_id: int) -> list[GradingScaleItemModel]:
        items = list(
            self.db.execute(
            select(GradingScaleItemModel)
            .where(
                and_(
                    GradingScaleItemModel.tenant_id == tenant_id,
                    GradingScaleItemModel.scale_id == grading_scale_id,
                )
            )
            .order_by(GradingScaleItemModel.max_percentage.desc(), GradingScaleItemModel.id)
        ).scalars().all()
        )
        if not items:
            raise DomainValidationError(f"Grading scale {grading_scale_id} has no scale items")
        return items

    @staticmethod
    def _scale_read_schema(
        scale: GradingScaleModel,
        items: list[GradingScaleItemModel],
    ) -> GradingScaleReadSchema:
        return GradingScaleReadSchema(
            id=scale.id,
            tenant_id=scale.tenant_id,
            name=scale.name,
            description=scale.description,
            is_active=bool(scale.is_active),
            items=[GradingScaleItemReadSchema.model_validate(item) for item in items],
        )

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
    ) -> MutationResult[GradeReadSchema]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        assert_billing_write_allowed(tenant_id, action="grades.submit")
        assert_quota_with_increment(tenant_id, "grades_submitted", increment=1)
        enrollment = self._load_enrollment(tenant_id, request.enrollment_id)

        # ABAC: Verify actor is authorized to submit grades for this course
        self._load_course(tenant_id, enrollment.course_id)
        await validate_grade_submission(
            actor_id=actor_id,
            course_id=enrollment.course_id,
            tenant_id=tenant_id,
        )
        self._check_section_not_cancelled(tenant_id, request.enrollment_id)
        self._check_term_submission_window_open(tenant_id, enrollment.term_id)
        GradeLifecycleRules.validate_grade_submission_allowed(enrollment)

        existing = self._load_grade_submission(tenant_id, request.enrollment_id)
        if existing is not None:
            return MutationResult(
                entity=GradeReadSchema.model_validate(existing),
                idempotent_replay=True,
            )

        self._load_grading_scale(tenant_id, request.grading_scale_id)
        scale_items = self._load_scale_items(tenant_id, request.grading_scale_id)
        resolved_points = GradeLifecycleRules.validate_grade_points_match_scale(
            request.grade_code,
            cast(list[object], scale_items),
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

        risk_level = self._derive_grade_risk_level(resolved_points)
        if risk_level is not None:
            try:
                from datetime import timedelta
                from app.modules.interventions.models import (
                    InterventionAssigneeType,
                    InterventionCaseModel,
                    InterventionCaseSeverity,
                    InterventionCaseStatus,
                    InterventionCaseType,
                )
                from sqlalchemy import and_, select
                _existing = self.db.execute(
                    select(InterventionCaseModel).where(
                        and_(
                            InterventionCaseModel.tenant_id == tenant_id,
                            InterventionCaseModel.student_profile_id == enrollment.student_profile_id,
                            InterventionCaseModel.case_type == InterventionCaseType.ACADEMIC_RISK,
                            InterventionCaseModel.status.in_(
                                (InterventionCaseStatus.OPEN, InterventionCaseStatus.IN_PROGRESS)
                            ),
                        )
                    )
                ).scalar_one_or_none()
                if _existing is None:
                    _sev = InterventionCaseSeverity.HIGH if risk_level == "high" else InterventionCaseSeverity.MEDIUM
                    _days = 3 if risk_level == "high" else 5
                    _assignee = "dean_office" if risk_level == "high" else "faculty_advisor"
                    _now = datetime.now(UTC)
                    intervention = InterventionCaseModel(
                        tenant_id=tenant_id,
                        case_type=InterventionCaseType.ACADEMIC_RISK,
                        student_profile_id=enrollment.student_profile_id,
                        severity=_sev,
                        status=InterventionCaseStatus.OPEN,
                        title=f"Grade risk ({risk_level}): student {enrollment.student_profile_id}",
                        description=(
                            f"Auto-created on grade submission {submission.id}. "
                            f"Grade: {request.grade_code} ({resolved_points} pts). "
                            f"Risk threshold: {risk_level}."
                        ),
                        risk_snapshot_json={
                            "grade_code": request.grade_code,
                            "grade_points": str(resolved_points),
                            "risk_level": risk_level,
                            "submission_id": submission.id,
                            "course_id": enrollment.course_id,
                        },
                        assignee_type=InterventionAssigneeType.GROUP,
                        assignee_ref=_assignee,
                        due_at=_now + timedelta(days=_days),
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                    self.db.add(intervention)
            except Exception:
                pass  # Intervention auto-create errors must never break grade submission

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

        publisher = EventPublisher(db_session=self.db)
        publisher.publish_event(
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

        if risk_level is not None:
            publisher.publish_event(
                tenant_id=tenant_id,
                event_type="academic.grade_risk.detected",
                aggregate_type="grade_submission",
                aggregate_id=submission.id,
                payload_json={
                    "student_id": enrollment.student_profile_id,
                    "course_id": enrollment.course_id,
                    "section_id": None,
                    "current_grade": float(resolved_points),
                    "grade_trend": "declining",
                    "risk_level": risk_level,
                    "source_entity_type": "grade_submission",
                    "source_entity_id": str(submission.id),
                },
            )
            try:
                from uuid import uuid4
                from app.modules.brain_core.service import brain_core_service
                brain_core_service.process_signal({
                    "event_type": "academic.grade_risk.detected",
                    "tenant_id": tenant_id,
                    "correlation_id": str(uuid4()),
                    "source_entity_type": "grade_submission",
                    "source_entity_id": str(submission.id),
                    "payload": {
                        "student_id": enrollment.student_profile_id,
                        "course_id": enrollment.course_id,
                        "current_grade": float(resolved_points),
                        "grade_trend": "declining",
                        "risk_level": risk_level,
                    },
                })
            except Exception:
                pass  # Brain Core errors must never break core flows

        record_usage_event(tenant_id=tenant_id, metric="grades_submitted", value=1)

        return MutationResult(entity=GradeReadSchema.model_validate(submission))

    async def create_grading_scale(
        self,
        tenant_id: int,
        *,
        request: GradingScaleCreateSchema,
        actor_id: str,
    ) -> GradingScaleReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        if not str(actor_id or "").strip():
            raise PermissionError("actor is required for grading scale creation")

        scale = GradingScaleModel(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            is_active=request.is_active,
        )
        self.db.add(scale)
        self.db.flush()

        items = [
            GradingScaleItemModel(
                tenant_id=tenant_id,
                scale_id=scale.id,
                grade_code=item.grade_code,
                grade_points=self._quantize(item.grade_points),
                min_percentage=self._quantize(item.min_percentage),
                max_percentage=self._quantize(item.max_percentage),
            )
            for item in request.items
        ]
        self.db.add_all(items)
        self.db.flush()

        _audit(
            actor=actor_id,
            action=build_audit_action("grades", "grading_scale", "created"),
            path="/internal/grades/scales/create",
            entity="grading_scale",
            metadata={
                "resource_id": str(scale.id),
                "name": scale.name,
                "item_count": len(items),
            },
            tenant_id=tenant_id,
        )
        log_data_access_event(
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource="grading_scale",
            resource_id=scale.id,
            action="write",
            result="success",
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create grading scale due to constraint violation") from exc

        self.db.refresh(scale)
        for item in items:
            self.db.refresh(item)

        return self._scale_read_schema(scale, items)

    async def change_grade(
        self,
        tenant_id: int,
        request: GradeChangeSchema,
        actor_id: str,
    ) -> MutationResult[GradeReadSchema]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        GradeLifecycleRules.validate_grade_change_allowed(actor_id)

        enrollment = self._load_enrollment(tenant_id, request.enrollment_id)
        GradeLifecycleRules.validate_grade_submission_allowed(enrollment)

        submission = self._load_grade_submission(tenant_id, request.enrollment_id)
        if submission is None:
            raise TenantResourceNotFoundError(
                f"Grade submission for enrollment {request.enrollment_id} not found or does not belong to tenant {tenant_id}"
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
            cast(list[object], scale_items),
            request.new_grade_points,
        )
        resolved_points = self._quantize(resolved_points)

        prev_code = submission.grade_code
        prev_points = submission.grade_points

        if prev_code == request.new_grade_code and Decimal(str(prev_points)) == resolved_points:
            return MutationResult(
                entity=GradeReadSchema.model_validate(submission),
                idempotent_replay=True,
            )

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

        record_usage_event(tenant_id=tenant_id, metric="grades_submitted", value=1)

        return MutationResult(entity=GradeReadSchema.model_validate(submission))

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
                student_id=0,
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

    async def list_tenant_grades(
        self,
        tenant_id: int,
        *,
        student_profile_id: int | None = None,
        course_id: int | None = None,
        term_id: int | None = None,
        section_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
        actor_id: str | None = None,
    ) -> GradeListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [GradeSubmissionModel.tenant_id == tenant_id]
        enrollment_filters = [EnrollmentModel.tenant_id == tenant_id]
        if student_profile_id is not None:
            enrollment_filters.append(EnrollmentModel.student_profile_id == student_profile_id)
        if course_id is not None:
            enrollment_filters.append(EnrollmentModel.course_id == course_id)
        if term_id is not None:
            enrollment_filters.append(EnrollmentModel.term_id == term_id)
        if section_id is not None:
            enrollment_filters.append(EnrollmentModel.section_id == section_id)

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
            .where(and_(*filters, *enrollment_filters))
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
            .where(and_(*filters, *enrollment_filters))
            .order_by(desc(GradeSubmissionModel.submitted_at), desc(GradeSubmissionModel.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="grade",
                resource_id=tenant_id,
                action="read",
                result="success",
            )

        return GradeListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[GradeReadSchema.model_validate(item) for item in items],
        )

    async def list_grading_scales(
        self,
        tenant_id: int,
        *,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 100,
        actor_id: str | None = None,
    ) -> GradingScaleListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [GradingScaleModel.tenant_id == tenant_id]
        if active_only:
            filters.append(GradingScaleModel.is_active.is_(True))

        total = self.db.execute(
            select(func.count()).select_from(GradingScaleModel).where(and_(*filters))
        ).scalar_one()

        scales = self.db.execute(
            select(GradingScaleModel)
            .where(and_(*filters))
            .order_by(GradingScaleModel.name, GradingScaleModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        scale_ids = [scale.id for scale in scales]
        item_map: dict[int, list[GradingScaleItemModel]] = {scale_id: [] for scale_id in scale_ids}
        if scale_ids:
            items = self.db.execute(
                select(GradingScaleItemModel)
                .where(
                    and_(
                        GradingScaleItemModel.tenant_id == tenant_id,
                        GradingScaleItemModel.scale_id.in_(scale_ids),
                    )
                )
                .order_by(
                    GradingScaleItemModel.scale_id,
                    GradingScaleItemModel.max_percentage.desc(),
                    GradingScaleItemModel.id,
                )
            ).scalars().all()
            for item in items:
                item_map.setdefault(item.scale_id, []).append(item)

        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="grading_scale",
                resource_id=tenant_id,
                action="read",
                result="success",
            )

        return GradingScaleListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[self._scale_read_schema(scale, item_map.get(scale.id, [])) for scale in scales],
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

    async def list_tenant_grade_enrollment_consistency_report(
        self,
        tenant_id: int,
    ) -> GradeEnrollmentConsistencyReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        enrollments = self.db.execute(
            select(EnrollmentModel)
            .where(EnrollmentModel.tenant_id == tenant_id)
            .order_by(EnrollmentModel.id)
        ).scalars().all()

        submissions = self.db.execute(
            select(GradeSubmissionModel)
            .where(GradeSubmissionModel.tenant_id == tenant_id)
            .order_by(GradeSubmissionModel.enrollment_id, GradeSubmissionModel.id)
        ).scalars().all()

        enrollment_by_id = {int(enrollment.id): enrollment for enrollment in enrollments}
        submissions_by_enrollment: dict[int, list[GradeSubmissionModel]] = {}
        for submission in submissions:
            submissions_by_enrollment.setdefault(int(submission.enrollment_id), []).append(submission)

        issues: list[GradeEnrollmentConsistencyIssueSchema] = []

        for enrollment in enrollments:
            enrollment_id = int(enrollment.id)
            linked_submissions = submissions_by_enrollment.get(enrollment_id, [])
            has_enrollment_grade = enrollment.grade_code is not None or enrollment.grade_points is not None

            if has_enrollment_grade and not linked_submissions:
                issues.append(
                    GradeEnrollmentConsistencyIssueSchema(
                        issue_type="missing_grade_submission",
                        enrollment_id=enrollment_id,
                    )
                )
                continue

            if len(linked_submissions) > 1:
                issues.append(
                    GradeEnrollmentConsistencyIssueSchema(
                        issue_type="duplicate_grade_submissions_for_enrollment",
                        enrollment_id=enrollment_id,
                        grade_submission_id=int(linked_submissions[0].id),
                    )
                )

            if not linked_submissions:
                continue

            submission = linked_submissions[0]
            field_pairs = [
                ("grade_code", enrollment.grade_code, submission.grade_code),
                (
                    "grade_points",
                    str(enrollment.grade_points) if enrollment.grade_points is not None else None,
                    str(submission.grade_points) if submission.grade_points is not None else None,
                ),
            ]

            for field_name, expected, actual in field_pairs:
                if expected != actual:
                    issues.append(
                        GradeEnrollmentConsistencyIssueSchema(
                            issue_type="grade_enrollment_mismatch",
                            enrollment_id=enrollment_id,
                            grade_submission_id=int(submission.id),
                            field=field_name,
                            expected=str(expected) if expected is not None else None,
                            actual=str(actual) if actual is not None else None,
                        )
                    )

        for submission in submissions:
            if int(submission.enrollment_id) not in enrollment_by_id:
                issues.append(
                    GradeEnrollmentConsistencyIssueSchema(
                        issue_type="dangling_grade_submission",
                        enrollment_id=int(submission.enrollment_id),
                        grade_submission_id=int(submission.id),
                    )
                )

        return GradeEnrollmentConsistencyReportSchema(
            enrollment_count=len(enrollments),
            grade_submission_count=len(submissions),
            issue_count=len(issues),
            issues=issues,
        )
