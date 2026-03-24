from __future__ import annotations

from decimal import Decimal

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.enrollments.models import EnrollmentStatus


class GradeLifecycleRules:
    ALLOWED_SUBMISSION_STATUSES: set[EnrollmentStatus] = {
        EnrollmentStatus.ENROLLED,
        EnrollmentStatus.COMPLETED,
    }

    @staticmethod
    def validate_grade_code_exists(scale_items: list[object], code: str) -> object:
        normalized = str(code or "").strip().upper()
        if not normalized:
            raise DomainValidationError("grade_code must be provided")

        for item in scale_items:
            if str(getattr(item, "grade_code", "")).strip().upper() == normalized:
                return item

        raise DomainValidationError(f"grade_code '{normalized}' does not exist in grading scale")

    @classmethod
    def validate_grade_submission_allowed(cls, enrollment: object) -> None:
        current_status = EnrollmentStatus(getattr(enrollment, "enrollment_status"))
        if current_status not in cls.ALLOWED_SUBMISSION_STATUSES:
            raise DomainValidationError(
                f"grade submission is not allowed for enrollment status '{current_status.value}'"
            )

    @staticmethod
    def validate_grade_change_allowed(actor: str | None) -> None:
        if not str(actor or "").strip():
            raise PermissionError("actor is required for grade change")

    @classmethod
    def validate_grade_points_match_scale(
        cls,
        code: str,
        scale_items: list[object],
        grade_points: Decimal | None,
    ) -> Decimal:
        item = cls.validate_grade_code_exists(scale_items, code)
        canonical_points = Decimal(str(getattr(item, "grade_points")))

        if grade_points is None:
            return canonical_points

        normalized_points = Decimal(str(grade_points))
        if normalized_points != canonical_points:
            raise DomainValidationError(
                f"grade_points {normalized_points} do not match grading scale for code '{code}'"
            )
        return normalized_points
