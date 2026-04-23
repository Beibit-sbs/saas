from __future__ import annotations

from typing import Any


class OperationalClassifier:
    """Classifies operational scenarios for future Brain Core routes."""

    def classify(self, signal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        event_type = str(signal.get("event_type") or "")
        return {
            "situation_type": "operational_risk",
            "severity": "medium",
            "urgency": "medium",
            "reasoning_path": f"operational::{event_type or 'default'}",
            "context_hint": context.get("operations") or {},
        }
