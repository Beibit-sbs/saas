"""Business rules for the university_core generic entity service."""
from __future__ import annotations


class UniversityCoreRules:
    """Encapsulates cross-entity invariants for the university_core entity service."""

    @staticmethod
    def validate_end_after_start(
        start_date: str | None,
        end_date: str | None,
        *,
        entity_name: str,
    ) -> None:
        """Raise ValueError if end_date is present and is not after start_date.

        Both values are expected as ISO-8601 date strings (YYYY-MM-DD).
        Validation is skipped when either value is absent/None.
        """
        if not start_date or not end_date:
            return
        if end_date <= start_date:
            raise ValueError(
                f"{entity_name}: end_date must be after start_date "
                f"(start_date={start_date}, end_date={end_date})"
            )
