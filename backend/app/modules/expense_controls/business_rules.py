"""Business rules for expense_controls module."""
from __future__ import annotations


class ExpenseControlRules:
    """Encapsulates invariants for expense controls."""

    @staticmethod
    def validate_within_cost_center_budget(
        current_total: float,
        amount: float,
        budget_limit: float,
        *,
        cost_center_id: int,
    ) -> None:
        """Raise ValueError if adding this expense would exceed the cost center budget_limit."""
        if budget_limit > 0 and current_total + amount > budget_limit:
            raise ValueError(
                "Expense exceeds cost center budget_limit: "
                f"attempted_total={current_total + amount:.2f}, budget_limit={budget_limit:.2f}"
            )
