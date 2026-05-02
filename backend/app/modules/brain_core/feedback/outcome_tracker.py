from __future__ import annotations

from typing import Any

from app.modules.brain_core.feedback.ingestor import FeedbackIngestor


class OutcomeTracker:
    """Stores outcomes linked to decisions for Brain Core v1."""

    def __init__(self, quality_tracker: Any = None) -> None:
        self._ingestor = FeedbackIngestor()
        self._outcomes: list[dict[str, Any]] = []
        self._quality_tracker = quality_tracker

    def record(self, *, decision_id: str, tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        outcome = self._ingestor.ingest(decision_id=decision_id, tenant_id=tenant_id, payload=payload)
        self._outcomes.append(outcome)
        return outcome

    def record_outcome(self, outcome: dict[str, Any]) -> dict[str, Any]:
        """Convenience wrapper — accepts a flat dict with decision_id/tenant_id fields."""
        decision_id = str(outcome.get("decision_id") or "")
        tenant_id = int(outcome.get("tenant_id") or 0)
        recorded = self.record(decision_id=decision_id, tenant_id=tenant_id, payload=outcome)
        if self._quality_tracker is not None:
            self._quality_tracker.record(
                decision={"decision_id": decision_id, "tenant_id": tenant_id},
                outcome=outcome,
            )
        return recorded

    def list_outcomes(self) -> list[dict[str, Any]]:
        return list(self._outcomes)
