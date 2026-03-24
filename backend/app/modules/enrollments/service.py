from __future__ import annotations

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
from app.modules.courses.models import CourseModel
from app.modules.enrollments.business_rules import EnrollmentLifecycleRules
from app.modules.enrollments.models import (
    AcademicTermModel,
    EnrollmentModel,
    EnrollmentStatus,
    EnrollmentStatusHistoryModel,
)
from app.modules.enrollments.schemas import (
    EnrollmentCreateSchema,
    EnrollmentDropSchema,
    EnrollmentListResponseSchema,
    EnrollmentReadSchema,
    EnrollmentStatusChangeSchema,
)
from app.modules.students.models import StudentProfileModel
from app.modules.university_core.service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


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


def _merge_metadata(existing: dict | None, incoming: dict | None) -> dict:
    base = deepcopy(existing or {})
    for key, value in (incoming or {}).items():
        current_value = base.get(key)
        if isinstance(current_value, dict) and isinstance(value, dict):
            base[key] = _merge_metadata(current_value, value)
        else:
            base[key] = deepcopy(value)
    return base


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

    def _load_course_placeholder(self, tenant_id: int, course_id: int) -> object:
        course = self.db.execute(
            select(CourseModel).where(CourseModel.id == course_id)
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
        return EnrollmentReadSchema.model_validate(enrollment)

    async def enroll_student(
        self,
        tenant_id: int,
        request: EnrollmentCreateSchema,
        actor_id: str,
    ) -> EnrollmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        EnrollmentLifecycleRules.validate_initial_status(request.enrollment_status)

        profile = self._load_student_profile(tenant_id, request.student_profile_id)
        EnrollmentLifecycleRules.validate_student_is_enrollable(profile, tenant_id)
        self._load_course_placeholder(tenant_id, request.course_id)
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

        enrollment = EnrollmentModel(
            tenant_id=tenant_id,
            student_profile_id=request.student_profile_id,
            course_id=request.course_id,
            term_id=request.term_id,
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
                "course_validation": "placeholder_existing_course_model",
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
                "enrollment_status": enrollment.enrollment_status.value,
            },
            tenant_id=tenant_id,
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError(
                "Unable to create enrollment due to constraint violation"
            ) from exc

        return EnrollmentReadSchema.model_validate(enrollment)

    async def get_enrollment(
        self,
        tenant_id: int,
        enrollment_id: int,
    ) -> EnrollmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        enrollment = self._load_enrollment(tenant_id, enrollment_id)
        return EnrollmentReadSchema.model_validate(enrollment)

    async def list_student_enrollments(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
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
        page: int = 1,
        page_size: int = 50,
        status: EnrollmentStatus | None = None,
    ) -> EnrollmentListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_course_placeholder(tenant_id, course_id)

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

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError(
                "Unable to change enrollment status due to constraint violation"
            ) from exc

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

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError(
                "Unable to drop enrollment due to constraint violation"
            ) from exc

        return EnrollmentReadSchema.model_validate(enrollment)


# ---------------------------------------------------------------------------
# Legacy compatibility for current router (to be removed in future phase).
# ---------------------------------------------------------------------------


def list_enrollments(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("enrollments", tenant_id)


def create_enrollment(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("enrollments", payload, tenant_id)


def update_enrollment(enrollment_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("enrollments", enrollment_id, payload, tenant_id)


def delete_enrollment(enrollment_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("enrollments", enrollment_id, tenant_id)
