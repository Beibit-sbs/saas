from __future__ import annotations

from decimal import Decimal

from app.core.module_helpers.service_validation import DomainValidationError


class TranscriptRules:
    @staticmethod
    def validate_transcript_integrity(items: list[object]) -> None:
        seen_enrollments: set[int] = set()
        for item in items:
            enrollment_id = int(
                getattr(item, "enrollment_id", getattr(item, "id", 0))
            )
            if enrollment_id <= 0:
                raise DomainValidationError("Transcript integrity violation: invalid enrollment identifier")
            if enrollment_id in seen_enrollments:
                raise DomainValidationError(
                    f"Transcript integrity violation: duplicated enrollment_id={enrollment_id}"
                )
            seen_enrollments.add(enrollment_id)

    @staticmethod
    def validate_credit_totals(total_credits: int) -> None:
        if int(total_credits) < 0:
            raise DomainValidationError("total transcript credits cannot be negative")

    @staticmethod
    def validate_gpa_threshold(gpa: Decimal | None) -> None:
        if gpa is None:
            return
        if gpa < Decimal("0") or gpa > Decimal("4.50"):
            raise DomainValidationError("calculated GPA is outside allowed range")

    @staticmethod
    def validate_transcript_not_locked(student_status: str | None, student_profile_id: int) -> None:
        """Raise DomainValidationError if the student has GRADUATED — transcript is locked."""
        if str(student_status or "").strip().lower() == "graduated":
            raise DomainValidationError(
                f"Transcript for student_profile_id={student_profile_id} is locked: "
                "student has graduated and the official transcript is immutable"
            )
