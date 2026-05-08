"""A-018.1 — Scheduling Brain maturity closure.

This suite closes the remaining Level 6 evidence gaps without introducing a new
optimizer or broadening scheduling architecture.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.context_sources.scheduling import fetch_scheduling_context
from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry
from app.modules.brain_core.service import BrainCoreService
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.kpi import service as kpi_service


def _make_service() -> BrainCoreService:
    svc = BrainCoreService.__new__(BrainCoreService)
    svc._observability = MagicMock()
    svc._signals = []
    svc._decisions = []
    svc._explanations = {}
    svc._context_builder = MagicMock()
    svc._classifier = MagicMock()
    svc._knowledge = MagicMock()
    svc._policy_resolver = MagicMock()
    svc._reasoning = MagicMock()
    svc._planner = MagicMock()
    svc._policy_guard = MagicMock()
    svc._dispatcher = MagicMock()
    svc._explanation = MagicMock()
    svc._outcome_tracker = MagicMock()
    svc._quality_tracker = MagicMock()
    svc._policy_tuning = MagicMock()
    return svc


def test_fetch_scheduling_context_includes_room_readiness_evidence() -> None:
    ctx = fetch_scheduling_context(
        tenant_id=7,
        subject={"section_id": 101, "room_id": "ROOM-A"},
        payload={
            "tenant_id": 999,
            "enrolled_count": 48,
            "required_capacity": 55,
            "room_capacity": 40,
            "max_capacity": 60,
        },
    )

    assert ctx["tenant_id"] == 7
    assert ctx["required_capacity"] == 55
    assert ctx["room_capacity"] == 40
    assert ctx["room_allocation_required"] is True
    assert ctx["fill_rate"] == 0.8


def test_fetch_scheduling_context_marks_room_allocation_required_without_room() -> None:
    ctx = fetch_scheduling_context(
        tenant_id=12,
        subject={"section_id": 202},
        payload={"required_capacity": 35, "enrolled_count": 35, "max_capacity": 40},
    )

    assert ctx["room_id"] is None
    assert ctx["room_allocation_required"] is True


def test_signal_registry_supports_room_readiness_signals() -> None:
    assert SignalRegistry.signals["scheduling.room_conflict.detected"]["scenario"] == "section_conflict"
    assert SignalRegistry.signals["scheduling.room_allocation.required"]["scenario"] == "section_conflict"
    assert SignalRegistry.signals["scheduling.capacity_mismatch.detected"]["scenario"] == "enrollment_capacity_risk"


def test_decision_registry_reuses_existing_scheduling_scenarios() -> None:
    assert "scheduling.room_conflict.detected" in DecisionRegistry.decisions["section_conflict"]["allowed_event_types"]
    assert "scheduling.room_allocation.required" in DecisionRegistry.decisions["section_conflict"]["allowed_event_types"]
    assert "scheduling.capacity_mismatch.detected" in DecisionRegistry.decisions["enrollment_capacity_risk"]["allowed_event_types"]


def test_risk_classifier_treats_room_conflict_as_high_section_conflict() -> None:
    classifier = RiskClassifier()
    result = classifier.classify(
        {
            "event_type": "scheduling.room_conflict.detected",
            "payload": {"conflict_type": "room_conflict"},
        },
        {},
    )

    assert result["reasoning_path"] == "section_conflict_high"
    assert result["severity"] == "high"


def test_risk_classifier_treats_room_capacity_mismatch_as_high_capacity_risk() -> None:
    classifier = RiskClassifier()
    result = classifier.classify(
        {
            "event_type": "scheduling.capacity_mismatch.detected",
            "payload": {"required_capacity": 55, "room_capacity": 40},
        },
        {},
    )

    assert result["reasoning_path"] == "enrollment_capacity_risk_high"
    assert result["severity"] == "high"


def test_room_allocation_required_defaults_to_non_destructive_medium_path() -> None:
    classifier = RiskClassifier()
    result = classifier.classify(
        {
            "event_type": "scheduling.room_allocation.required",
            "payload": {"required_capacity": 30, "room_id": None},
        },
        {},
    )

    assert result["reasoning_path"] == "section_conflict_medium"
    assert result["severity"] == "medium"


def test_room_readiness_events_are_valid_for_event_ingestion_and_registry() -> None:
    events = {
        "scheduling.room_conflict.detected",
        "scheduling.room_allocation.required",
        "scheduling.capacity_mismatch.detected",
    }

    for event_type in events:
        assert event_type in VALID_EVENT_TYPES
        assert event_type in EXACT_EVENT_REGISTRY


def test_scheduling_kpi_lineage_covers_room_readiness_contracts() -> None:
    assert kpi_service.METRIC_TITLES["room_conflict_count"] == "Room Conflict Count"
    assert "scheduling.room_conflict.detected" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["scheduling_conflicts_count"]
    assert "scheduling.room_allocation.required" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["scheduling_conflicts_count"]
    assert "scheduling.capacity_mismatch.detected" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["capacity_risk_sections_count"]
    assert set(kpi_service.EVENT_DERIVED_METRIC_LINEAGE["room_conflict_count"]) == {
        "scheduling.room_conflict.detected",
        "scheduling.room_allocation.required",
    }


def test_process_signal_room_allocation_required_preserves_tenant_and_avoids_auto_reassignment() -> None:
    svc = _make_service()

    svc._context_builder.build_context.return_value = {
        "tenant_id": 15,
        "event_type": "scheduling.room_allocation.required",
        "scheduling": {
            "section_id": 200,
            "tenant_id": 15,
            "required_capacity": 55,
            "room_capacity": 40,
            "room_allocation_required": True,
        },
        "academic": {},
        "faculty": {},
        "student_success": {},
        "finance": {},
        "operations": {},
        "platform": {},
    }
    svc._classifier.classify.return_value = {
        "situation_type": "operational_risk",
        "severity": "high",
        "urgency": "high",
        "reasoning_path": "section_conflict_high",
    }
    svc._knowledge.retrieve.return_value = {"items": []}
    svc._reasoning.decide.return_value = {
        "decision_type": "operational",
        "priority": "high",
        "recommended_actions": ["create_section_conflict_task", "notify_scheduling_office"],
        "requires_approval": False,
        "confidence_score": 0.91,
        "severity_score": 0.9,
        "urgency_score": 0.9,
        "ai_reasoning_enabled": False,
        "ai_reasoning_trace": [],
        "knowledge_guidance": [],
    }
    svc._planner.build_plan.return_value = [
        {
            "action_name": "create_section_conflict_task",
            "action_type": "workflow_task",
            "payload": {"section_id": 200, "required_capacity": 55},
        }
    ]
    svc._policy_guard.validate.return_value = MagicMock(
        approved=True,
        reason="scheduling_room_allocation_review_required",
        requires_approval=False,
        approval_role="scheduling_office",
    )
    svc._dispatcher.dispatch.return_value = [
        {"status": "dispatched", "action_name": "create_section_conflict_task"}
    ]
    svc._outcome_tracker.record_dispatch_outcome = MagicMock()
    svc._quality_tracker.record = MagicMock()
    svc._policy_tuning.tune = MagicMock(return_value={})

    result = svc.process_signal(
        {
            "tenant_id": 15,
            "event_type": "scheduling.room_allocation.required",
            "source_entity_type": "course_section",
            "source_entity_id": "200",
            "subject": {"section_id": 200},
            "payload": {"tenant_id": 999, "required_capacity": 55, "room_capacity": 40},
        }
    )

    assert result["status"] == "processed"
    dispatch_call = svc._dispatcher.dispatch.call_args
    assert dispatch_call.kwargs["tenant_id"] == 15
    assert dispatch_call.kwargs["actions"] == svc._planner.build_plan.return_value
    actions = svc._reasoning.decide.return_value["recommended_actions"]
    assert "create_section_conflict_task" in actions
    assert all("reassign" not in action for action in actions)
    assert all("reschedule" not in action for action in actions)