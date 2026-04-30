"""Business rules for student_life module."""
from __future__ import annotations


class StudentLifeRules:
    """Encapsulates invariants for student life cases."""

    @staticmethod
    def validate_no_duplicate_active_disciplinary_case(
        existing_active_cases: list[object],
        *,
        student_id: str,
    ) -> None:
        """Raise ValueError if a student already has an active disciplinary case."""
        if existing_active_cases:
            raise ValueError(
                f"Student '{student_id}' already has an active disciplinary case. "
                "Resolve the existing case before opening a new one."
            )
