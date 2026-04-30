"""Unit tests for UniversityCoreRules business rules."""
from __future__ import annotations

import pytest


def test_validate_end_after_start_raises_when_end_before_start() -> None:
    """validate_end_after_start raises ValueError when end_date < start_date."""
    from app.modules.university_core.business_rules import UniversityCoreRules

    with pytest.raises(ValueError, match="end_date must be after start_date"):
        UniversityCoreRules.validate_end_after_start(
            "2025-09-01",
            "2025-08-01",
            entity_name="faculty_contracts",
        )


def test_validate_end_after_start_raises_when_end_equals_start() -> None:
    """validate_end_after_start raises ValueError when end_date == start_date."""
    from app.modules.university_core.business_rules import UniversityCoreRules

    with pytest.raises(ValueError, match="end_date must be after start_date"):
        UniversityCoreRules.validate_end_after_start(
            "2025-09-01",
            "2025-09-01",
            entity_name="faculty_contracts",
        )


def test_validate_end_after_start_passes_when_end_after_start() -> None:
    """validate_end_after_start does NOT raise when end_date > start_date."""
    from app.modules.university_core.business_rules import UniversityCoreRules

    UniversityCoreRules.validate_end_after_start(
        "2025-01-01",
        "2026-01-01",
        entity_name="faculty_contracts",
    )


def test_validate_end_after_start_skips_when_end_date_absent() -> None:
    """validate_end_after_start does NOT raise when end_date is None (open-ended contract)."""
    from app.modules.university_core.business_rules import UniversityCoreRules

    UniversityCoreRules.validate_end_after_start(
        "2025-01-01",
        None,
        entity_name="faculty_contracts",
    )
