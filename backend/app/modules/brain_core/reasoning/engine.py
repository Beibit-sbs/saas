from __future__ import annotations

from typing import Any

from app.modules.brain_core.reasoning.ai_adapter import OptionalAIReasoningAdapter
from app.modules.brain_core.reasoning.rules_engine import RulesEngine


class ReasoningEngine:
    """Builds a decision recommendation from classification and context."""

    def __init__(self) -> None:
        self._rules = RulesEngine()
        self._ai_adapter = OptionalAIReasoningAdapter()

    def decide(
        self,
        classification: dict[str, Any],
        context: dict[str, Any],
        *,
        knowledge: dict[str, Any] | None = None,
        enable_ai_reasoning: bool = False,
    ) -> dict[str, Any]:
        rules_result = self._rules.evaluate(classification, context)
        ai_trace: list[str] = ["ai_reasoning=disabled"]
        priority = rules_result["priority"]
        recommended_actions = list(rules_result.get("recommended_actions") or [])
        confidence = self._confidence_from_classification(classification)
        knowledge_items = list((knowledge or {}).get("items") or [])

        if knowledge_items:
            confidence = min(1.0, confidence + 0.03)
            ai_trace.append(f"knowledge_guidance={len(knowledge_items)}")

        if enable_ai_reasoning:
            ai_result = self._ai_adapter.suggest(
                classification=classification,
                context=context,
                rules_result=rules_result,
            )
            priority = str(ai_result.get("priority") or priority)
            recommended_actions = list(ai_result.get("recommended_actions") or recommended_actions)
            confidence = min(1.0, confidence + float(ai_result.get("confidence_boost") or 0.0))
            ai_trace = list(ai_result.get("trace") or ["ai_reasoning=enabled", "ai_reasoning=no_trace"])

        return {
            "decision_type": rules_result["decision_type"],
            "priority": priority,
            "recommended_actions": recommended_actions,
            "requires_approval": bool(rules_result.get("requires_approval", False)),
            "confidence_score": confidence,
            "severity_score": self._severity_score(classification),
            "urgency_score": self._urgency_score(classification),
            "ai_reasoning_enabled": enable_ai_reasoning,
            "ai_reasoning_trace": ai_trace,
            "knowledge_guidance": knowledge_items,
        }

    @staticmethod
    def _confidence_from_classification(classification: dict[str, Any]) -> float:
        severity = str(classification.get("severity") or "low")
        return {"high": 0.9, "medium": 0.75, "low": 0.6}.get(severity, 0.5)

    @staticmethod
    def _severity_score(classification: dict[str, Any]) -> float:
        severity = str(classification.get("severity") or "low")
        return {"high": 0.9, "medium": 0.6, "low": 0.3}.get(severity, 0.3)

    @staticmethod
    def _urgency_score(classification: dict[str, Any]) -> float:
        urgency = str(classification.get("urgency") or "low")
        return {"high": 0.9, "medium": 0.6, "low": 0.3}.get(urgency, 0.3)
