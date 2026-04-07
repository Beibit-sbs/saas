from __future__ import annotations

from decimal import Decimal

from app.core.module_helpers.service_validation import DomainValidationError


class DegreeProgressRules:
    @staticmethod
    def validate_program_requirement(requirement: object | None) -> None:
        if requirement is None:
            raise DomainValidationError("active program requirement is not configured")

    @staticmethod
    def validate_credit_totals(earned: int, minimum: int) -> None:
        if int(earned) < 0 or int(minimum) < 0:
            raise DomainValidationError("credit totals must be non-negative")

    @staticmethod
    def validate_gpa_threshold(gpa: Decimal | None, minimum_gpa: Decimal) -> bool:
        if gpa is None:
            return False
        return Decimal(str(gpa)) >= Decimal(str(minimum_gpa))

    @classmethod
    def validate_degree_completion(
        cls,
        *,
        earned_credits: int,
        minimum_credits: int,
        remaining_required_items: int,
        gpa_passed: bool,
    ) -> bool:
        cls.validate_credit_totals(earned_credits, minimum_credits)
        return earned_credits >= minimum_credits and remaining_required_items == 0 and gpa_passed
