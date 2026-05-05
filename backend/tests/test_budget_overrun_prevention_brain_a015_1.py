from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import pytest

from app.modules.brain_core.registry import SignalRegistry
from app.modules.brain_core.service import BrainCoreService


@pytest.fixture(autouse=True)
def _stub_context_sources() -> None:
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
                return_value={"active_interventions": 0, "open_advising_tasks": 0},
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


def _budget_signal(*, tenant_id: int, source_entity_id: str = "CC-101", risk_level: str = "high") -> dict:
    return {
        "signal_id": f"sig-budget-{tenant_id}-{source_entity_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-budget-{tenant_id}-{source_entity_id}",
        "event_type": "finance.expense.budget_exceeded",
        "payload": {
            "cost_center_id": source_entity_id,
            "department_id": "D-01",
            "project_id": "P-01",
            "amount": 7000.0,
            "current_total": 47000.0,
            "budget_limit": 50000.0,
            "attempted_total": 54000.0,
            "risk_level": risk_level,
            "reason": "procurement_request_exceeds_available_budget",
            "source_entity_type": "expense_record",
            "source_entity_id": source_entity_id,
        },
        "metadata": {},
    }


def test_budget_overrun_signal_supported_and_mapped() -> None:
    assert SignalRegistry.is_supported("finance.expense.budget_exceeded")
    assert SignalRegistry.is_supported("campus.budget.overrun_risk_detected")
    assert SignalRegistry.is_supported("campus.expense_controls.budget_exceeded_risk_detected")
    assert SignalRegistry.signals["finance.expense.budget_exceeded"]["scenario"] == "budget_overrun_prevention"


def test_budget_overrun_signal_creates_finance_action() -> None:
    service = BrainCoreService()

    result = service.process_signal(_budget_signal(tenant_id=101))

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "risk"
    assert result["decision"]["priority"] == "high"
    assert any(item["name"] == "create_intervention_case" for item in result["action_plan"])
    assert any(item["action"] == "create_intervention_case" for item in result["dispatch_results"])


def test_duplicate_budget_overrun_signal_is_deduplicated() -> None:
    service = BrainCoreService()

    first = service.process_signal(_budget_signal(tenant_id=102, source_entity_id="CC-DEDUP"))
    second = service.process_signal(_budget_signal(tenant_id=102, source_entity_id="CC-DEDUP"))

    assert first["status"] == "processed"
    assert second["status"] == "deduplicated"
    assert second["reason"] == "duplicate_signal_within_window"


def test_budget_risk_origin_and_evidence_propagated_to_action_payload() -> None:
    service = BrainCoreService()

    result = service.process_signal(_budget_signal(tenant_id=103, source_entity_id="CC-EVID"))

    assert result["status"] == "processed"
    payload = next(item["payload"] for item in result["action_plan"] if item["name"] == "create_intervention_case")
    assert payload["budget_risk_origin"] == "finance.expense.budget_exceeded"
    assert payload["budget_risk_evidence"]["budget_limit"] == 50000.0
    assert payload["budget_risk_evidence"]["attempted_total"] == 54000.0
    assert payload["overrun_amount"] == pytest.approx(4000.0)
    assert payload["overrun_percent"] == pytest.approx(0.08)


def test_missing_tenant_fails_closed() -> None:
    service = BrainCoreService()

    signal = _budget_signal(tenant_id=0)
    signal["tenant_id"] = None

    result = service.process_signal(signal)

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_tenant_context"


def test_missing_amount_and_threshold_fails_closed() -> None:
    service = BrainCoreService()

    signal = _budget_signal(tenant_id=104)
    signal["payload"].pop("amount", None)
    signal["payload"].pop("current_total", None)
    signal["payload"].pop("attempted_total", None)
    signal["payload"].pop("budget_limit", None)

    result = service.process_signal(signal)

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_budget_amount_or_threshold"


def test_cross_tenant_isolation_for_budget_overrun() -> None:
    service = BrainCoreService()

    first = service.process_signal(_budget_signal(tenant_id=201, source_entity_id="CC-X"))
    second = service.process_signal(_budget_signal(tenant_id=202, source_entity_id="CC-X"))

    assert first["status"] == "processed"
    assert second["status"] == "processed"
    assert len(service.list_decisions(tenant_id=201)) == 1
    assert len(service.list_decisions(tenant_id=202)) == 1
    assert service.list_decisions(tenant_id=201)[0]["decision_id"] != service.list_decisions(tenant_id=202)[0]["decision_id"]


def test_non_risk_budget_event_does_not_create_action() -> None:
    service = BrainCoreService()

    signal = {
        "signal_id": "sig-budget-low-1",
        "tenant_id": 301,
        "correlation_id": "corr-budget-low-1",
        "event_type": "campus.budget.overrun_risk_detected",
        "payload": {
            "budget_id": "BUD-LOW-301",
            "amount": 100.0,
            "budget_limit": 10000.0,
            "overrun_percent": 0.01,
            "risk_level": "low",
            "source_entity_type": "budget_plan",
            "source_entity_id": "BUD-LOW-301",
        },
        "metadata": {},
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "low"
    assert result["action_plan"] == []
    assert result["dispatch_results"] == []
