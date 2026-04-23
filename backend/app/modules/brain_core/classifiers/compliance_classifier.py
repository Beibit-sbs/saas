from __future__ import annotations

from typing import Any


class ComplianceClassifier:
    """Classifies compliance-sensitive scenarios for future Brain Core routes."""

    def classify(self, signal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        event_type = str(signal.get("event_type") or "")
        return {
            "situation_type": "compliance_risk",
            "severity": "medium",
            "urgency": "medium",
            "reasoning_path": f"compliance::{event_type or 'default'}",
            "context_hint": context.get("platform") or {},
        }
