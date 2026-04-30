"""Unit tests for BudgetPlanningRules business rules."""
from __future__ import annotations

import pytest


def test_validate_no_over_allocation_raises_when_exceeds() -> None:
    """validate_no_over_allocation raises ValueError when allocation would exceed plan total."""
    from app.modules.budget_planning.business_rules import BudgetPlanningRules

    with pytest.raises(ValueError, match="Allocation exceeds plan total_amount"):
        BudgetPlanningRules.validate_no_over_allocation(
            already_allocated=800.0,
            requested_allocation=300.0,
            plan_total=1000.0,
            plan_id=1,
        )


def test_validate_no_over_allocation_passes_within_limit() -> None:
    """validate_no_over_allocation does NOT raise when allocation is within plan total."""
    from app.modules.budget_planning.business_rules import BudgetPlanningRules

    # 800 + 200 == 1000 — exactly at limit, should pass
    BudgetPlanningRules.validate_no_over_allocation(
        already_allocated=800.0,
        requested_allocation=200.0,
        plan_total=1000.0,
        plan_id=1,
    )


def test_validate_no_over_allocation_zero_total_blocks_any_allocation() -> None:
    """When plan_total is 0, any positive allocation should be rejected."""
    from app.modules.budget_planning.business_rules import BudgetPlanningRules

    with pytest.raises(ValueError, match="Allocation exceeds plan total_amount"):
        BudgetPlanningRules.validate_no_over_allocation(
            already_allocated=0.0,
            requested_allocation=1.0,
            plan_total=0.0,
            plan_id=5,
        )
