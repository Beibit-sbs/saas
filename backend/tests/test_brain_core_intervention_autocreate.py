"""Tests for Brain decision -> intervention auto-create wiring (Audit next item).

DoD: decision_type="intervention" must include create_intervention_case action and
trigger dispatcher execution in process_signal when auto-approval is enabled.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.brain_core.service import BrainCoreService


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
    svc._policy_tuner = MagicMock()
    return svc


def test_ensure_intervention_action_noop_for_non_intervention() -> None:
    svc = _make_service()
    original = [{"name": "notify_student_success_team", "action_type": "notification"}]

    result = svc._ensure_intervention_action_for_intervention_decisions(
        decision_type="risk",
        action_plan=list(original),
        signal={"event_type": "academic.attendance_risk.detected"},
        requires_approval=False,
    )

    assert result == original


def test_ensure_intervention_action_appends_when_missing() -> None:
    svc = _make_service()

    result = svc._ensure_intervention_action_for_intervention_decisions(
        decision_type="intervention",
        action_plan=[],
        signal={
            "event_type": "academic.attendance_risk.detected",
            "student_id": "S-100",
            "source_entity_type": "student",
            "source_entity_id": "S-100",
            "payload": {"risk_level": "high"},
        },
        requires_approval=False,
    )

    assert len(result) == 1
    action = result[0]
    assert action["name"] == "create_intervention_case"
    assert action["action_type"] == "workflow_task"
    assert action["requires_approval"] is False
    assert action["payload"]["student_id"] == "S-100"
    assert action["payload"]["risk_level"] == "high"


def test_ensure_intervention_action_does_not_duplicate_existing_action() -> None:
    svc = _make_service()
    original = [
        {
            "name": "create_intervention_case",
            "action_type": "workflow_task",
            "requires_approval": False,
            "payload": {"student_id": "S-1"},
        }
    ]

    result = svc._ensure_intervention_action_for_intervention_decisions(
        decision_type="intervention",
        action_plan=list(original),
        signal={"event_type": "academic.attendance_risk.detected"},
        requires_approval=False,
    )

    assert result == original


def test_process_signal_intervention_decision_dispatches_create_intervention_case() -> None:
    from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile

    svc = _make_service()
    svc._context_builder.build_context.return_value = {}
    svc._classifier.classify.return_value = {
        "situation_type": "academic_risk",
        "severity": "high",
        "urgency": "high",
        "reasoning_path": "test_path",
    }
    svc._knowledge.retrieve.return_value = {}
    svc._policy_resolver.get_profile.return_value = TenantPolicyProfile(
        tenant_id=3,
        autonomy_level=3,
        require_approval_for_critical=False,
        default_approval_role="dean_office",
        enable_ai_reasoning=False,
    )
    svc._reasoning.decide.return_value = {
        "decision_type": "intervention",
        "priority": "high",
        "recommended_actions": [],
        "requires_approval": False,
        "confidence_score": 0.9,
        "severity_score": 0.8,
        "urgency_score": 0.8,
        "ai_reasoning_enabled": False,
        "ai_reasoning_trace": [],
    }
    # Planner returns no actions; service must inject create_intervention_case.
    svc._planner.build_plan.return_value = []
    svc._policy_guard.validate.return_value = MagicMock(
        approved=True,
        requires_approval=False,
        reason="auto",
        approval_role=None,
    )
    svc._dispatcher.dispatch.return_value = [
        {"action": "create_intervention_case", "status": "created", "item": {"id": 101}}
    ]
    svc._explanation.build.return_value = {"summary": "intervention created"}

    signal = {
        "event_type": "academic.attendance_risk.detected",
        "tenant_id": 3,
        "source_entity_type": "student",
        "source_entity_id": "S-200",
        "student_id": "S-200",
        "payload": {"risk_level": "high"},
    }

    with (
        patch.object(svc, "_check_duplicate_signal", return_value=None),
        patch.object(svc, "_try_persist_signal_to_db"),
        patch.object(svc, "_try_persist_decision_to_db"),
        patch.object(svc, "_emit_decision_notification"),
    ):
        result = svc.process_signal(dict(signal))

    assert result["status"] == "processed"
    dispatched_actions = svc._dispatcher.dispatch.call_args.kwargs["actions"]
    assert any(item["name"] == "create_intervention_case" for item in dispatched_actions)
    assert result["decision"]["decision_type"] == "intervention"
    assert result["dispatch_results"][0]["action"] == "create_intervention_case"
