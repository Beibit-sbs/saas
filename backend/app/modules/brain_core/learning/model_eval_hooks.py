from __future__ import annotations

from typing import Any


class ModelEvaluationHooks:
    """Placeholder hooks for future model-based evaluations in Brain Core."""

    def evaluate_reasoning_trace(self, *, decision: dict[str, Any]) -> dict[str, Any]:
        trace = list(decision.get("ai_reasoning_trace") or [])
        return {
            "trace_steps": len(trace),
            "ai_reasoning_enabled": bool(decision.get("ai_reasoning_enabled")),
            "quality": "ok" if trace else "no_trace",
        }
