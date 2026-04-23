from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile


class PolicyTuningEngine:
    """Builds conservative tenant policy tuning suggestions from outcomes."""

    def suggest(self, *, profile: TenantPolicyProfile, metrics: dict[str, Any]) -> dict[str, Any]:
        total = int(metrics.get("total_outcomes") or 0)
        negative_rate = float(metrics.get("negative_rate") or 0.0)
        positive_rate = float(metrics.get("positive_rate") or 0.0)

        suggested = profile
        reason = "insufficient_data"

        if total >= 4 and negative_rate >= 0.5:
            suggested = TenantPolicyProfile(
                tenant_id=profile.tenant_id,
                autonomy_level=1,
                require_approval_for_critical=True,
                default_approval_role=profile.default_approval_role,
                enable_ai_reasoning=profile.enable_ai_reasoning,
            )
            reason = "high_negative_outcome_rate"
        elif total >= 5 and positive_rate >= 0.8 and negative_rate <= 0.1:
            suggested = TenantPolicyProfile(
                tenant_id=profile.tenant_id,
                autonomy_level=3,
                require_approval_for_critical=profile.require_approval_for_critical,
                default_approval_role=profile.default_approval_role,
                enable_ai_reasoning=profile.enable_ai_reasoning,
            )
            reason = "consistently_positive_outcomes"

        return {
            "reason": reason,
            "current_profile": asdict(profile),
            "suggested_profile": asdict(suggested),
            "changed": suggested != profile,
            "metrics": metrics,
        }
