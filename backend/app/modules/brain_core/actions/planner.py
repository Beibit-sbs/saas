from __future__ import annotations

from typing import Any

from app.modules.brain_core.registry import DecisionRegistry


class ActionPlanner:
    """Builds executable action items from reasoning output."""

    def build_plan(self, *, decision_scenario: str, reasoning: dict[str, Any], signal: dict[str, Any]) -> list[dict[str, Any]]:
        config = DecisionRegistry.decisions.get(decision_scenario)
        if config is None:
            return []

        actions: list[dict[str, Any]] = []
        subject = dict(signal.get("subject") or {})
        payload = dict(signal.get("payload") or {})
        actor_student_id = subject.get("student_id") or payload.get("student_id")
        advisor_id = payload.get("advisor_id") or payload.get("assigned_advisor_id")
        faculty_id = subject.get("faculty_id") or payload.get("faculty_id")
        thesis_id = payload.get("thesis_id")
        delinquency_days = payload.get("delinquency_days")
        balance_due = payload.get("balance_due")
        budget_code = payload.get("budget_code")
        variance_amount = payload.get("variance_amount")
        variance_ratio = payload.get("variance_ratio")
        vendor_code = payload.get("vendor_code")
        contract_code = payload.get("contract_code")
        asset_code = payload.get("asset_code")
        vendor_sla_breach_rate = payload.get("sla_breach_rate")
        on_time_delivery_rate = payload.get("on_time_delivery_rate")
        contract_risk_score = payload.get("risk_score")
        sla_target_met = payload.get("sla_target_met")
        stock_item_id = payload.get("stock_item_id")
        stock_level = payload.get("stock_level")
        threshold = payload.get("threshold")
        projected_daily_usage = payload.get("projected_daily_usage")
        lead_time_days = payload.get("lead_time_days")
        auto_reorder = payload.get("auto_reorder")
        workload_ratio = payload.get("workload_ratio")
        accreditation_id = payload.get("accreditation_id")
        old_status = payload.get("old_status")
        new_status = payload.get("new_status")
        risk_level = payload.get("risk_level")
        standard_code = payload.get("standard_code")
        workflow_name = payload.get("workflow_name")
        integration_key = payload.get("integration_key")
        failure_count = payload.get("failure_count")
        error_rate = payload.get("error_rate")
        platform_severity = payload.get("severity")
        facility_code = payload.get("facility_code")
        issue_type = payload.get("issue_type")
        room_code = payload.get("room_code")
        building_code = payload.get("building_code")
        missed_count = payload.get("missed_count")
        asset_code = payload.get("asset_code")
        asset_type = payload.get("asset_type")
        days_since_maintenance = payload.get("days_since_maintenance")
        expected_service_interval_days = payload.get("expected_service_interval_days")
        health_score = payload.get("health_score")
        meter_code = payload.get("meter_code")
        utility_type = payload.get("utility_type")
        usage_value = payload.get("usage_value")
        baseline_value = payload.get("baseline_value")
        spike_ratio = payload.get("spike_ratio")
        affected_buildings = payload.get("affected_buildings")
        wellbeing_score = payload.get("wellbeing_score")
        incident_count_30d = payload.get("incident_count_30d")
        incident_severity = payload.get("incident_severity")
        concern_type = payload.get("concern_type")
        incident_type = payload.get("incident_type")
        grant_id = payload.get("grant_id")
        publication_id = payload.get("publication_id")
        research_project_id = payload.get("research_project_id")
        days_to_deadline = payload.get("days_to_deadline")
        days_without_progress = payload.get("days_without_progress")
        pipeline_risk_score = payload.get("pipeline_risk_score")
        delayed_milestones = payload.get("delayed_milestones")
        lab_code = payload.get("lab_code")
        utilization_rate = payload.get("utilization_rate")
        idle_days = payload.get("idle_days")

        for action_name in reasoning.get("recommended_actions") or []:
            if not action_name:
                continue
            action_type = config["action_map"].get(action_name)
            if action_type is None:
                continue

            actions.append(
                {
                    "name": action_name,
                    "action_type": action_type,
                    "requires_approval": bool(reasoning.get("requires_approval", False)),
                    "payload": {
                        "student_id": actor_student_id,
                        "advisor_id": advisor_id,
                        "faculty_id": faculty_id,
                        "thesis_id": thesis_id,
                        "delinquency_days": delinquency_days,
                        "balance_due": balance_due,
                        "budget_code": budget_code,
                        "variance_amount": variance_amount,
                        "variance_ratio": variance_ratio,
                        "vendor_code": vendor_code,
                        "contract_code": contract_code,
                        "asset_code": asset_code,
                        "sla_breach_rate": vendor_sla_breach_rate,
                        "on_time_delivery_rate": on_time_delivery_rate,
                        "risk_score": contract_risk_score,
                        "sla_target_met": sla_target_met,
                        "stock_item_id": stock_item_id,
                        "stock_level": stock_level,
                        "threshold": threshold,
                        "projected_daily_usage": projected_daily_usage,
                        "lead_time_days": lead_time_days,
                        "auto_reorder": auto_reorder,
                        "workload_ratio": workload_ratio,
                        "accreditation_id": accreditation_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "risk_level": risk_level,
                        "standard_code": standard_code,
                        "workflow_name": workflow_name,
                        "integration_key": integration_key,
                        "failure_count": failure_count,
                        "error_rate": error_rate,
                        "severity": platform_severity,
                        "facility_code": facility_code,
                        "issue_type": issue_type,
                        "room_code": room_code,
                        "building_code": building_code,
                        "missed_count": missed_count,
                        "asset_code": asset_code,
                        "asset_type": asset_type,
                        "days_since_maintenance": days_since_maintenance,
                        "expected_service_interval_days": expected_service_interval_days,
                        "health_score": health_score,
                        "meter_code": meter_code,
                        "utility_type": utility_type,
                        "usage_value": usage_value,
                        "baseline_value": baseline_value,
                        "spike_ratio": spike_ratio,
                        "affected_buildings": affected_buildings,
                        "wellbeing_score": wellbeing_score,
                        "incident_count_30d": incident_count_30d,
                        "incident_severity": incident_severity,
                        "concern_type": concern_type,
                        "incident_type": incident_type,
                        "grant_id": grant_id,
                        "publication_id": publication_id,
                        "research_project_id": research_project_id,
                        "days_to_deadline": days_to_deadline,
                        "days_without_progress": days_without_progress,
                        "pipeline_risk_score": pipeline_risk_score,
                        "delayed_milestones": delayed_milestones,
                        "lab_code": lab_code,
                        "utilization_rate": utilization_rate,
                        "idle_days": idle_days,
                        "event_type": signal.get("event_type"),
                    },
                }
            )

        return actions
