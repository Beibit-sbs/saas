from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import pytest

from app.modules.brain_core.actions.dispatcher import ActionDispatcher
from app.modules.brain_core.service import BrainCoreService


@pytest.fixture(autouse=True)
def _stub_student_success_context_source() -> None:
    # Keep Brain Core unit tests independent from optional/unmigrated domain tables.
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_academic_context",
                return_value={"student_profile": None, "academic_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_student_success_context",
                return_value={
                    "active_interventions": 0,
                    "open_advising_tasks": 0,
                    "student_life_health_snapshot": {
                        "open_counseling_cases": 0,
                        "active_accommodations": 0,
                        "disciplinary_incidents_30d": 0,
                        "at_risk_students": 0,
                    },
                },
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_faculty_context",
                return_value={"faculty_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_finance_context",
                return_value={"billing_health_snapshot": {}, "procurement_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_operations_context",
                return_value={"operations_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_platform_context",
                return_value={"platform_health_snapshot": {}},
            )
        )
        yield


def test_student_risk_signal_full_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-1",
        "tenant_id": 101,
        "correlation_id": "corr-1",
        "event_type": "academic.attendance_risk.detected",
        "subject": {
            "student_id": "STU-1",
            "course_id": "COURSE-1",
            "section_id": "SEC-1",
            "faculty_id": "FAC-1",
        },
        "payload": {
            "student_id": "STU-1",
            "attendance_rate": 0.35,
            "grade_trend": "declining",
            "advisor_id": "ADV-1",
            "faculty_id": "FAC-1",
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC-1",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    # A-013.1 contract: academic risk routes to intervention decisions.
    assert result["decision"]["decision_type"] == "intervention"
    assert result["decision"]["priority"] == "critical"
    # Intervention decisions are autonomous by policy design.
    assert result["decision"]["status"] == "dispatched"
    assert "explanation" in result["decision"]
    assert "summary" in result["decision"]["explanation"]
    assert result["context"]["knowledge"]["retrieved"] >= 1
    assert result["decision"]["explanation"]["knowledge_items"][0]["document_id"] == "playbook.student_attendance_outreach"
    assert len(result["action_plan"]) >= 2
    assert any(item["action"] == "create_intervention_case" for item in result["dispatch_results"])


def test_signal_without_tenant_is_rejected() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-2",
        "tenant_id": None,
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": "STU-2"},
        "payload": {"attendance_rate": 0.25},
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_tenant_context"


def test_thesis_delay_full_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-3",
        "tenant_id": 101,
        "correlation_id": "corr-3",
        "event_type": "thesis.status_changed",
        "subject": {
            "student_id": "STU-3",
            "faculty_id": "FAC-3",
        },
        "payload": {
            "student_id": "STU-3",
            "thesis_id": "TH-3",
            "advisor_id": "ADV-3",
            "faculty_id": "FAC-3",
            "days_since_last_milestone": 90,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-3",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "intervention"
    assert result["decision"]["priority"] == "high"
    assert result["decision"]["status"] == "dispatched"
    assert "explanation" in result["decision"]
    assert any(item["action"] == "create_intervention_case" for item in result["dispatch_results"])
    assert any(item["action"] == "create_supervision_task" for item in result["dispatch_results"])


def test_critical_decision_can_be_approved_and_dispatched() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-4",
        "tenant_id": 101,
        "correlation_id": "corr-4",
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": "STU-4", "faculty_id": "FAC-4"},
        "payload": {
            "student_id": "STU-4",
            "attendance_rate": 0.30,
            "advisor_id": "ADV-4",
            "faculty_id": "FAC-4",
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC-4",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    assert processed["decision"]["decision_type"] == "intervention"
    assert processed["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_intervention_case" for item in processed["dispatch_results"])


def test_what_if_simulation_previews_forecast_without_persisting_state() -> None:
    service = BrainCoreService()

    simulated = service.simulate_what_if(
        signal={
            "signal_id": "sig-e5-1",
            "tenant_id": 905,
            "correlation_id": "corr-e5-1",
            "event_type": "operations.consumable_stock.low",
            "subject": {},
            "payload": {
                "stock_item_id": "ITEM-E5-1",
                "stock_level": 6,
                "threshold": 10,
                "projected_daily_usage": 2,
                "lead_time_days": 5,
                "auto_reorder": True,
                "source_entity_type": "inventory_item",
                "source_entity_id": "ITEM-E5-1",
            },
            "metadata": {"mode": "what_if"},
        },
        forecast_horizon_days=21,
        simulation_label="supply stress test",
        policy_override={
            "autonomy_level": 4,
            "require_approval_for_critical": True,
            "default_approval_role": "ops_manager",
            "enable_ai_reasoning": False,
        },
    )

    assert simulated["status"] == "simulated"
    assert simulated["decision"]["status"] == "simulated"
    assert simulated["decision"]["priority"] == "high"
    assert simulated["context"]["knowledge"]["retrieved"] >= 1
    assert simulated["forecast"]["horizon_days"] == 21
    assert simulated["forecast"]["dispatchable_now"] is True
    assert simulated["dispatch_results"] == []
    # A-009 tenant isolation contract: list APIs require explicit tenant_id.
    assert service.list_signals(tenant_id=905) == []
    assert service.list_decisions(tenant_id=905) == []


def test_pending_decision_can_be_cancelled() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-5",
        "tenant_id": 101,
        "correlation_id": "corr-5",
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": "STU-5"},
        "payload": {
            "student_id": "STU-5",
            "attendance_rate": 0.35,
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC-5",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    decision_id = processed["decision"]["decision_id"]

    cancelled = service.cancel_decision(decision_id, actor="ops@tenant", reason="manual_review_needed")
    assert cancelled["status"] == "cancelled"
    assert cancelled["decision"]["status"] == "cancelled"


def test_record_outcome_updates_metrics() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-6",
        "tenant_id": 101,
        "correlation_id": "corr-6",
        "event_type": "thesis.status_changed",
        "subject": {"student_id": "STU-6", "faculty_id": "FAC-6"},
        "payload": {
            "student_id": "STU-6",
            "thesis_id": "TH-6",
            "advisor_id": "ADV-6",
            "faculty_id": "FAC-6",
            "days_since_last_milestone": 70,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-6",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    decision_id = processed["decision"]["decision_id"]

    outcome_result = service.record_outcome(
        decision_id,
        actor="ops@tenant",
        payload={"outcome_type": "completed", "effectiveness": "positive", "notes": "closed_on_time"},
    )

    assert outcome_result["status"] == "recorded"
    assert outcome_result["decision"]["status"] == "completed"

    metrics = service.learning_metrics()
    assert metrics["total_outcomes"] == 1
    assert metrics["positive"] == 1


def test_record_dispatch_outcome_closes_dispatched_case_and_updates_learning_loop() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-6b",
        "tenant_id": 101,
        "correlation_id": "corr-6b",
        "event_type": "thesis.status_changed",
        "subject": {"student_id": "STU-6B", "faculty_id": "FAC-6B"},
        "payload": {
            "student_id": "STU-6B",
            "thesis_id": "TH-6B",
            "advisor_id": "ADV-6B",
            "faculty_id": "FAC-6B",
            "days_since_last_milestone": 90,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-6B",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    dispatch_results = processed.get("dispatch_results") or []
    assert dispatch_results
    case_result = next(
        (
            item
            for item in dispatch_results
            if isinstance(item.get("item"), dict) and item["item"].get("case_id")
        ),
        None,
    )
    assert case_result is not None
    case_id = case_result["item"]["case_id"]

    outcome_result = service.record_dispatch_outcome(
        case_id,
        actor="ops@tenant",
        payload={"outcome_type": "completed", "effectiveness": "positive", "notes": "case_resolved"},
    )

    assert outcome_result["status"] == "recorded"
    assert outcome_result["decision"]["status"] == "completed"
    assert outcome_result["decision"]["decision_id"] == processed["decision"]["decision_id"]
    assert outcome_result["case"]["status"] == "resolved"
    assert outcome_result["case"]["resolved_by"] == "ops@tenant"

    metrics = service.learning_metrics()
    assert metrics["total_outcomes"] == 1
    assert metrics["positive"] == 1


def test_dispatcher_case_outcome_auto_invokes_feedback_callback() -> None:
    observed: dict[str, object] = {}

    def on_case_outcome(case: dict, payload: dict, actor: str) -> dict:
        observed["case"] = dict(case)
        observed["payload"] = dict(payload)
        observed["actor"] = actor
        return {
            "status": "recorded",
            "decision": {"decision_id": case["decision_id"], "status": "completed"},
            "outcome": {"effectiveness": payload["effectiveness"]},
        }

    dispatcher = ActionDispatcher(on_workflow_case_outcome=on_case_outcome)
    dispatch_result = dispatcher.dispatch(
        tenant_id=101,
        decision_id="decision-6c",
        actions=[
            {
                "name": "create_supervision_task",
                "payload": {
                    "student_id": "STU-6C",
                    "thesis_id": "TH-6C",
                    "event_type": "thesis.status_changed",
                },
            }
        ],
    )

    case_id = dispatch_result[0]["item"]["case_id"]
    feedback_result = dispatcher.record_workflow_case_outcome(
        case_id=case_id,
        actor="workflow@system",
        payload={"outcome_type": "completed", "effectiveness": "positive", "notes": "workflow_done"},
    )

    assert feedback_result["status"] == "recorded"
    assert feedback_result["decision"]["status"] == "completed"
    assert feedback_result["case"]["status"] == "resolved"
    assert feedback_result["case"]["resolved_by"] == "workflow@system"
    assert observed["actor"] == "workflow@system"
    assert observed["payload"] == {
        "outcome_type": "completed",
        "effectiveness": "positive",
        "notes": "workflow_done",
    }


def test_observability_metrics_and_traces_are_recorded() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-7",
        "tenant_id": 101,
        "correlation_id": "corr-7",
        "event_type": "thesis.status_changed",
        "subject": {"student_id": "STU-7", "faculty_id": "FAC-7"},
        "payload": {
            "student_id": "STU-7",
            "thesis_id": "TH-7",
            "advisor_id": "ADV-7",
            "faculty_id": "FAC-7",
            "days_since_last_milestone": 75,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-7",
        },
        "metadata": {},
    }

    service.process_signal(signal)

    snapshot = service.observability_metrics()
    assert snapshot["counters"]["signals_received_total"] >= 1
    assert snapshot["counters"]["decisions_created_total"] >= 1
    assert snapshot["traces_total"] >= 1


def test_faculty_overload_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-8",
        "tenant_id": 101,
        "correlation_id": "corr-8",
        "event_type": "faculty.workload_overload.detected",
        "subject": {"faculty_id": "FAC-8"},
        "payload": {
            "faculty_id": "FAC-8",
            "workload_ratio": 1.45,
            "source_entity_type": "faculty_workload",
            "source_entity_id": "FAC-8",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "optimization"
    assert result["decision"]["priority"] == "high"
    assert result["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_workload_review_task" for item in result["dispatch_results"])


def test_payment_recovery_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-9",
        "tenant_id": 101,
        "correlation_id": "corr-9",
        "event_type": "finance.payment_overdue.detected",
        "subject": {"student_id": "STU-9"},
        "payload": {
            "student_id": "STU-9",
            "delinquency_days": 60,
            "balance_due": 1200.0,
            "source_entity_type": "billing_account",
            "source_entity_id": "STU-9",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "risk"
    # A-013.2 contract: overdue recovery executes as high-priority autonomous flow.
    assert result["decision"]["priority"] == "high"
    assert result["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_collections_case" for item in result["dispatch_results"])


def test_budget_variance_procurement_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-9b",
        "tenant_id": 101,
        "correlation_id": "corr-9b",
        "event_type": "finance.budget_variance.threshold_reached",
        "subject": {},
        "payload": {
            "budget_code": "BUD-OPS-101",
            "variance_amount": 31000.0,
            "variance_ratio": 0.22,
            "vendor_code": "VEN-101",
            "contract_code": "CON-101",
            "asset_code": "AST-101",
            "source_entity_type": "budget_variance",
            "source_entity_id": "BUD-OPS-101",
        },
        "metadata": {},
    }

    service.update_policy_profile(
        tenant_id=101,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="procurement_lead",
        enable_ai_reasoning=False,
        actor="ops@brain",
    )

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "procurement"
    assert result["decision"]["priority"] == "high"
    assert result["decision"]["status"] == "dispatched"
    assert any(item["action"] == "initiate_procurement_request" for item in result["dispatch_results"])


def test_supply_management_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-10",
        "tenant_id": 101,
        "correlation_id": "corr-10",
        "event_type": "operations.consumable_stock.low",
        "subject": {},
        "payload": {
            "stock_item_id": "ITEM-10",
            "stock_level": 4.0,
            "threshold": 10.0,
            "source_entity_type": "inventory_item",
            "source_entity_id": "ITEM-10",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "operational"
    assert result["decision"]["priority"] == "high"
    assert result["decision"]["status"] == "approval_pending"
    assert result["dispatch_results"] == []

    approved = service.approve_decision(result["decision"]["decision_id"], actor="ops_manager@tenant")
    assert approved["status"] == "approved"
    assert any(item["action"] == "create_replenishment_task" for item in approved["dispatch_results"])


def test_supply_management_forecast_auto_reorder_flow_processed() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-10b",
        "tenant_id": 101,
        "correlation_id": "corr-10b",
        "event_type": "operations.consumable_stock.low",
        "subject": {},
        "payload": {
            "stock_item_id": "ITEM-FORECAST-10",
            "stock_level": 18.0,
            "threshold": 10.0,
            "projected_daily_usage": 3.5,
            "lead_time_days": 6,
            "auto_reorder": True,
            "source_entity_type": "inventory_item",
            "source_entity_id": "ITEM-FORECAST-10",
        },
        "metadata": {},
    }

    service.update_policy_profile(
        tenant_id=101,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="ops_manager",
        enable_ai_reasoning=False,
        actor="ops@brain",
    )

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "operational"
    assert result["decision"]["priority"] == "high"
    assert result["decision"]["status"] == "dispatched"
    assert any(item["action"] == "initiate_procurement_request" for item in result["dispatch_results"])


def test_policy_tuning_applies_conservative_profile_on_negative_outcomes() -> None:
    service = BrainCoreService()

    for idx in range(1, 5):
        signal = {
            "signal_id": f"sig-pt-{idx}",
            "tenant_id": 202,
            "correlation_id": f"corr-pt-{idx}",
            "event_type": "thesis.status_changed",
            "subject": {"student_id": f"STU-PT-{idx}", "faculty_id": "FAC-PT"},
            "payload": {
                "student_id": f"STU-PT-{idx}",
                "thesis_id": f"TH-PT-{idx}",
                "advisor_id": "ADV-PT",
                "faculty_id": "FAC-PT",
                "days_since_last_milestone": 90,
                "source_entity_type": "thesis",
                "source_entity_id": f"TH-PT-{idx}",
            },
            "metadata": {},
        }
        processed = service.process_signal(signal)
        decision_id = processed["decision"]["decision_id"]
        service.record_outcome(
            decision_id,
            actor="ops@tenant",
            payload={"outcome_type": "completed", "effectiveness": "negative"},
        )

    suggestion = service.policy_tuning_suggestion(202)
    assert suggestion["changed"] is True
    assert suggestion["reason"] == "high_negative_outcome_rate"
    assert suggestion["suggested_profile"]["autonomy_level"] == 1
    assert suggestion["suggested_profile"]["require_approval_for_critical"] is True

    applied = service.apply_policy_tuning(202, actor="ops@tenant")
    assert applied["status"] == "applied"
    assert applied["changed"] is True
    assert applied["profile"]["autonomy_level"] == 1


def test_ai_reasoning_disabled_by_default() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-ai-off",
        "tenant_id": 303,
        "correlation_id": "corr-ai-off",
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": "STU-AI-OFF"},
        "payload": {
            "student_id": "STU-AI-OFF",
            "attendance_rate": 0.45,
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC-AI-OFF",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["decision"]["ai_reasoning_enabled"] is False
    assert "ai_reasoning=disabled" in result["decision"]["ai_reasoning_trace"]


def test_ai_reasoning_enabled_via_policy_profile() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        404,
        autonomy_level=2,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=True,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-ai-on",
        "tenant_id": 404,
        "correlation_id": "corr-ai-on",
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": "STU-AI-ON"},
        "payload": {
            "student_id": "STU-AI-ON",
            "attendance_rate": 0.45,
            "grade_trend": "declining",
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC-AI-ON",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["decision"]["ai_reasoning_enabled"] is True
    assert any("ai_adapter:" in step for step in result["decision"]["ai_reasoning_trace"])
    assert "ai_reasoning=enabled" in result["decision"]["explanation"]["factors"]


def test_dispatch_failure_retries_and_escalates_after_three_attempts() -> None:
    service = BrainCoreService()
    attempts = {"count": 0}

    def always_fail(**_: object) -> dict:
        attempts["count"] += 1
        raise RuntimeError("workflow_temporarily_unavailable")

    service._dispatcher._workflow.create_supervision_task = always_fail  # type: ignore[attr-defined]

    signal = {
        "signal_id": "sig-fail-dispatch",
        "tenant_id": 505,
        "correlation_id": "corr-fail-dispatch",
        "event_type": "thesis.status_changed",
        "subject": {"student_id": "STU-FAIL", "faculty_id": "FAC-FAIL"},
        "payload": {
            "student_id": "STU-FAIL",
            "thesis_id": "TH-FAIL",
            "advisor_id": "ADV-FAIL",
            "faculty_id": "FAC-FAIL",
            "days_since_last_milestone": 90,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-FAIL",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    supervision_dispatch = next(
        item for item in result["dispatch_results"] if item.get("action") == "create_supervision_task"
    )
    assert supervision_dispatch["status"] == "escalated"
    assert supervision_dispatch["reason"] == "dispatch_failed_after_retries"
    assert supervision_dispatch["attempts"] == 3
    assert attempts["count"] == 3

    metrics = service.observability_metrics()
    assert metrics["counters"]["action_dispatch_failure_total"] >= 1


def test_accreditation_risk_creates_compliance_decision_and_remediation_workflow() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-c7-1",
        "tenant_id": 606,
        "correlation_id": "corr-c7-1",
        "event_type": "accreditation.status_changed",
        "subject": {"faculty_id": "FAC-COMP-1"},
        "payload": {
            "accreditation_id": "ACC-2026-A",
            "old_status": "compliant",
            "new_status": "at_risk",
            "risk_level": "high",
            "standard_code": "STD-7.3",
            "source_entity_type": "accreditation_record",
            "source_entity_id": "ACC-2026-A",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "compliance"
    assert processed["decision"]["priority"] == "critical"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["dispatch_results"] == []

    approved = service.approve_decision(processed["decision"]["decision_id"], actor="compliance_lead@tenant")
    assert approved["status"] == "approved"
    assert approved["decision"]["status"] == "dispatched"
    assert any(
        item["action"] == "create_accreditation_remediation_workflow"
        for item in approved["dispatch_results"]
    )


def test_platform_workflow_failed_creates_reliability_incident_after_approval() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-c8-1",
        "tenant_id": 707,
        "correlation_id": "corr-c8-1",
        "event_type": "platform.workflow.failed",
        "subject": {},
        "payload": {
            "workflow_name": "nightly_sync",
            "failure_count": 4,
            "severity": "high",
            "source_entity_type": "workflow_job",
            "source_entity_id": "nightly_sync",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "critical"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["dispatch_results"] == []

    approved = service.approve_decision(processed["decision"]["decision_id"], actor="platform_lead@tenant")
    assert approved["status"] == "approved"
    assert approved["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_platform_reliability_incident" for item in approved["dispatch_results"])
    assert any(item["action"] == "notify_platform" for item in approved["dispatch_results"])


def test_platform_integration_degraded_dispatches_reliability_incident_without_approval() -> None:
    service = BrainCoreService()

    service.update_policy_profile(
        707,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-c8-2",
        "tenant_id": 707,
        "correlation_id": "corr-c8-2",
        "event_type": "platform.integration.degraded",
        "subject": {},
        "payload": {
            "integration_key": "sis_gateway",
            "error_rate": 0.06,
            "severity": "medium",
            "source_entity_type": "integration_channel",
            "source_entity_id": "sis_gateway",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "high"
    assert processed["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_platform_reliability_incident" for item in processed["dispatch_results"])


def test_autonomy_level_0_observe_only_requires_approval_for_preventive() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        808,
        autonomy_level=0,
        require_approval_for_critical=False,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-c9-l0",
        "tenant_id": 808,
        "correlation_id": "corr-c9-l0",
        "event_type": "thesis.status_changed",
        "subject": {"student_id": "STU-L0", "faculty_id": "FAC-L0"},
        "payload": {
            "student_id": "STU-L0",
            "thesis_id": "TH-L0",
            "days_since_last_milestone": 10,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-L0",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["decision"]["policy_reason"] == "autonomy_level_observe_only"


def test_autonomy_level_1_recommend_only_requires_approval_for_preventive() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        809,
        autonomy_level=1,
        require_approval_for_critical=False,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-c9-l1",
        "tenant_id": 809,
        "correlation_id": "corr-c9-l1",
        "event_type": "thesis.status_changed",
        "subject": {"student_id": "STU-L1", "faculty_id": "FAC-L1"},
        "payload": {
            "student_id": "STU-L1",
            "thesis_id": "TH-L1",
            "days_since_last_milestone": 10,
            "source_entity_type": "thesis",
            "source_entity_id": "TH-L1",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["decision"]["policy_reason"] == "autonomy_level_recommend_only"


def test_autonomy_level_2_requires_approval_for_operational() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        810,
        autonomy_level=2,
        require_approval_for_critical=False,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-c9-l2",
        "tenant_id": 810,
        "correlation_id": "corr-c9-l2",
        "event_type": "operations.consumable_stock.low",
        "subject": {},
        "payload": {
            "stock_item_id": "ITEM-L2",
            "stock_level": 8.0,
            "threshold": 10.0,
            "source_entity_type": "inventory_item",
            "source_entity_id": "ITEM-L2",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["decision"]["policy_reason"] == "autonomy_level_insufficient"


def test_autonomy_level_3_requires_approval_for_compliance() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        811,
        autonomy_level=3,
        require_approval_for_critical=False,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-c9-l3",
        "tenant_id": 811,
        "correlation_id": "corr-c9-l3",
        "event_type": "accreditation.status_changed",
        "subject": {},
        "payload": {
            "accreditation_id": "ACC-L3",
            "old_status": "compliant",
            "new_status": "warning",
            "risk_level": "medium",
            "source_entity_type": "accreditation_record",
            "source_entity_id": "ACC-L3",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    assert processed["decision"]["decision_type"] == "compliance"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["decision"]["policy_reason"] == "autonomy_level_3_compliance_requires_approval"


def test_autonomy_level_4_allows_compliance_autodispatch_when_not_critical() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        812,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-c9-l4",
        "tenant_id": 812,
        "correlation_id": "corr-c9-l4",
        "event_type": "accreditation.status_changed",
        "subject": {},
        "payload": {
            "accreditation_id": "ACC-L4",
            "old_status": "compliant",
            "new_status": "warning",
            "risk_level": "medium",
            "source_entity_type": "accreditation_record",
            "source_entity_id": "ACC-L4",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)
    assert processed["decision"]["decision_type"] == "compliance"
    assert processed["decision"]["status"] == "dispatched"
    assert processed["decision"]["policy_reason"] == "policy_passed"


def test_research_grant_deadline_signal_dispatches_research_remediation_workflow() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-d1-1",
        "tenant_id": 901,
        "correlation_id": "corr-d1-1",
        "event_type": "research.grant_deadline.approaching",
        "subject": {},
        "payload": {
            "grant_id": "GRANT-2026-01",
            "research_project_id": "RP-1",
            "days_to_deadline": 10,
            "source_entity_type": "grant_record",
            "source_entity_id": "GRANT-2026-01",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["priority"] == "high"
    assert processed["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_research_remediation_workflow" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_research_office" for item in processed["dispatch_results"])


def test_research_publication_stagnant_medium_dispatches_research_remediation_only() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-d1-2",
        "tenant_id": 901,
        "correlation_id": "corr-d1-2",
        "event_type": "research.publication_stagnant",
        "subject": {},
        "payload": {
            "publication_id": "PUB-2026-22",
            "research_project_id": "RP-2",
            "days_without_progress": 30,
            "source_entity_type": "publication_record",
            "source_entity_id": "PUB-2026-22",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["priority"] == "medium"
    assert processed["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_research_remediation_workflow" for item in processed["dispatch_results"])
    assert not any(item["action"] == "notify_research_office" for item in processed["dispatch_results"])


def test_research_grant_pipeline_risk_high_dispatches_workflow_and_notification() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-e3-1",
        "tenant_id": 901,
        "correlation_id": "corr-e3-1",
        "event_type": "research.grant_pipeline.at_risk",
        "subject": {},
        "payload": {
            "grant_id": "GRANT-PIPE-1",
            "research_project_id": "RP-PIPE-1",
            "pipeline_risk_score": 0.82,
            "delayed_milestones": 3,
            "source_entity_type": "grant_pipeline",
            "source_entity_id": "GRANT-PIPE-1",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["priority"] == "high"
    assert any(item["action"] == "create_research_remediation_workflow" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_research_office" for item in processed["dispatch_results"])


def test_research_lab_utilization_low_medium_dispatches_workflow_only() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-e3-2",
        "tenant_id": 901,
        "correlation_id": "corr-e3-2",
        "event_type": "research.lab_utilization.low",
        "subject": {},
        "payload": {
            "lab_code": "LAB-LOW-1",
            "research_project_id": "RP-LAB-1",
            "utilization_rate": 0.55,
            "idle_days": 12,
            "source_entity_type": "research_lab",
            "source_entity_id": "LAB-LOW-1",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["priority"] == "medium"
    assert any(item["action"] == "create_research_remediation_workflow" for item in processed["dispatch_results"])
    assert not any(item["action"] == "notify_research_office" for item in processed["dispatch_results"])


def test_operations_facility_issue_signal_dispatches_incident_workflow_and_notification() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        902,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-d2-1",
        "tenant_id": 902,
        "correlation_id": "corr-d2-1",
        "event_type": "operations.facility_issue.reported",
        "subject": {},
        "payload": {
            "facility_code": "BLDG-C-HVAC",
            "issue_type": "hvac_failure",
            "severity": "high",
            "source_entity_type": "facility_issue",
            "source_entity_id": "BLDG-C-HVAC",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "high"
    assert any(item["action"] == "create_facility_incident_workflow" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_facilities_team" for item in processed["dispatch_results"])


def test_operations_cleaning_missed_medium_dispatches_recovery_task_only() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        902,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-d2-2",
        "tenant_id": 902,
        "correlation_id": "corr-d2-2",
        "event_type": "operations.cleaning_service.missed",
        "subject": {},
        "payload": {
            "room_code": "ROOM-45",
            "building_code": "BLDG-C",
            "missed_count": 1,
            "source_entity_type": "cleaning_check",
            "source_entity_id": "ROOM-45",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "medium"
    assert any(item["action"] == "create_cleaning_recovery_task" for item in processed["dispatch_results"])
    assert not any(item["action"] == "notify_facilities_team" for item in processed["dispatch_results"])


def test_campus_security_incident_high_dispatches_incident_workflow_and_notification() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        902,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-vi1-1",
        "tenant_id": 902,
        "correlation_id": "corr-vi1-1",
        "event_type": "campus.security_incident.detected",
        "subject": {},
        "payload": {
            "facility_code": "BLDG-SEC-A",
            "issue_type": "unauthorized_access",
            "severity": "critical",
            "source_entity_type": "security_incident",
            "source_entity_id": "SEC-1",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "high"
    assert any(item["action"] == "create_facility_incident_workflow" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_facilities_team" for item in processed["dispatch_results"])


def test_operations_maintenance_predicted_due_dispatches_incident_workflow_and_notification() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        902,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-e2-1",
        "tenant_id": 902,
        "correlation_id": "corr-e2-1",
        "event_type": "operations.maintenance.predicted_due",
        "subject": {},
        "payload": {
            "asset_code": "MA-202",
            "facility_code": "BLDG-C-HVAC",
            "asset_type": "hvac",
            "days_since_maintenance": 120,
            "expected_service_interval_days": 90,
            "health_score": 22,
            "source_entity_type": "maintenance_asset",
            "source_entity_id": "MA-202",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "high"
    assert any(item["action"] == "create_facility_incident_workflow" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_facilities_team" for item in processed["dispatch_results"])


def test_operations_utilities_spike_medium_dispatches_incident_workflow_only() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        902,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-e2-2",
        "tenant_id": 902,
        "correlation_id": "corr-e2-2",
        "event_type": "operations.utilities.spike_detected",
        "subject": {},
        "payload": {
            "meter_code": "MTR-502",
            "building_code": "BLDG-C",
            "utility_type": "electricity",
            "usage_value": 126,
            "baseline_value": 100,
            "spike_ratio": 1.26,
            "affected_buildings": 1,
            "source_entity_type": "utility_reading",
            "source_entity_id": "MTR-502",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "operational"
    assert processed["decision"]["priority"] == "medium"
    assert any(item["action"] == "create_facility_incident_workflow" for item in processed["dispatch_results"])
    assert not any(item["action"] == "notify_facilities_team" for item in processed["dispatch_results"])


def test_procurement_vendor_sla_high_dispatches_request_and_notification() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        904,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="procurement_lead",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-e4-1",
        "tenant_id": 904,
        "correlation_id": "corr-e4-1",
        "event_type": "procurement.vendor_sla.degraded",
        "subject": {},
        "payload": {
            "vendor_code": "VEN-RISK-1",
            "sla_breach_rate": 0.28,
            "on_time_delivery_rate": 0.70,
            "source_entity_type": "vendor_sla_profile",
            "source_entity_id": "VEN-RISK-1",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "procurement"
    assert processed["decision"]["priority"] == "high"
    assert any(item["action"] == "initiate_procurement_request" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_procurement_team" for item in processed["dispatch_results"])


def test_procurement_contract_risk_medium_dispatches_request_only() -> None:
    service = BrainCoreService()
    service.update_policy_profile(
        904,
        autonomy_level=4,
        require_approval_for_critical=True,
        default_approval_role="procurement_lead",
        enable_ai_reasoning=False,
        actor="admin@tenant",
    )

    signal = {
        "signal_id": "sig-e4-2",
        "tenant_id": 904,
        "correlation_id": "corr-e4-2",
        "event_type": "procurement.contract_risk.high",
        "subject": {},
        "payload": {
            "contract_code": "CON-RISK-2",
            "vendor_code": "VEN-RISK-2",
            "risk_score": 0.74,
            "sla_target_met": True,
            "source_entity_type": "contract_risk_profile",
            "source_entity_id": "CON-RISK-2",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "procurement"
    assert processed["decision"]["priority"] == "medium"
    assert any(item["action"] == "initiate_procurement_request" for item in processed["dispatch_results"])
    assert not any(item["action"] == "notify_procurement_team" for item in processed["dispatch_results"])


def test_student_life_wellbeing_signal_dispatches_support_case_and_notification() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-d3-1",
        "tenant_id": 903,
        "correlation_id": "corr-d3-1",
        "event_type": "student_life.wellbeing.at_risk",
        "subject": {"student_id": "STU-903"},
        "payload": {
            "student_id": "STU-903",
            "wellbeing_score": 24,
            "concern_type": "burnout",
            "source_entity_type": "wellbeing_checkin",
            "source_entity_id": "STU-903",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "risk"
    assert processed["decision"]["priority"] == "high"
    assert any(item["action"] == "create_student_support_case" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_student_success_team" for item in processed["dispatch_results"])


def test_student_life_disciplinary_medium_dispatches_review_case_only() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-d3-2",
        "tenant_id": 903,
        "correlation_id": "corr-d3-2",
        "event_type": "student_life.disciplinary.incident_reported",
        "subject": {"student_id": "STU-904"},
        "payload": {
            "student_id": "STU-904",
            "incident_type": "policy_violation",
            "incident_severity": "medium",
            "incident_count_30d": 1,
            "source_entity_type": "disciplinary_incident",
            "source_entity_id": "STU-904",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "risk"
    assert processed["decision"]["priority"] == "medium"
    assert any(item["action"] == "create_disciplinary_review_case" for item in processed["dispatch_results"])
    assert not any(item["action"] == "notify_student_success_team" for item in processed["dispatch_results"])


def test_financial_aid_warning_rejected_requires_approval_and_support_actions() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-h-1",
        "tenant_id": 905,
        "correlation_id": "corr-h-1",
        "event_type": "financial_aid.warning.detected",
        "subject": {"student_id": "STU-H-1"},
        "payload": {
            "student_id": "STU-H-1",
            "record_id": "FA-1",
            "from_status": "pending",
            "to_status": "rejected",
            "source_entity_type": "financial_aid_record",
            "source_entity_id": "FA-1",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "risk"
    assert processed["decision"]["priority"] == "critical"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["dispatch_results"] == []

    approved = service.approve_decision(processed["decision"]["decision_id"], actor="student_success@tenant")
    assert approved["status"] == "approved"
    assert approved["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_student_support_case" for item in approved["dispatch_results"])
    assert any(item["action"] == "notify_student_success_team" for item in approved["dispatch_results"])
    assert any(item["action"] == "notify_advisor" for item in approved["dispatch_results"])


def test_housing_status_in_review_dispatches_support_actions_without_approval() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-h-2",
        "tenant_id": 905,
        "correlation_id": "corr-h-2",
        "event_type": "housing.status.risk_detected",
        "subject": {"student_id": "STU-H-2"},
        "payload": {
            "student_id": "STU-H-2",
            "request_id": "HR-2",
            "from_status": "submitted",
            "to_status": "in_review",
            "source_entity_type": "housing_request",
            "source_entity_id": "HR-2",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["decision_type"] == "preventive"
    assert processed["decision"]["priority"] == "medium"
    assert processed["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_student_support_case" for item in processed["dispatch_results"])
    assert any(item["action"] == "notify_student_success_team" for item in processed["dispatch_results"])
