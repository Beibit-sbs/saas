from __future__ import annotations

import logging
from copy import deepcopy
from datetime import UTC, datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.audit.service import log_data_access_event
from app.modules.billing.service import assert_billing_write_allowed
from app.modules.courses.models import CourseModel
from app.modules.enrollments.business_rules import EnrollmentLifecycleRules
from app.modules.enrollments.models import (
    AcademicTermModel,
    EnrollmentModel,
    EnrollmentStatus,
    EnrollmentStatusHistoryModel,
)
from app.modules.enrollments.schemas import (
    EnrollmentConsistencyIssueSchema,
    EnrollmentConsistencyReportSchema,
    EnrollmentCreateSchema,
    EnrollmentDropSchema,
    EnrollmentListResponseSchema,
    EnrollmentReadSchema,
    EnrollmentStatusChangeSchema,
)
from app.modules.scheduling.models import CourseSectionModel, SectionStatus
from app.modules.students.models import StudentProfileModel
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher

logger = logging.getLogger("app.modules.enrollments")


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


_DROPOUT_RISK_STATUSES = {
    EnrollmentStatus.WITHDRAWN,
    EnrollmentStatus.SUSPENDED,
    EnrollmentStatus.DROPPED,
}


def _emit_dropout_risk_signal(
    *,
    tenant_id: int,
    enrollment_id: int,
    student_profile_id: int,
    course_id: int,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for enrollment dropout-risk scenarios."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="enrollments.dropout_risk.detected",
        aggregate_type="enrollment",
        aggregate_id=enrollment_id,
        payload_json={
            "enrollment_id": enrollment_id,
            "student_id": student_profile_id,
            "course_id": course_id,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "enrollments",
            "source_entity_type": "enrollment",
            "source_entity_id": str(enrollment_id),
        },
    )


def _merge_metadata(existing: dict | None, incoming: dict | None) -> dict:
    base = deepcopy(existing or {})
    for key, value in (incoming or {}).items():
        current_value = base.get(key)
        if isinstance(current_value, dict) and isinstance(value, dict):
            base[key] = _merge_metadata(current_value, value)
        else:
            base[key] = deepcopy(value)
    return base


def _record_outcome(entity_id: object, outcome_type: str, actor_id: str) -> None:
    try:
        from app.modules.brain_core import service as brain_core_service  # noqa: PLC0415
        brain_core_service.record_dispatch_outcome(
            entity_id=entity_id,
            outcome_type=outcome_type,
            actor_id=str(actor_id),
        )
    except Exception:
        logger.exception("enrollments outcome failed entity_id=%s outcome=%s", entity_id, outcome_type)


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        logger.exception("enrollments metric failed metric=%s", metric)


class EnrollmentLifecycleService:
    """Canonical lifecycle service for Enrollment Phase 2."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def _load_student_profile(self, tenant_id: int, student_profile_id: int) -> StudentProfileModel:
        profile = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            profile,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )
        return profile

    def _load_course(self, tenant_id: int, course_id: int) -> CourseModel:
        course = self.db.execute(
            select(CourseModel).where(
                and_(
                    CourseModel.id == course_id,
                    CourseModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        EnrollmentLifecycleRules.validate_course_reference(
            course,
            tenant_id=tenant_id,
            course_id=course_id,
        )
        return course

    def _load_term(self, tenant_id: int, term_id: int) -> AcademicTermModel:
        term = self.db.execute(
            select(AcademicTermModel).where(
                and_(
                    AcademicTermModel.id == term_id,
                    AcademicTermModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        EnrollmentLifecycleRules.validate_term_reference(
            term,
            tenant_id=tenant_id,
            term_id=term_id,
        )
        return term

    def _load_section_for_enrollment(
        self,
        tenant_id: int,
        *,
        section_id: int,
        course_id: int,
        term_id: int,
    ) -> CourseSectionModel:
        section = self.db.execute(
            select(CourseSectionModel).where(
                and_(
                    CourseSectionModel.tenant_id == tenant_id,
                    CourseSectionModel.id == section_id,
                )
            )
        ).scalar_one_or_none()
        if section is None:
            raise DomainValidationError(
                f"section_id={section_id} not found for tenant_id={tenant_id}"
            )
        if section.course_id != course_id or section.term_id != term_id:
            raise DomainValidationError(
                "Enrollment blocked: section linkage mismatch. "
                f"section_id={section_id} belongs to course_id={section.course_id}, term_id={section.term_id}, "
                f"but enrollment requested course_id={course_id}, term_id={term_id}"
            )
        if section.status == SectionStatus.CANCELLED:
            raise DomainValidationError(
                f"Enrollment blocked: section_id={section_id} is cancelled"
            )
        return section

    def _check_section_capacity(self, tenant_id: int, section: CourseSectionModel) -> None:
        """Cross-module capacity guard: concrete section capacity via section_id."""
        section_capacity = section.max_capacity or 0
        if section_capacity <= 0:
            return

        active_count = self.db.execute(
            select(func.count()).select_from(EnrollmentModel).where(
                and_(
                    EnrollmentModel.tenant_id == tenant_id,
                    EnrollmentModel.section_id == section.id,
                    EnrollmentModel.enrollment_status.in_(
                        tuple(EnrollmentLifecycleRules.ACTIVE_ENROLLMENT_STATUSES)
                    ),
                )
            )
        ).scalar() or 0

        if active_count >= section_capacity:
            raise DomainValidationError(
                f"Section is at full capacity ({active_count}/{section_capacity})"
            )

    def _check_course_prerequisites(self, tenant_id: int, student_profile_id: int, course_id: int) -> None:
        """Cross-module prerequisite guard: courses.prerequisites → enrollments.completed.

        Before enrolling a student in a course, verify that all declared prerequisite courses
        have been COMPLETED by the student (any term).  Raises DomainValidationError listing
        every unmet prerequisite so the student receives actionable feedback.
        """
        from app.modules.courses.models import CoursePrerequisiteModel  # noqa: PLC0415

        prereqs = self.db.execute(
            select(CoursePrerequisiteModel).where(
                and_(
                    CoursePrerequisiteModel.tenant_id == tenant_id,
                    CoursePrerequisiteModel.course_id == course_id,
                )
            )
        ).scalars().all()

        if not prereqs:
            return

        missing: list[int] = []
        for prereq in prereqs:
            completed = self.db.execute(
                select(func.count()).select_from(EnrollmentModel).where(
                    and_(
                        EnrollmentModel.tenant_id == tenant_id,
                        EnrollmentModel.student_profile_id == student_profile_id,
                        EnrollmentModel.course_id == prereq.prerequisite_course_id,
                        EnrollmentModel.enrollment_status == EnrollmentStatus.COMPLETED,
                    )
                )
            ).scalar() or 0

            if completed == 0:
                missing.append(prereq.prerequisite_course_id)

        if missing:
            ids = ", ".join(str(cid) for cid in sorted(missing))
            raise DomainValidationError(
                f"Prerequisite courses not completed for course_id={course_id}: "
                f"missing completed enrollment for course_id(s) [{ids}]"
            )

    def _check_drop_deadline(self, tenant_id: int, term_id: int) -> None:
        """Cross-entity add/drop deadline guard: enrollments × academic_terms.add_drop_deadline.

        If the term has an add_drop_deadline set and the current UTC time is past it,
        the drop operation is blocked to enforce institutional policy.
        Silently proceeds when no deadline is configured on the term.
        """
        term = self.db.execute(
            select(AcademicTermModel).where(
                and_(
                    AcademicTermModel.id == term_id,
                    AcademicTermModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if term is None or term.add_drop_deadline is None:
            return

        now = datetime.now(UTC)
        deadline = term.add_drop_deadline
        if deadline.tzinfo is None:
            from datetime import timezone as _tz  # noqa: PLC0415
            deadline = deadline.replace(tzinfo=_tz.utc)

        if now > deadline:
            raise DomainValidationError(
                f"Drop not allowed: term add/drop deadline "
                f"{deadline.strftime('%Y-%m-%d %H:%M UTC')} has passed"
            )

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

    def _append_status_history(
        self,
        *,
        tenant_id: int,
        enrollment_id: int,
        from_status: EnrollmentStatus | None,
        to_status: EnrollmentStatus,
        actor_id: str,
        reason: str | None,
        metadata_json: dict,
        version: int,
    ) -> None:
        self.db.add(
            EnrollmentStatusHistoryModel(
                tenant_id=tenant_id,
                enrollment_id=enrollment_id,
                from_status=from_status,
                to_status=to_status,
                actor_id=actor_id,
                reason=reason,
                changed_at=_utc_now(),
                metadata_json=metadata_json,
                version=version,
            )
        )

    async def get_active_enrollment_for_student_course_term(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        course_id: int,
        term_id: int,
        actor_id: str | None = None,
    ) -> EnrollmentReadSchema | None:
        tenant_id = validate_tenant_id_provided(tenant_id)

        enrollment = self.db.execute(
            select(EnrollmentModel)
            .where(
                and_(
                    EnrollmentModel.tenant_id == tenant_id,
                    EnrollmentModel.student_profile_id == student_profile_id,
                    EnrollmentModel.course_id == course_id,
                    EnrollmentModel.term_id == term_id,
                    EnrollmentModel.enrollment_status.in_(
                        tuple(EnrollmentLifecycleRules.ACTIVE_ENROLLMENT_STATUSES)
                    ),
                )
            )
            .order_by(desc(EnrollmentModel.enrolled_at), desc(EnrollmentModel.id))
        ).scalars().first()

        if enrollment is None:
            return None
        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="enrollment",
                resource_id=enrollment.id,
                action="read",
                result="success",
            )
        return EnrollmentReadSchema.model_validate(enrollment)

    async def enroll_student(
        self,
        tenant_id: int,
        request: EnrollmentCreateSchema,
        actor_id: str,
    ) -> EnrollmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        assert_billing_write_allowed(tenant_id, action="enrollments.create")
        EnrollmentLifecycleRules.validate_initial_status(request.enrollment_status)

        profile = self._load_student_profile(tenant_id, request.student_profile_id)
        EnrollmentLifecycleRules.validate_student_is_enrollable(profile, tenant_id)
        self._load_course(tenant_id, request.course_id)
        self._load_term(tenant_id, request.term_id)

        existing_active = await self.get_active_enrollment_for_student_course_term(
            tenant_id,
            student_profile_id=request.student_profile_id,
            course_id=request.course_id,
            term_id=request.term_id,
        )
        EnrollmentLifecycleRules.validate_no_active_duplicate(
            existing_active,
            student_profile_id=request.student_profile_id,
            course_id=request.course_id,
            term_id=request.term_id,
        )

        section = self._load_section_for_enrollment(
            tenant_id,
            section_id=request.section_id,
            course_id=request.course_id,
            term_id=request.term_id,
        )
        self._check_section_capacity(tenant_id, section)
        self._check_course_prerequisites(tenant_id, request.student_profile_id, request.course_id)

        enrollment = EnrollmentModel(
            tenant_id=tenant_id,
            student_profile_id=request.student_profile_id,
            course_id=request.course_id,
            term_id=request.term_id,
            section_id=request.section_id,
            enrollment_status=request.enrollment_status,
            enrollment_type=request.enrollment_type,
            enrolled_at=request.enrolled_at or _utc_now(),
            metadata_json=request.metadata_json,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(enrollment)
        self.db.flush()

        self._append_status_history(
            tenant_id=tenant_id,
            enrollment_id=enrollment.id,
            from_status=None,
            to_status=enrollment.enrollment_status,
            actor_id=actor_id,
            reason="initial_enrollment_creation",
            metadata_json={
                "course_validation": "real_course_reference_validated",
                "term_reference_strategy": "canonical_term_id",
            },
            version=enrollment.version,
        )

        self.db.flush()
        self.db.refresh(enrollment)

        _audit(
            actor=actor_id,
            action=build_audit_action("enrollments", "enrollment", "created"),
            path=f"/internal/enrollments/enrollments/{enrollment.id}",
            entity="enrollment",
            metadata={
                "resource_id": str(enrollment.id),
                "student_profile_id": enrollment.student_profile_id,
                "course_id": enrollment.course_id,
                "term_id": enrollment.term_id,
                "section_id": enrollment.section_id,
                "enrollment_status": enrollment.enrollment_status.value,
            },
            tenant_id=tenant_id,
        )
        log_data_access_event(
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource="enrollment",
            resource_id=enrollment.id,
            action="write",
            result="success",
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError(
                "Unable to create enrollment due to constraint violation"
            ) from exc

        EventPublisher(db_session=self.db).publish_event(
            tenant_id=tenant_id,
            event_type="enrollment.created",
            aggregate_type="enrollment",
            aggregate_id=enrollment.id,
            payload_json={
                "enrollment_id": enrollment.id,
                "student_profile_id": enrollment.student_profile_id,
                "course_id": enrollment.course_id,
                "term_id": enrollment.term_id,
                "section_id": enrollment.section_id,
                "enrollment_status": enrollment.enrollment_status.value,
                "created_by": actor_id,
            },
        )

        try:
            from app.modules.usage.service import record_usage_event
            record_usage_event(tenant_id, "enrollments_created", 1)
        except Exception:
            pass

        return EnrollmentReadSchema.model_validate(enrollment)

    async def get_enrollment(
        self,
        tenant_id: int,
        enrollment_id: int,
        actor_id: str | None = None,
    ) -> EnrollmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        enrollment = self._load_enrollment(tenant_id, enrollment_id)
        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="enrollment",
                resource_id=enrollment.id,
                action="read",
                result="success",
            )
        return EnrollmentReadSchema.model_validate(enrollment)

    async def list_tenant_enrollment_consistency_report(
        self,
        tenant_id: int,
    ) -> EnrollmentConsistencyReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        enrollments = self.db.execute(
            select(EnrollmentModel)
            .where(EnrollmentModel.tenant_id == tenant_id)
            .order_by(EnrollmentModel.id)
        ).scalars().all()

        student_ids = set(
            self.db.execute(
                select(StudentProfileModel.id).where(
                    StudentProfileModel.tenant_id == tenant_id
                )
            ).scalars().all()
        )
        course_ids = set(
            self.db.execute(
                    select(CourseModel.id).where(CourseModel.tenant_id == tenant_id)
            ).scalars().all()
        )
        term_ids = set(
            self.db.execute(
                select(AcademicTermModel.id).where(
                    AcademicTermModel.tenant_id == tenant_id
                )
            ).scalars().all()
        )

        issues: list[EnrollmentConsistencyIssueSchema] = []
        for enrollment in enrollments:
            enrollment_id = int(enrollment.id)
            if int(enrollment.student_profile_id) not in student_ids:
                issues.append(
                    EnrollmentConsistencyIssueSchema(
                        issue_type="enrollment_missing_student_profile",
                        enrollment_id=enrollment_id,
                        student_profile_id=int(enrollment.student_profile_id),
                        course_id=int(enrollment.course_id),
                        term_id=int(enrollment.term_id),
                    )
                )
            if int(enrollment.course_id) not in course_ids:
                issues.append(
                    EnrollmentConsistencyIssueSchema(
                        issue_type="enrollment_missing_course",
                        enrollment_id=enrollment_id,
                        student_profile_id=int(enrollment.student_profile_id),
                        course_id=int(enrollment.course_id),
                        term_id=int(enrollment.term_id),
                    )
                )
            if int(enrollment.term_id) not in term_ids:
                issues.append(
                    EnrollmentConsistencyIssueSchema(
                        issue_type="enrollment_missing_term",
                        enrollment_id=enrollment_id,
                        student_profile_id=int(enrollment.student_profile_id),
                        course_id=int(enrollment.course_id),
                        term_id=int(enrollment.term_id),
                    )
                )

        return EnrollmentConsistencyReportSchema(
            enrollment_count=len(enrollments),
            issue_count=len(issues),
            issues=issues,
        )

    async def list_student_enrollments(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        status: EnrollmentStatus | None = None,
        term_id: int | None = None,
    ) -> EnrollmentListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_student_profile(tenant_id, student_profile_id)

        filters = [
            EnrollmentModel.tenant_id == tenant_id,
            EnrollmentModel.student_profile_id == student_profile_id,
        ]
        if status is not None:
            filters.append(EnrollmentModel.enrollment_status == status)
        if term_id is not None:
            filters.append(EnrollmentModel.term_id == term_id)

        total = self.db.execute(
            select(func.count()).select_from(EnrollmentModel).where(and_(*filters))
        ).scalar_one()
        items = self.db.execute(
            select(EnrollmentModel)
            .where(and_(*filters))
            .order_by(desc(EnrollmentModel.enrolled_at), desc(EnrollmentModel.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="enrollment",
                resource_id=student_profile_id,
                action="read",
                result="success",
            )

        return EnrollmentListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[EnrollmentReadSchema.model_validate(item) for item in items],
        )

    async def list_course_roster(
        self,
        tenant_id: int,
        *,
        course_id: int,
        term_id: int,
        actor_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
        status: EnrollmentStatus | None = None,
    ) -> EnrollmentListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_course(tenant_id, course_id)

        filters = [
            EnrollmentModel.tenant_id == tenant_id,
            EnrollmentModel.course_id == course_id,
            EnrollmentModel.term_id == term_id,
        ]
        if status is not None:
            filters.append(EnrollmentModel.enrollment_status == status)

        total = self.db.execute(
            select(func.count()).select_from(EnrollmentModel).where(and_(*filters))
        ).scalar_one()
        items = self.db.execute(
            select(EnrollmentModel)
            .where(and_(*filters))
            .order_by(desc(EnrollmentModel.enrolled_at), desc(EnrollmentModel.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        if actor_id:
            log_data_access_event(
                actor_id=actor_id,
                tenant_id=tenant_id,
                resource="enrollment",
                resource_id=course_id,
                action="read",
                result="success",
            )

        return EnrollmentListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[EnrollmentReadSchema.model_validate(item) for item in items],
        )

    async def change_enrollment_status(
        self,
        tenant_id: int,
        enrollment_id: int,
        request: EnrollmentStatusChangeSchema,
        actor_id: str,
    ) -> EnrollmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        enrollment = self._load_enrollment(tenant_id, enrollment_id)

        validate_version_match(enrollment.version, request.expected_version)
        previous_status = EnrollmentStatus(enrollment.enrollment_status)
        EnrollmentLifecycleRules.validate_status_transition(previous_status, request.to_status)

        merged_metadata = _merge_metadata(enrollment.metadata_json, request.metadata_json)
        self._append_status_history(
            tenant_id=tenant_id,
            enrollment_id=enrollment.id,
            from_status=previous_status,
            to_status=request.to_status,
            actor_id=actor_id,
            reason=request.reason,
            metadata_json=request.metadata_json,
            version=enrollment.version + 1,
        )

        enrollment.enrollment_status = request.to_status
        if request.to_status in {EnrollmentStatus.DROPPED, EnrollmentStatus.WITHDRAWN}:
            enrollment.dropped_at = enrollment.dropped_at or _utc_now()
        enrollment.metadata_json = merged_metadata
        enrollment.version += 1
        enrollment.updated_by = actor_id
        self.db.flush()
        self.db.refresh(enrollment)

        _audit(
            actor=actor_id,
            action=build_audit_action("enrollments", "enrollment", "status_changed"),
            path=f"/internal/enrollments/enrollments/{enrollment.id}/status",
            entity="enrollment",
            metadata={
                "resource_id": str(enrollment.id),
                "from_status": previous_status.value,
                "to_status": request.to_status.value,
                "version": enrollment.version,
            },
            tenant_id=tenant_id,
        )
        log_data_access_event(
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource="enrollment",
            resource_id=enrollment.id,
            action="update",
            result="success",
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError(
                "Unable to change enrollment status due to constraint violation"
            ) from exc

        if request.to_status in _DROPOUT_RISK_STATUSES:
            try:
                _emit_dropout_risk_signal(
                    tenant_id=tenant_id,
                    enrollment_id=enrollment.id,
                    student_profile_id=enrollment.student_profile_id,
                    course_id=enrollment.course_id,
                    from_status=previous_status.value,
                    to_status=request.to_status.value,
                )
            except Exception:
                pass
            try:
                from uuid import uuid4
                from app.modules.brain_core.service import brain_core_service
                brain_core_service.process_signal({
                    "event_type": "enrollments.dropout_risk.detected",
                    "tenant_id": tenant_id,
                    "correlation_id": str(uuid4()),
                    "source_entity_type": "enrollment",
                    "source_entity_id": str(enrollment.id),
                    "payload": {
                        "enrollment_id": enrollment.id,
                        "student_id": enrollment.student_profile_id,
                        "course_id": enrollment.course_id,
                        "from_status": previous_status.value,
                        "to_status": request.to_status.value,
                    },
                })
            except Exception:
                pass  # Brain Core errors must never break core flows

            # Cross-module: create intervention case directly (no Brain dependency)
            try:
                from app.modules.interventions.models import (
                    InterventionAssigneeType,
                    InterventionCaseModel,
                    InterventionCaseSeverity,
                    InterventionCaseStatus,
                    InterventionCaseType,
                )
                from datetime import datetime, UTC, timedelta

                intervention = InterventionCaseModel(
                    tenant_id=tenant_id,
                    case_type=InterventionCaseType.ACADEMIC_RISK,
                    student_profile_id=enrollment.student_profile_id,
                    severity=InterventionCaseSeverity.HIGH,
                    status=InterventionCaseStatus.OPEN,
                    title=f"Dropout risk: student {enrollment.student_profile_id} ({request.to_status.value})",
                    description=(
                        f"Auto-created on enrollment status change. "
                        f"Enrollment {enrollment.id}: {previous_status.value} → {request.to_status.value}."
                    ),
                    risk_snapshot_json={
                        "enrollment_id": enrollment.id,
                        "course_id": enrollment.course_id,
                        "from_status": previous_status.value,
                        "to_status": request.to_status.value,
                    },
                    assignee_type=InterventionAssigneeType.GROUP,
                    assignee_ref="student_support",
                    due_at=datetime.now(UTC) + timedelta(days=3),
                )
                self.db.add(intervention)
                self.db.commit()
            except Exception:
                pass  # intervention wiring must never break core enrollment flow

        return EnrollmentReadSchema.model_validate(enrollment)

    async def drop_enrollment(
        self,
        tenant_id: int,
        enrollment_id: int,
        request: EnrollmentDropSchema,
        actor_id: str,
    ) -> EnrollmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        enrollment = self._load_enrollment(tenant_id, enrollment_id)

        validate_version_match(enrollment.version, request.expected_version)
        previous_status = EnrollmentStatus(enrollment.enrollment_status)
        EnrollmentLifecycleRules.validate_drop_allowed(previous_status)
        self._check_drop_deadline(tenant_id, enrollment.term_id)

        dropped_at = request.dropped_at or _utc_now()
        merged_metadata = _merge_metadata(enrollment.metadata_json, request.metadata_json)

        self._append_status_history(
            tenant_id=tenant_id,
            enrollment_id=enrollment.id,
            from_status=previous_status,
            to_status=EnrollmentStatus.DROPPED,
            actor_id=actor_id,
            reason=request.reason or "drop_enrollment",
            metadata_json=request.metadata_json,
            version=enrollment.version + 1,
        )

        enrollment.enrollment_status = EnrollmentStatus.DROPPED
        enrollment.dropped_at = dropped_at
        enrollment.metadata_json = merged_metadata
        enrollment.version += 1
        enrollment.updated_by = actor_id
        self.db.flush()
        self.db.refresh(enrollment)

        _audit(
            actor=actor_id,
            action=build_audit_action("enrollments", "enrollment", "dropped"),
            path=f"/internal/enrollments/enrollments/{enrollment.id}/drop",
            entity="enrollment",
            metadata={
                "resource_id": str(enrollment.id),
                "from_status": previous_status.value,
                "to_status": EnrollmentStatus.DROPPED.value,
                "dropped_at": enrollment.dropped_at.isoformat() if enrollment.dropped_at else None,
                "version": enrollment.version,
            },
            tenant_id=tenant_id,
        )
        log_data_access_event(
            actor_id=actor_id,
            tenant_id=tenant_id,
            resource="enrollment",
            resource_id=enrollment.id,
            action="delete",
            result="success",
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError(
                "Unable to drop enrollment due to constraint violation"
            ) from exc

        try:
            from app.modules.usage.service import record_usage_event
            record_usage_event(tenant_id, "enrollments_dropped", 1)
        except Exception:
            pass

        try:
            from uuid import uuid4
            from app.modules.brain_core.service import brain_core_service
            brain_core_service.process_signal({
                "event_type": "enrollments.dropout_risk.detected",
                "tenant_id": tenant_id,
                "correlation_id": str(uuid4()),
                "source_entity_type": "enrollment",
                "source_entity_id": str(enrollment.id),
                "payload": {
                    "enrollment_id": enrollment.id,
                    "student_id": enrollment.student_profile_id,
                    "course_id": enrollment.course_id,
                    "from_status": previous_status.value,
                    "to_status": EnrollmentStatus.DROPPED.value,
                },
            })
        except Exception:
            pass  # Brain Core errors must never break core flows

        return EnrollmentReadSchema.model_validate(enrollment)


# ---------------------------------------------------------------------------
# Legacy compatibility for current router (to be removed in future phase).
# ---------------------------------------------------------------------------


def list_enrollments(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("enrollments", tenant_id)


def create_enrollment(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    assert_billing_write_allowed(int(tenant_id), action="enrollments.create")
    result = create_entity_for_tenant("enrollments", payload, tenant_id)
    _record_outcome(result.get("id"), "enrollment_created", str(payload.get("actor_id") or "system"))
    _metric(tenant_id, "enrollments_created")
    return result


def update_enrollment(enrollment_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    result = update_entity_for_tenant("enrollments", enrollment_id, payload, tenant_id)
    _record_outcome(enrollment_id, "enrollment_updated", str(payload.get("actor_id") or "system"))
    _metric(tenant_id, "enrollments_updated")
    return result


def delete_enrollment(enrollment_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("enrollments", enrollment_id, tenant_id)
