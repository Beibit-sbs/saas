from __future__ import annotations

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
)
from app.modules.enrollments.models import EnrollmentStatus
from app.modules.students.models import StudentStatus


class EnrollmentLifecycleRules:
    """Domain rules for canonical enrollment lifecycle operations."""

    ACTIVE_ENROLLMENT_STATUSES: set[EnrollmentStatus] = {
        EnrollmentStatus.PENDING,
        EnrollmentStatus.ENROLLED,
        EnrollmentStatus.WAITLIST,
        EnrollmentStatus.SUSPENDED,
    }

    _INITIAL_ENROLLMENT_STATUSES: set[EnrollmentStatus] = {
        EnrollmentStatus.PENDING,
        EnrollmentStatus.ENROLLED,
        EnrollmentStatus.WAITLIST,
    }

    _ALLOWED_STATUS_TRANSITIONS: dict[EnrollmentStatus, set[EnrollmentStatus]] = {
        EnrollmentStatus.PENDING: {
            EnrollmentStatus.ENROLLED,
            EnrollmentStatus.WAITLIST,
            EnrollmentStatus.DROPPED,
            EnrollmentStatus.WITHDRAWN,
            EnrollmentStatus.SUSPENDED,
        },
        EnrollmentStatus.ENROLLED: {
            EnrollmentStatus.COMPLETED,
            EnrollmentStatus.DROPPED,
            EnrollmentStatus.WITHDRAWN,
            EnrollmentStatus.SUSPENDED,
        },
        EnrollmentStatus.WAITLIST: {
            EnrollmentStatus.PENDING,
            EnrollmentStatus.ENROLLED,
            EnrollmentStatus.DROPPED,
            EnrollmentStatus.WITHDRAWN,
        },
        EnrollmentStatus.SUSPENDED: {
            EnrollmentStatus.ENROLLED,
            EnrollmentStatus.DROPPED,
            EnrollmentStatus.WITHDRAWN,
        },
        EnrollmentStatus.COMPLETED: set(),
        EnrollmentStatus.DROPPED: set(),
        EnrollmentStatus.WITHDRAWN: set(),
    }

    @classmethod
    def validate_initial_status(cls, status: EnrollmentStatus) -> None:
        if status not in cls._INITIAL_ENROLLMENT_STATUSES:
            raise DomainValidationError(
                f"initial enrollment status '{status.value}' is not allowed"
            )

    @classmethod
    def validate_status_transition(
        cls,
        from_status: EnrollmentStatus,
        to_status: EnrollmentStatus,
    ) -> None:
        if from_status == to_status:
            raise DomainValidationError("status transition must change current status")

        allowed_targets = cls._ALLOWED_STATUS_TRANSITIONS.get(from_status, set())
        if to_status not in allowed_targets:
            raise DomainValidationError(
                f"enrollment status transition '{from_status.value}' -> '{to_status.value}' is not allowed"
            )

    @classmethod
    def validate_drop_allowed(cls, current_status: EnrollmentStatus) -> None:
        if current_status not in cls.ACTIVE_ENROLLMENT_STATUSES:
            raise DomainValidationError(
                f"enrollment with status '{current_status.value}' cannot be dropped"
            )

    @classmethod
    def validate_no_active_duplicate(
        cls,
        existing_enrollment: object | None,
        *,
        student_profile_id: int,
        course_id: int,
        term_id: int,
    ) -> None:
        if existing_enrollment is not None:
            raise DomainValidationError(
                "Active enrollment already exists for "
                f"student_profile_id={student_profile_id}, course_id={course_id}, term_id={term_id}"
            )

    @staticmethod
    def validate_student_is_enrollable(student: object | None, tenant_id: int) -> None:
        if student is None:
            raise TenantResourceNotFoundError(
                f"Student profile not found or does not belong to tenant {tenant_id}"
            )
        current_status = StudentStatus(getattr(student, "current_status"))
        if current_status not in {StudentStatus.ADMITTED, StudentStatus.ACTIVE}:
            raise DomainValidationError(
                f"Student profile with status '{current_status.value}' cannot be enrolled"
            )

    @staticmethod
    def validate_course_reference(
        course: object | None,
        *,
        tenant_id: int,
        course_id: int,
    ) -> None:
        if course is None:
            raise TenantResourceNotFoundError(
                f"Course {course_id} not found or does not belong to tenant {tenant_id}"
            )

        raw_tenant_id = getattr(course, "tenant_id", None)
        try:
            normalized_course_tenant_id = int(raw_tenant_id)
        except (TypeError, ValueError):
            raise TenantResourceNotFoundError(
                f"Course {course_id} not found or does not belong to tenant {tenant_id}"
            ) from None

        if normalized_course_tenant_id != tenant_id:
            raise TenantResourceNotFoundError(
                f"Course {course_id} not found or does not belong to tenant {tenant_id}"
            )

        course_status = str(getattr(course, "status", "")).strip().lower()
        if course_status and course_status != "active":
            raise DomainValidationError(
                f"Course {course_id} is not active and cannot accept enrollments"
            )

    @staticmethod
    def validate_term_reference(
        term: object | None,
        *,
        tenant_id: int,
        term_id: int,
    ) -> None:
        if term is None:
            raise TenantResourceNotFoundError(
                f"Academic term {term_id} not found or does not belong to tenant {tenant_id}"
            )
        term_status = str(getattr(term, "status", "")).strip().lower()
        if term_status and term_status != "active":
            raise DomainValidationError(
                f"Academic term {term_id} is not active and cannot accept enrollments"
            )