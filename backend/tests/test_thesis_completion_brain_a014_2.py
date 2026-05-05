"""A-014.2: Thesis Completion Brain.

Tests that thesis risk signals route through Brain Core into idempotent
intervention/advisor-support behavior without weakening tenant isolation.

Pattern:
    thesis.status_changed -> brain_core thesis_delay scenario -> decision ->
    create_intervention_case / notify_advisor
"""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from app.modules.brain_core.service import BrainCoreService


@pytest.fixture(autouse=True)
def _stub_brain_core_context_sources() -> None:
    """Keep thesis tests independent from optional DB-backed context tables."""
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


def _thesis_signal(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-TH-1",
    thesis_id: str = "THESIS-1",
    advisor_id: str = "ADV-TH-1",
    to_status: str = "under_review",
    from_status: str = "submitted",
    days_since_last_milestone: int = 75,
    source_entity_id: str | None = None,
) -> dict:
    entity_id = source_entity_id or thesis_id
    return {
        "signal_id": f"thesis-risk-{tenant_id}-{student_id}-{entity_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-thesis-{tenant_id}-{student_id}",
        "event_type": "thesis.status_changed",
        "source_entity_type": "thesis",
        "source_entity_id": entity_id,
        "subject": {
            "student_id": student_id,
            "faculty_id": advisor_id,
        },
        "payload": {
            "student_id": student_id,
            "thesis_id": thesis_id,
            "advisor_id": advisor_id,
            "faculty_id": advisor_id,
            "to_status": to_status,
            "from_status": from_status,
            "days_since_last_milestone": days_since_last_milestone,
            "source_entity_type": "thesis",
            "source_entity_id": entity_id,
        },
        "metadata": {},
    }


class TestThesisRiskRoutingToBrainCore:
    def test_rejected_thesis_routes_to_intervention_decision(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(to_status="rejected", from_status="under_review", days_since_last_milestone=20)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        decision = result["decision"]
        assert decision["decision_type"] == "intervention"
        assert decision["status"] == "dispatched"
        assert "create_intervention_case" in [item["action"] for item in result["dispatch_results"]]
        assert "notify_advisor" in [item["action"] for item in result["dispatch_results"]]

    def test_stalled_thesis_routes_to_intervention_decision(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(to_status="under_review", days_since_last_milestone=90)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        assert result["decision"]["decision_type"] == "intervention"
        assert "create_intervention_case" in [item["action"] for item in result["dispatch_results"]]

    def test_non_risk_thesis_status_does_not_create_intervention(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(to_status="submitted", from_status="draft", days_since_last_milestone=5)

        result = service.process_signal(signal)

        actions = [item["action"] for item in result.get("dispatch_results", [])]
        assert "create_intervention_case" not in actions, actions


class TestThesisRiskIdempotency:
    def test_duplicate_thesis_signal_does_not_fail(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(student_id="STU-IDEM-TH-1", thesis_id="TH-IDEM-1", to_status="rejected")

        first = service.process_signal(signal)
        second = service.process_signal(signal)

        assert first["status"] == "processed"
        assert second["status"] in {"processed", "deduplicated"}
        if second["status"] == "deduplicated":
            assert "original_signal_id" in second

    def test_action_bridge_ensures_existing_thesis_risk_case(self) -> None:
        from app.modules.brain_core.action_bridge import _make_create_intervention_case_handler
        from app.modules.interventions.models import InterventionCaseModel, InterventionCaseStatus

        existing_case = MagicMock(spec=InterventionCaseModel)
        existing_case.id = "THESIS-CASE-EXISTING"
        existing_case.status = InterventionCaseStatus.OPEN

        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing_case

        handler = _make_create_intervention_case_handler(lambda: mock_session)
        result = handler(
            tenant_id=1,
            decision_id="decision-thesis-1",
            payload={
                "student_id": "STU-IDEM-TH-2",
                "thesis_id": "TH-IDEM-2",
                "event_type": "thesis.status_changed",
                "to_status": "rejected",
                "risk_level": "high",
            },
        )

        assert result["status"] == "ensured"
        assert result.get("idempotent_replay") is True
        assert result["item"]["case_id"] == "THESIS-CASE-EXISTING"
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestThesisRiskOriginEvidence:
    def test_thesis_risk_action_plan_preserves_origin_evidence(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(
            student_id="STU-EVID-TH-1",
            thesis_id="TH-EVID-1",
            to_status="rejected",
            from_status="under_review",
            days_since_last_milestone=30,
        )

        result = service.process_signal(signal)

        intervention_action = next(
            item for item in result["decision"]["action_plan"] if item.get("name") == "create_intervention_case"
        )
        payload = intervention_action["payload"]
        assert payload["event_type"] == "thesis.status_changed"
        assert payload["thesis_id"] == "TH-EVID-1"
        assert payload["to_status"] == "rejected"
        assert payload["source_entity_id"] == "TH-EVID-1"


class TestThesisRiskFailClosed:
    def test_missing_thesis_id_does_not_create_intervention(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(thesis_id="", to_status="rejected")
        signal["payload"].pop("thesis_id", None)

        result = service.process_signal(signal)

        actions = [item["action"] for item in result.get("dispatch_results", [])]
        assert "create_intervention_case" not in actions, actions

    def test_missing_student_id_does_not_create_intervention(self) -> None:
        service = BrainCoreService()
        signal = _thesis_signal(student_id="", to_status="rejected")
        signal["payload"].pop("student_id", None)
        signal["subject"].pop("student_id", None)

        result = service.process_signal(signal)

        actions = [item["action"] for item in result.get("dispatch_results", [])]
        assert "create_intervention_case" not in actions, actions


class TestThesisRiskTenantIsolation:
    def test_thesis_risk_cross_tenant_decisions_are_isolated(self) -> None:
        service = BrainCoreService()

        signal_a = _thesis_signal(tenant_id=100, student_id="STU-TA", thesis_id="TH-TA", to_status="rejected")
        signal_b = _thesis_signal(tenant_id=200, student_id="STU-TB", thesis_id="TH-TB", to_status="rejected")

        result_a = service.process_signal(signal_a)
        result_b = service.process_signal(signal_b)

        assert result_a["status"] == "processed"
        assert result_b["status"] == "processed"
        assert result_a["decision"]["tenant_id"] == 100
        assert result_b["decision"]["tenant_id"] == 200
