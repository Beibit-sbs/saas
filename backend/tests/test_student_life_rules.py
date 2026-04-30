"""Unit tests for StudentLifeRules business rules."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def test_validate_no_duplicate_active_disciplinary_case_raises_when_exists() -> None:
    """validate_no_duplicate_active_disciplinary_case raises ValueError when an active case exists."""
    from app.modules.student_life.business_rules import StudentLifeRules

    existing = [MagicMock()]  # non-empty list → duplicate
    with pytest.raises(ValueError, match="already has an active disciplinary case"):
        StudentLifeRules.validate_no_duplicate_active_disciplinary_case(
            existing, student_id="STU-001"
        )


def test_validate_no_duplicate_active_disciplinary_case_passes_when_empty() -> None:
    """validate_no_duplicate_active_disciplinary_case does NOT raise when there are no active cases."""
    from app.modules.student_life.business_rules import StudentLifeRules

    # Empty list → no active cases → no raise
    StudentLifeRules.validate_no_duplicate_active_disciplinary_case(
        [], student_id="STU-001"
    )
