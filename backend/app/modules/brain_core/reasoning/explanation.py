from __future__ import annotations

from typing import Any


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
        }
