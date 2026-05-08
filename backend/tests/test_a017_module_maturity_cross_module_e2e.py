"""A-017.7 — Cross-module maturity E2E/contract validation.

This suite is intentionally thin and reuse-first: it validates shared cross-module
contracts for already-completed A-017 modules without introducing new features.
"""

from __future__ import annotations

from contextlib import ExitStack
from uuid import uuid4

import pytest

from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry
from app.modules.brain_core.service import BrainCoreService
from app.platform.event_ingestion.types import BILLING_USAGE_RECORDED, VALID_EVENT_TYPES
from app.platform.kpi.service import (
    EVENT_DERIVED_METRIC_LINEAGE,
    METRIC_TITLES,
    _compute_budget_kpi_values,
)


@pytest.fixture(autouse=True)
def _stub_context_sources() -> None:
    """Keep BrainCoreService deterministic for contract assertions."""
    from unittest.mock import patch

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
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_scheduling_context",
                return_value={"scheduling_health_snapshot": {}},
            )
        )
        yield


def _exam_governance_signal(*, tenant_id: int, risk_level: str = "high") -> dict[str, object]:
    return {
        "signal_id": f"a0177-{tenant_id}-{uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-a0177-{tenant_id}",
        "event_type": "exam.violation_detected",
        "source_entity_type": "exam_governance",
        "source_entity_id": "EXAM-A0177",
        "payload": {
            "student_id": "STU-A0177",
            "exam_id": "EXAM-A0177",
            "risk_level": risk_level,
            "source_module": "exam_governance",
        },
        "metadata": {},
    }


def test_a017_7_budget_event_contract_and_kpi_lineage_remain_active() -> None:
    assert "finance.budget_variance.threshold_reached" in VALID_EVENT_TYPES

    budget_lineage = EVENT_DERIVED_METRIC_LINEAGE["budget_overrun_risk_count"]
    assert "finance.budget_variance.threshold_reached" in budget_lineage

    computed = _compute_budget_kpi_values({
        "finance.expense.budget_exceeded": 1,
        "finance.budget_variance.threshold_reached": 2,
    })
    assert computed["budget_overrun_risk_count"] >= 3
    assert computed["budget_review_actions_count"] >= 2


def test_a017_7_exam_governance_brain_path_remains_exam_integrity_and_non_punitive() -> None:
    service = BrainCoreService()
    result = service.process_signal(_exam_governance_signal(tenant_id=17, risk_level="high"))

    assert result["status"] == "processed"
    decision = result["decision"]
    assert decision["decision_type"] == "exam_integrity_review"
    assert decision["requires_approval"] is True

    actions = [str(item).lower() for item in decision.get("recommended_actions", [])]
    forbidden_tokens = ("grade", "fail", "suspend", "expel", "sanction", "penalt")
    assert all(not any(token in action for token in forbidden_tokens) for action in actions)


def test_a017_7_research_ethics_and_billing_contract_event_types_remain_accepted() -> None:
    assert "research_ethics.application.submitted" in VALID_EVENT_TYPES
    assert "research_ethics.high_risk.detected" in VALID_EVENT_TYPES
    assert BILLING_USAGE_RECORDED in VALID_EVENT_TYPES

    assert "research_ethics.application.submitted" in EVENT_DERIVED_METRIC_LINEAGE[
        "research_ethics_review_cases_count"
    ]
    assert "research_ethics.high_risk.detected" in EVENT_DERIVED_METRIC_LINEAGE[
        "research_ethics_requires_approval_count"
    ]


def test_a017_7_billing_kpi_contract_surface_remains_available() -> None:
    assert "total_active_subscriptions" in METRIC_TITLES
    assert "delinquency_cases_active" in METRIC_TITLES
    assert "overdue_amount_at_risk" in METRIC_TITLES
    assert "delinquency_recovery_rate" in METRIC_TITLES
    assert "billing_usage_recorded_from_events_total" in EVENT_DERIVED_METRIC_LINEAGE


def test_a017_7_no_duplicate_budget_or_exam_brain_scenarios_introduced() -> None:
    assert SignalRegistry.signals["budget_plan.approved"]["scenario"] == "budget_overrun_prevention"
    assert SignalRegistry.signals["budget_plan.rejected"]["scenario"] == "budget_overrun_prevention"
    assert SignalRegistry.signals["exam.violation_detected"]["scenario"] == "exam_proctoring_violation"

    budget_scenarios = [
        cfg["scenario"] for key, cfg in SignalRegistry.signals.items() if key.startswith("budget_plan.")
    ]
    assert set(budget_scenarios) == {"budget_overrun_prevention"}

    assert list(DecisionRegistry.decisions.keys()).count("budget_overrun_prevention") == 1
    assert list(DecisionRegistry.decisions.keys()).count("exam_proctoring_violation") == 1


def test_a017_7_tenant_fail_closed_and_isolation_for_exam_governance_path() -> None:
    service = BrainCoreService()

    rejected = service.process_signal(_exam_governance_signal(tenant_id=0))
    assert rejected["status"] == "rejected"
    assert rejected["reason"] == "missing_tenant_context"

    processed_a = service.process_signal(_exam_governance_signal(tenant_id=1701))
    processed_b = service.process_signal(_exam_governance_signal(tenant_id=1702))

    assert processed_a["status"] == "processed"
    assert processed_b["status"] == "processed"
    assert int(processed_a["decision"]["tenant_id"]) == 1701
    assert int(processed_b["decision"]["tenant_id"]) == 1702
