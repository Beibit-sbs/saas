from __future__ import annotations

from typing import Any


class DecisionQualityTracker:
    """Aggregates quality observations from decision outcomes."""

    def __init__(self) -> None:
        self._observations: list[dict[str, Any]] = []

    def record(self, *, decision: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
        observation = {
            "decision_id": decision.get("decision_id"),
            "tenant_id": decision.get("tenant_id"),
            "decision_type": decision.get("decision_type"),
            "priority": decision.get("priority"),
            "effectiveness": outcome.get("effectiveness", "neutral"),
            "outcome_type": outcome.get("outcome_type", "completed"),
        }
        self._observations.append(observation)
        return observation

    def metrics(self) -> dict[str, Any]:
        total = len(self._observations)
        positive = sum(1 for row in self._observations if row.get("effectiveness") == "positive")
        neutral = sum(1 for row in self._observations if row.get("effectiveness") == "neutral")
        negative = sum(1 for row in self._observations if row.get("effectiveness") == "negative")
        return {
            "total_outcomes": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "positive_rate": (positive / total) if total else 0.0,
            "negative_rate": (negative / total) if total else 0.0,
        }

    def metrics_for_tenant(self, tenant_id: int) -> dict[str, Any]:
        rows = [row for row in self._observations if int(row.get("tenant_id") or 0) == int(tenant_id)]
        total = len(rows)
        positive = sum(1 for row in rows if row.get("effectiveness") == "positive")
        neutral = sum(1 for row in rows if row.get("effectiveness") == "neutral")
        negative = sum(1 for row in rows if row.get("effectiveness") == "negative")
        return {
            "tenant_id": int(tenant_id),
            "total_outcomes": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "positive_rate": (positive / total) if total else 0.0,
            "negative_rate": (negative / total) if total else 0.0,
        }

    def list_observations(self) -> list[dict[str, Any]]:
        return list(self._observations)
