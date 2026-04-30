"""XVII4 — Brain Optimization Engine.

Analyses domain signals and produces resource-allocation recommendations aimed at
improving platform efficiency and reducing risk across the tenant's operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_DOMAIN_PRIORITIES: dict[str, int] = {
    "academic": 10,
    "finance": 9,
    "faculty": 8,
    "operations": 7,
    "research": 5,
    "procurement": 5,
    "student_life": 6,
}

_ACTION_TEMPLATES: dict[str, str] = {
    "academic": "Increase advising capacity and launch early-alert intervention for affected students.",
    "finance": "Escalate collections workflow and schedule payment review with finance team.",
    "faculty": "Redistribute workload across faculty pool and review scheduling to prevent burnout.",
    "operations": "Dispatch facilities team and escalate maintenance SLA for affected assets.",
    "research": "Allocate additional lab time and review grant milestone deadlines.",
    "procurement": "Trigger auto-reorder for low-stock items and review vendor SLAs.",
    "student_life": "Activate wellbeing outreach and schedule counseling capacity review.",
}


class BrainOptimizer:
    """Resource-allocation optimizer for Brain Core signals."""

    def optimize(self, *, tenant_id: int, domain_signals: list[dict[str, Any]]) -> dict[str, Any]:
        """Return optimization recommendations for *domain_signals*.

        Args:
            tenant_id: The target tenant.
            domain_signals: List of ``{domain, metric, value, threshold?}`` dicts.

        Returns:
            Dict with ``tenant_id``, ``recommendations``, ``optimization_score``, ``generated_at``.
        """
        recommendations: list[dict[str, Any]] = []

        for signal in domain_signals:
            domain = str(signal.get("domain") or "unknown")
            metric = str(signal.get("metric") or "unknown")
            value = float(signal.get("value") or 0.0)
            threshold = float(signal.get("threshold") or 0.0)

            # Determine if the signal breaches its threshold
            breached = (threshold > 0.0 and value >= threshold) or (threshold == 0.0 and value > 0.0)
            if not breached:
                continue

            severity = self._severity(domain, value, threshold)
            expected_improvement = self._expected_improvement(domain, value, threshold)

            recommendations.append(
                {
                    "domain": domain,
                    "metric": metric,
                    "current_value": value,
                    "recommended_action": _ACTION_TEMPLATES.get(domain, "Review the metric and escalate as needed."),
                    "priority": severity,
                    "expected_improvement": round(expected_improvement, 4),
                    "rationale": (
                        f"Metric '{metric}' in domain '{domain}' has reached {value:.2f}"
                        + (f" (threshold: {threshold:.2f})" if threshold > 0 else "")
                        + ". Optimization action is recommended to reduce risk."
                    ),
                }
            )

        # Sort by priority weight descending
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 9))

        optimization_score = self._compute_score(recommendations, domain_signals)

        return {
            "tenant_id": tenant_id,
            "recommendations": recommendations,
            "optimization_score": round(optimization_score, 4),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _severity(domain: str, value: float, threshold: float) -> str:
        if threshold > 0:
            ratio = value / threshold
            if ratio >= 2.0:
                return "critical"
            if ratio >= 1.5:
                return "high"
            if ratio >= 1.0:
                return "medium"
            return "low"
        # No threshold — use raw domain priority
        base_priority = _DOMAIN_PRIORITIES.get(domain, 5)
        if base_priority >= 9:
            return "critical"
        if base_priority >= 7:
            return "high"
        if base_priority >= 5:
            return "medium"
        return "low"

    @staticmethod
    def _expected_improvement(domain: str, value: float, threshold: float) -> float:
        """Estimate proportional improvement if action is taken (0.0–1.0)."""
        base = _DOMAIN_PRIORITIES.get(domain, 5) / 10.0
        if threshold > 0 and value > 0:
            excess = max(0.0, (value - threshold) / value)
            return min(1.0, base * (1.0 + excess))
        return base * 0.5

    @staticmethod
    def _compute_score(recommendations: list[dict], domain_signals: list[dict]) -> float:
        """Overall optimization score: 1.0 = fully optimized, 0.0 = critical."""
        if not domain_signals:
            return 1.0
        weight_map = {"critical": 4, "high": 2, "medium": 1, "low": 0}
        total_weight = sum(weight_map.get(r["priority"], 0) for r in recommendations)
        max_weight = len(domain_signals) * 4
        if max_weight == 0:
            return 1.0
        return max(0.0, 1.0 - (total_weight / max_weight))
