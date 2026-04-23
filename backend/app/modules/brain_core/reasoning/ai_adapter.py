from __future__ import annotations

from typing import Any


class OptionalAIReasoningAdapter:
    """Deterministic local AI-like adapter used as optional augmentation.

    This does not call external models; it enriches rule-based outputs
    and provides transparent reasoning traces.
    """

    def suggest(
        self,
        *,
        classification: dict[str, Any],
        context: dict[str, Any],
        rules_result: dict[str, Any],
    ) -> dict[str, Any]:
        severity = str(classification.get("severity") or "low")
        urgency = str(classification.get("urgency") or "low")
        attendance_rate = (context.get("academic") or {}).get("attendance_rate")
        grade_trend = (context.get("academic") or {}).get("grade_trend")

        priority = str(rules_result.get("priority") or "medium")
        recommended_actions = list(rules_result.get("recommended_actions") or [])
        trace = [
            "ai_adapter: enabled",
            f"ai_adapter: severity={severity}, urgency={urgency}",
            f"ai_adapter: base_priority={priority}",
        ]

        if attendance_rate is not None:
            trace.append(f"ai_adapter: attendance_rate={attendance_rate}")
        if grade_trend:
            trace.append(f"ai_adapter: grade_trend={grade_trend}")

        # Conservative uplift: only promote medium -> high for clear dual risk.
        if (
            priority == "medium"
            and severity == "high"
            and urgency == "high"
            and isinstance(attendance_rate, (int, float))
            and float(attendance_rate) < 0.5
        ):
            priority = "high"
            if "notify_faculty" not in recommended_actions:
                recommended_actions.append("notify_faculty")
            trace.append("ai_adapter: priority uplift medium->high due to compounded risk")
        else:
            trace.append("ai_adapter: no priority override")

        return {
            "priority": priority,
            "recommended_actions": recommended_actions,
            "confidence_boost": 0.03,
            "trace": trace,
        }
