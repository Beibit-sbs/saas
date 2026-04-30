"""Unit tests for ExpenseControlRules business rules."""
from __future__ import annotations

import pytest


def test_validate_within_cost_center_budget_raises_when_exceeded() -> None:
    """validate_within_cost_center_budget raises ValueError when expense would exceed budget."""
    from app.modules.expense_controls.business_rules import ExpenseControlRules

    with pytest.raises(ValueError, match="Expense exceeds cost center budget_limit"):
        ExpenseControlRules.validate_within_cost_center_budget(
            current_total=800.0,
            amount=300.0,
            budget_limit=1000.0,
            cost_center_id=1,
        )


def test_validate_within_cost_center_budget_passes_when_within_limit() -> None:
    """validate_within_cost_center_budget does NOT raise when expense is within budget."""
    from app.modules.expense_controls.business_rules import ExpenseControlRules

    # 800 + 200 == 1000 — exactly at limit, should pass
    ExpenseControlRules.validate_within_cost_center_budget(
        current_total=800.0,
        amount=200.0,
        budget_limit=1000.0,
        cost_center_id=1,
    )


def test_validate_within_cost_center_budget_skips_when_no_budget_limit() -> None:
    """validate_within_cost_center_budget does NOT raise when budget_limit is 0 (unlimited)."""
    from app.modules.expense_controls.business_rules import ExpenseControlRules

    # budget_limit=0 means no limit → should never raise
    ExpenseControlRules.validate_within_cost_center_budget(
        current_total=9999.0,
        amount=9999.0,
        budget_limit=0.0,
        cost_center_id=1,
    )
