from __future__ import annotations

from typing import Any


class ScenarioSelector:
    """Maps classified situations into named execution scenarios."""

    _MAP = {
        "academic_risk": "student_risk",
        "faculty_risk": "faculty_overload",
        "financial_risk": "payment_recovery",
        "procurement_risk": "procurement_supply_chain",
        "operational_risk": "supply_management",
        "student_success_risk": "advanced_student_life",
        "optimization_opportunity": "faculty_overload",
        "compliance_risk": "student_risk",
    }

    def select(self, classification: dict[str, Any]) -> str:
        situation_type = str(classification.get("situation_type") or "")
        reasoning_path = str(classification.get("reasoning_path") or "")
        if reasoning_path.startswith("operations_"):
            return "campus_operations"
        if reasoning_path.startswith("procurement_"):
            return "procurement_supply_chain"
        if reasoning_path.startswith("student_life_"):
            return "advanced_student_life"
        # A-013.3: Scheduling conflict + enrollment capacity risk
        if reasoning_path.startswith("section_conflict_"):
            return "section_conflict"
        if reasoning_path.startswith("enrollment_capacity_risk_"):
            return "enrollment_capacity_risk"
        return self._MAP.get(situation_type, "student_risk")
