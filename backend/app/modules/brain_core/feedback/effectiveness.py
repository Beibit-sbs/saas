from __future__ import annotations

from typing import Any


class EffectivenessEvaluator:
    """Evaluates outcome payloads into coarse effectiveness labels."""

    def evaluate(self, outcome_payload: dict[str, Any]) -> str:
        effectiveness = str(outcome_payload.get("effectiveness") or "").strip().lower()
        if effectiveness in {"positive", "neutral", "negative"}:
            return effectiveness

        outcome_type = str(outcome_payload.get("outcome_type") or "").strip().lower()
        if outcome_type in {"completed", "resolved"}:
            return "positive"
        if outcome_type in {"failed", "escalated"}:
            return "negative"
        return "neutral"
