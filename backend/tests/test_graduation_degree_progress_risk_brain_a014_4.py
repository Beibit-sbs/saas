from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import pytest

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


def test_degree_progress_event_registered_for_brain() -> None:
    from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry

    assert SignalRegistry.is_supported("degree_progress.graduation_risk.detected")
    sig = SignalRegistry.signals["degree_progress.graduation_risk.detected"]
    assert sig["scenario"] == "graduation_degree_progress_risk"

    decision = DecisionRegistry.decisions["graduation_degree_progress_risk"]
    assert "create_intervention_case" in decision["action_map"]
    assert "notify_advisor" in decision["action_map"]


def test_graduation_risk_high_creates_intervention_and_keeps_origin_evidence() -> None:
    service = BrainCoreService()

    signal = {
        "event_type": "degree_progress.graduation_risk.detected",
        "tenant_id": 71,
        "payload": {
            "student_profile_id": "STU-71",
            "program_id": 301,
            "remaining_required_items": 4,
            "credits_earned": 78,
            "minimum_credits": 120,
            "source_module": "degree_progress",
        },
    }

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "intervention"
    assert result["decision"]["priority"] == "critical"
    assert "create_intervention_case" in result["decision"]["recommended_actions"]

    assert any(item["name"] == "create_intervention_case" for item in result["action_plan"])
    intervention_action = next(
        item for item in result["action_plan"] if item["name"] == "create_intervention_case"
    )
    assert intervention_action["payload"]["student_id"] == "STU-71"
    assert intervention_action["payload"]["source_entity_id"] == "STU-71"
    assert intervention_action["payload"]["event_type"] == "degree_progress.graduation_risk.detected"

    assert any(item["action"] == "create_intervention_case" for item in result["dispatch_results"])


def test_graduation_risk_duplicate_signal_is_idempotently_deduplicated() -> None:
    service = BrainCoreService()
    signal = {
        "event_type": "degree_progress.graduation_risk.detected",
        "tenant_id": 88,
        "source_entity_type": "student_graduation_progress",
        "source_entity_id": "STU-88",
        "payload": {
            "student_profile_id": "STU-88",
            "remaining_required_items": 3,
            "credits_earned": 90,
            "minimum_credits": 120,
        },
    }

    first = service.process_signal(dict(signal))
    second = service.process_signal(dict(signal))

    assert first["status"] == "processed"
    assert second["status"] == "deduplicated"
    assert second["reason"] == "duplicate_signal_within_window"


def test_graduation_risk_missing_student_is_fail_closed() -> None:
    service = BrainCoreService()

    result = service.process_signal(
        {
            "event_type": "degree_progress.graduation_risk.detected",
            "tenant_id": 9,
            "payload": {
                "program_id": 22,
                "remaining_required_items": 5,
                "credits_earned": 60,
                "minimum_credits": 120,
            },
        }
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_student_context"


def test_graduation_risk_is_tenant_isolated_for_dedup() -> None:
    service = BrainCoreService()

    baseline = {
        "event_type": "degree_progress.graduation_risk.detected",
        "source_entity_type": "student_graduation_progress",
        "source_entity_id": "STU-100",
        "payload": {
            "student_profile_id": "STU-100",
            "remaining_required_items": 3,
            "credits_earned": 95,
            "minimum_credits": 120,
        },
    }

    tenant_a = service.process_signal({**baseline, "tenant_id": 1001})
    tenant_b = service.process_signal({**baseline, "tenant_id": 2002})

    assert tenant_a["status"] == "processed"
    assert tenant_b["status"] == "processed"


def test_graduation_low_risk_produces_no_actions() -> None:
    service = BrainCoreService()

    result = service.process_signal(
        {
            "event_type": "degree_progress.graduation_risk.detected",
            "tenant_id": 55,
            "payload": {
                "student_profile_id": "STU-55",
                "remaining_required_items": 0,
                "credits_earned": 120,
                "minimum_credits": 120,
            },
        }
    )

    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "low"
    assert result["decision"]["recommended_actions"] == []
    assert result["action_plan"] == []
    assert result["dispatch_results"] == []


def test_transcripts_with_graduation_context_routes_to_supported_risk_actions() -> None:
    service = BrainCoreService()

    result = service.process_signal(
        {
            "event_type": "transcripts.inconsistency.detected",
            "tenant_id": 311,
            "source_entity_type": "transcript_record",
            "source_entity_id": "TR-311",
            "payload": {
                "student_id": "STU-311",
                "issue_count": 4,
                "graduation_risk_detected": True,
                "source_module": "transcripts",
            },
        }
    )

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "intervention"
    assert "create_intervention_case" in result["decision"]["recommended_actions"]
    assert any(item["name"] == "create_intervention_case" for item in result["action_plan"])
