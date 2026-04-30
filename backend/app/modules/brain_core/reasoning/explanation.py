from __future__ import annotations

import logging
from typing import Any

from app.platform.ai import llm_bridge

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """Builds explainability payload for each Brain decision."""

    def build(
        self,
        *,
        signal: dict[str, Any],
        context: dict[str, Any],
        classification: dict[str, Any],
        reasoning: dict[str, Any],
        knowledge: dict[str, Any] | None,
        policy_reason: str,
        approval_role: str | None,
    ) -> dict[str, Any]:
        event_type = signal.get("event_type")
        student_id = (signal.get("subject") or {}).get("student_id")
        attendance_rate = ((context.get("academic") or {}).get("attendance_rate"))
        grade_trend = ((context.get("academic") or {}).get("grade_trend"))

        factors: list[str] = [
            f"event_type={event_type}",
            f"situation_type={classification.get('situation_type')}",
            f"severity={classification.get('severity')}",
            f"urgency={classification.get('urgency')}",
        ]
        if attendance_rate is not None:
            factors.append(f"attendance_rate={attendance_rate}")
        if grade_trend:
            factors.append(f"grade_trend={grade_trend}")

        if reasoning.get("ai_reasoning_enabled"):
            factors.append("ai_reasoning=enabled")
            for step in list(reasoning.get("ai_reasoning_trace") or []):
                factors.append(str(step))
        else:
            factors.append("ai_reasoning=disabled")

        knowledge_items = list((knowledge or {}).get("items") or [])
        if knowledge_items:
            factors.append(f"knowledge_retrieved={len(knowledge_items)}")

        policy_notes = [policy_reason]
        if approval_role:
            policy_notes.append(f"approval_role={approval_role}")

        return {
            "summary": (
                f"Decision for student={student_id} based on {event_type}; "
                f"priority={reasoning.get('priority')}"
            ),
            "factors": factors,
            "policy_notes": policy_notes,
            "expected_outcome": "Actions dispatched or queued for approval based on policy.",
            "knowledge_items": knowledge_items,
            "llm_explanation": self._build_llm_explanation(
                event_type=event_type,
                situation_type=str(classification.get("situation_type", "")),
                severity=str(classification.get("severity", "")),
                urgency=str(classification.get("urgency", "")),
                factors=factors,
                reasoning=reasoning,
            ),
        }

    @staticmethod
    def _build_llm_explanation(
        *,
        event_type: str | None,
        situation_type: str,
        severity: str,
        urgency: str,
        factors: list[str],
        reasoning: dict[str, Any],
    ) -> str | None:
        """Call LLM bridge for enhanced explanation; return None if unavailable."""
        actions = list(reasoning.get("actions") or [])
        action_names = [
            a.get("action_type", str(a)) if isinstance(a, dict) else str(a)
            for a in actions
        ]
        try:
            return llm_bridge.generate_explanation(
                event_type=str(event_type or "unknown"),
                situation_type=situation_type,
                severity=severity,
                urgency=urgency,
                factors=factors,
                actions=action_names,
            )
        except Exception as exc:
            logger.debug("LLM explanation skipped: %s", exc)
            return None
