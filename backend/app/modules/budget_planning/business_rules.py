"""Business rules for budget_planning module."""
from __future__ import annotations


class BudgetPlanningRules:
    """Encapsulates invariants for budget planning allocations."""

    @staticmethod
    def validate_no_over_allocation(
        already_allocated: float,
        requested_allocation: float,
        plan_total: float,
        *,
        plan_id: int,
    ) -> None:
        """Raise ValueError if adding the requested allocation would exceed the plan total."""
        if already_allocated + requested_allocation > plan_total:
            raise ValueError(
                "Allocation exceeds plan total_amount: "
                f"allocated={already_allocated + requested_allocation:.2f}, total={plan_total:.2f}"
            )
