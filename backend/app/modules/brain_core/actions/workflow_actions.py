from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


class InMemoryWorkflowActionDispatcher:
    """Minimal workflow action sink for first Brain Core scenario."""

    def __init__(self) -> None:
        self._cases: list[dict] = []

    def create_intervention_case(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "intervention",
            "student_id": payload.get("student_id"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "source": "brain_core",
                "event_type": payload.get("event_type"),
            },
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_supervision_task(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "thesis_supervision",
            "student_id": payload.get("student_id"),
            "thesis_id": payload.get("thesis_id"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "source": "brain_core",
                "event_type": payload.get("event_type"),
            },
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_workload_review_task(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "workload_review",
            "faculty_id": payload.get("faculty_id"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_collections_case(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "collections_recovery",
            "student_id": payload.get("student_id"),
            "balance_due": payload.get("balance_due"),
            "delinquency_days": payload.get("delinquency_days"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_replenishment_task(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "replenishment",
            "stock_item_id": payload.get("stock_item_id"),
            "stock_level": payload.get("stock_level"),
            "threshold": payload.get("threshold"),
            "projected_daily_usage": payload.get("projected_daily_usage"),
            "lead_time_days": payload.get("lead_time_days"),
            "auto_reorder": payload.get("auto_reorder"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def initiate_procurement_request(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "procurement_request",
            "budget_code": payload.get("budget_code"),
            "variance_amount": payload.get("variance_amount"),
            "variance_ratio": payload.get("variance_ratio"),
            "vendor_code": payload.get("vendor_code"),
            "contract_code": payload.get("contract_code"),
            "asset_code": payload.get("asset_code"),
            "sla_breach_rate": payload.get("sla_breach_rate"),
            "on_time_delivery_rate": payload.get("on_time_delivery_rate"),
            "risk_score": payload.get("risk_score"),
            "sla_target_met": payload.get("sla_target_met"),
            "stock_item_id": payload.get("stock_item_id"),
            "projected_daily_usage": payload.get("projected_daily_usage"),
            "lead_time_days": payload.get("lead_time_days"),
            "auto_reorder": payload.get("auto_reorder"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_procurement_approval_case(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        """A-015.2 — Create an approval workflow case for a submitted procurement request."""
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "procurement_approval",
            "request_id": payload.get("request_id"),
            "estimated_total": payload.get("estimated_total"),
            "priority": payload.get("priority"),
            "department_id": payload.get("department_id"),
            "procurement_risk_origin": payload.get("procurement_risk_origin"),
            "procurement_risk_evidence": payload.get("procurement_risk_evidence"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_accreditation_remediation_workflow(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "accreditation_remediation",
            "accreditation_id": payload.get("accreditation_id"),
            "old_status": payload.get("old_status"),
            "new_status": payload.get("new_status"),
            "risk_level": payload.get("risk_level"),
            "standard_code": payload.get("standard_code"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_platform_reliability_incident(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "platform_reliability_incident",
            "workflow_name": payload.get("workflow_name"),
            "integration_key": payload.get("integration_key"),
            "failure_count": payload.get("failure_count"),
            "error_rate": payload.get("error_rate"),
            "severity": payload.get("severity"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_research_remediation_workflow(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "research_remediation",
            "grant_id": payload.get("grant_id"),
            "publication_id": payload.get("publication_id"),
            "research_project_id": payload.get("research_project_id"),
            "days_to_deadline": payload.get("days_to_deadline"),
            "days_without_progress": payload.get("days_without_progress"),
            "pipeline_risk_score": payload.get("pipeline_risk_score"),
            "delayed_milestones": payload.get("delayed_milestones"),
            "lab_code": payload.get("lab_code"),
            "utilization_rate": payload.get("utilization_rate"),
            "idle_days": payload.get("idle_days"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_facility_incident_workflow(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "facility_incident",
            "facility_code": payload.get("facility_code"),
            "issue_type": payload.get("issue_type"),
            "severity": payload.get("severity"),
            "asset_code": payload.get("asset_code"),
            "asset_type": payload.get("asset_type"),
            "days_since_maintenance": payload.get("days_since_maintenance"),
            "expected_service_interval_days": payload.get("expected_service_interval_days"),
            "health_score": payload.get("health_score"),
            "meter_code": payload.get("meter_code"),
            "utility_type": payload.get("utility_type"),
            "usage_value": payload.get("usage_value"),
            "baseline_value": payload.get("baseline_value"),
            "spike_ratio": payload.get("spike_ratio"),
            "affected_buildings": payload.get("affected_buildings"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_cleaning_recovery_task(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "cleaning_recovery",
            "room_code": payload.get("room_code"),
            "building_code": payload.get("building_code"),
            "missed_count": payload.get("missed_count"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_student_support_case(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "student_support",
            "student_id": payload.get("student_id"),
            "concern_type": payload.get("concern_type"),
            "wellbeing_score": payload.get("wellbeing_score"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_disciplinary_review_case(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "disciplinary_review",
            "student_id": payload.get("student_id"),
            "incident_type": payload.get("incident_type"),
            "incident_severity": payload.get("incident_severity"),
            "incident_count_30d": payload.get("incident_count_30d"),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": "brain_core", "event_type": payload.get("event_type")},
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def create_attendance_recovery_plan(self, *, tenant_id: int, decision_id: str, payload: dict) -> dict:
        case = {
            "case_id": str(uuid4()),
            "tenant_id": int(tenant_id),
            "decision_id": decision_id,
            "case_type": "attendance_recovery",
            "student_id": payload.get("student_id"),
            "attendance_rate": payload.get("attendance_rate"),
            "course_id": payload.get("course_id"),
            "section_id": payload.get("section_id") or payload.get("source_entity_id"),
            "advisor_id": payload.get("advisor_id"),
            "source": "attendance_risk",
            "recommended_action": "attendance_recovery_plan",
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "source": "brain_core",
                "event_type": payload.get("event_type"),
                "idempotency_key": f"{tenant_id}:{payload.get('student_id')}:{payload.get('source_entity_id')}",
            },
        }
        self._cases.append(case)
        return {"status": "created", "item": case}

    def record_case_outcome(self, *, case_id: str, payload: dict, actor: str) -> dict:
        case = next((item for item in self._cases if item.get("case_id") == case_id), None)
        if case is None:
            return {"status": "not_found", "case_id": case_id}

        if case.get("outcome_id"):
            return {
                "status": "ignored",
                "case_id": case_id,
                "reason": "case_outcome_already_recorded",
                "item": case,
            }

        outcome_type = str(payload.get("outcome_type") or "completed").strip().lower()
        terminal_status = "closed" if outcome_type in {"cancelled", "canceled", "failed", "rejected"} else "resolved"

        case["status"] = terminal_status
        case["resolved_at"] = datetime.now(timezone.utc).isoformat()
        case["resolved_by"] = actor
        case["outcome"] = dict(payload)

        return {"status": "recorded", "item": case}

    def snapshot(self) -> list[dict]:
        return list(self._cases)
