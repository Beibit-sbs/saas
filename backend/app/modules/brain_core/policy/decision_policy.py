from __future__ import annotations

from dataclasses import dataclass

from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile


@dataclass(frozen=True)
class PolicyValidationResult:
    approved: bool
    requires_approval: bool
    reason: str
    approval_role: str | None = None


class DecisionPolicyGuard:
    """Validates whether a decision can be auto-dispatched for a tenant."""

    def validate(
        self,
        *,
        tenant_id: int,
        decision_type: str,
        priority: str,
        profile: TenantPolicyProfile,
    ) -> PolicyValidationResult:
        if tenant_id <= 0:
            return PolicyValidationResult(
                approved=False,
                requires_approval=False,
                reason="missing_tenant_context",
            )

        if profile.autonomy_level < 0 or profile.autonomy_level > 4:
            return PolicyValidationResult(
                approved=False,
                requires_approval=True,
                reason="invalid_autonomy_level",
                approval_role=profile.default_approval_role,
            )

        # L0: Observe only. Brain can detect/analyze but never auto-dispatch.
        if profile.autonomy_level == 0:
            return PolicyValidationResult(
                approved=False,
                requires_approval=True,
                reason="autonomy_level_observe_only",
                approval_role=profile.default_approval_role,
            )

        # L1: Recommend only. All actions require explicit human approval.
        if profile.autonomy_level == 1:
            return PolicyValidationResult(
                approved=False,
                requires_approval=True,
                reason="autonomy_level_recommend_only",
                approval_role=profile.default_approval_role,
            )

        # A-013.1: Intervention decisions are autonomous by design.
        # Intervention case creation is a safeguard (not a severe action), and the intervention
        # system itself has tenant isolation, audit, and approval gates at the case/action level.
        # Allow autonomous dispatch for intervention decisions regardless of priority or autonomy level.
        if decision_type == "intervention":
            return PolicyValidationResult(
                approved=True,
                requires_approval=False,
                reason="intervention_decision_autonomous_by_design",
                approval_role=None,
            )

        if profile.require_approval_for_critical and priority == "critical":
            return PolicyValidationResult(
                approved=False,
                requires_approval=True,
                reason="critical_decision_requires_approval",
                approval_role=profile.default_approval_role,
            )

        # L2: Semi-autonomous.
        # Operational and compliance routes still require approval.
        if profile.autonomy_level == 2 and decision_type in {"operational", "compliance", "procurement"}:
            return PolicyValidationResult(
                approved=False,
                requires_approval=True,
                reason="autonomy_level_insufficient",
                approval_role=profile.default_approval_role,
            )

        # L3: Autonomous, except compliance still requires human sign-off.
        if profile.autonomy_level == 3 and decision_type == "compliance":
            return PolicyValidationResult(
                approved=False,
                requires_approval=True,
                reason="autonomy_level_3_compliance_requires_approval",
                approval_role=profile.default_approval_role,
            )

        return PolicyValidationResult(
            approved=True,
            requires_approval=False,
            reason="policy_passed",
            approval_role=None,
        )
