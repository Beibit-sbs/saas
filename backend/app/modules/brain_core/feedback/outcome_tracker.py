from __future__ import annotations

from typing import Any

from app.modules.brain_core.feedback.ingestor import FeedbackIngestor


class OutcomeTracker:
    """Stores outcomes linked to decisions for Brain Core v1."""

    def __init__(self) -> None:
        self._ingestor = FeedbackIngestor()
        self._outcomes: list[dict[str, Any]] = []

    def record(self, *, decision_id: str, tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        outcome = self._ingestor.ingest(decision_id=decision_id, tenant_id=tenant_id, payload=payload)
        self._outcomes.append(outcome)
        return outcome

    def list_outcomes(self) -> list[dict[str, Any]]:
        return list(self._outcomes)
