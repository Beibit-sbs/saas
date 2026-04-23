from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovalRoute:
    required: bool
    role: str | None
    reason: str


class ApprovalPolicy:
    """Resolves approval route based on decision priority and tenant policy values."""

    def resolve(
        self,
        *,
        priority: str,
        require_approval_for_critical: bool,
        default_approval_role: str,
    ) -> ApprovalRoute:
        if require_approval_for_critical and str(priority) == "critical":
            return ApprovalRoute(
                required=True,
                role=default_approval_role,
                reason="critical_priority_requires_approval",
            )
        return ApprovalRoute(required=False, role=None, reason="approval_not_required")
