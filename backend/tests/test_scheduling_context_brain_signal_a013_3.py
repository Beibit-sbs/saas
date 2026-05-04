"""A-013.3 — Scheduling context source + prerequisite/conflict Brain Core signal.

Targeted test suite (red → green):
1. Scheduling context source returns tenant-scoped payload-derived context.
2. ContextBuilder.build_context() includes a "scheduling" key.
3. scheduling.section.conflict_detected signal maps to section_conflict scenario.
4. enrollment.capacity_risk.detected signal maps to enrollment_capacity_risk scenario.
5. Missing tenant_id fails closed (ValueError).
6. Full process_signal() for conflict event dispatches expected action.
7. Cross-tenant payload cannot override the signal's tenant_id in dispatch.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.brain_core.context_sources.scheduling import fetch_scheduling_context
from app.modules.brain_core.context_builder import ContextBuilder
from app.modules.brain_core.registry import SignalRegistry
from app.modules.brain_core.service import BrainCoreService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 1. Scheduling context source returns tenant-scoped payload-derived context
# ---------------------------------------------------------------------------

def test_fetch_scheduling_context_returns_tenant_scoped_context() -> None:
    ctx = fetch_scheduling_context(
        tenant_id=42,
        subject={"section_id": 100, "course_id": 7},
        payload={
            "enrolled_count": 48,
            "max_capacity": 50,
            "room_id": "ROOM-A1",
            "faculty_id": "FAC-001",
            "term_id": 3,
            "conflict_type": "room_conflict",
        },
    )
    assert ctx["tenant_id"] == 42
    assert ctx["section_id"] == 100
    assert ctx["course_id"] == 7
    assert ctx["enrolled_count"] == 48
    assert ctx["max_capacity"] == 50
    assert ctx["room_id"] == "ROOM-A1"
    assert ctx["faculty_id"] == "FAC-001"
    assert ctx["conflict_type"] == "room_conflict"
    # fill_rate auto-computed
    assert ctx["fill_rate"] is not None
    assert abs(ctx["fill_rate"] - 0.96) < 0.01


def test_fetch_scheduling_context_uses_explicit_fill_rate_when_provided() -> None:
    ctx = fetch_scheduling_context(
        tenant_id=10,
        subject={},
        payload={
            "enrolled_count": 10,
            "max_capacity": 50,
            "fill_rate": 0.20,  # explicit override
        },
    )
    assert ctx["fill_rate"] == 0.20


def test_fetch_scheduling_context_empty_payload_returns_nones() -> None:
    ctx = fetch_scheduling_context(tenant_id=5, subject={}, payload={})
    assert ctx["tenant_id"] == 5
    assert ctx["section_id"] is None
    assert ctx["fill_rate"] is None
    assert ctx["conflict_type"] is None


# ---------------------------------------------------------------------------
# 2. ContextBuilder includes "scheduling" key
# ---------------------------------------------------------------------------

def test_context_builder_includes_scheduling_context() -> None:
    builder = ContextBuilder()

    # Patch all context source fetchers to no-ops except scheduling
    noop = lambda **_kw: {}
    with (
        patch("app.modules.brain_core.context_builder.fetch_academic_context", noop),
        patch("app.modules.brain_core.context_builder.fetch_student_success_context", noop),
        patch("app.modules.brain_core.context_builder.fetch_faculty_context", noop),
        patch("app.modules.brain_core.context_builder.fetch_finance_context", noop),
        patch("app.modules.brain_core.context_builder.fetch_operations_context", noop),
        patch("app.modules.brain_core.context_builder.fetch_platform_context", noop),
        patch("app.modules.brain_core.context_builder.fetch_scheduling_context", return_value={"tenant_id": 9, "_source": "scheduling_mock"}) as mock_sched,
    ):
        result = builder.build_context({
            "tenant_id": 9,
            "event_type": "scheduling.section.conflict_detected",
            "subject": {"section_id": 55},
            "payload": {"conflict_type": "instructor_conflict"},
        })

    assert "scheduling" in result
    assert result["scheduling"]["_source"] == "scheduling_mock"
    mock_sched.assert_called_once_with(
        tenant_id=9,
        subject={"section_id": 55},
        payload={"conflict_type": "instructor_conflict"},
    )


def test_context_builder_raises_for_missing_tenant_id() -> None:
    import pytest
    builder = ContextBuilder()
    with pytest.raises(ValueError, match="tenant_id"):
        builder.build_context({"tenant_id": 0, "event_type": "test", "subject": {}, "payload": {}})


# ---------------------------------------------------------------------------
# 3. Signal registry maps scheduling.section.conflict_detected
# ---------------------------------------------------------------------------

def test_section_conflict_signal_is_registered_in_signal_registry() -> None:
    assert SignalRegistry.is_supported("scheduling.section.conflict_detected"), (
        "scheduling.section.conflict_detected must be in SignalRegistry.signals"
    )
    entry = SignalRegistry.signals["scheduling.section.conflict_detected"]
    assert entry["scenario"] == "section_conflict"
    assert "scheduling" in entry["context_sources"]


# ---------------------------------------------------------------------------
# 4. Signal registry maps enrollment.capacity_risk.detected
# ---------------------------------------------------------------------------

def test_enrollment_capacity_risk_signal_is_registered_in_signal_registry() -> None:
    assert SignalRegistry.is_supported("enrollment.capacity_risk.detected"), (
        "enrollment.capacity_risk.detected must be in SignalRegistry.signals"
    )
    entry = SignalRegistry.signals["enrollment.capacity_risk.detected"]
    assert entry["scenario"] == "enrollment_capacity_risk"
    assert "scheduling" in entry["context_sources"]


# ---------------------------------------------------------------------------
# 5. Full process_signal() for conflict event dispatches expected action
# ---------------------------------------------------------------------------

def test_process_signal_conflict_dispatches_section_conflict_action() -> None:
    svc = _make_service()

    svc._context_builder.build_context.return_value = {
        "tenant_id": 15,
        "event_type": "scheduling.section.conflict_detected",
        "scheduling": {"section_id": 200, "conflict_type": "room_conflict", "tenant_id": 15},
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
        "confidence_score": 0.9,
        "severity_score": 0.9,
        "urgency_score": 0.9,
        "ai_reasoning_enabled": False,
        "ai_reasoning_trace": [],
        "knowledge_guidance": [],
    }
    svc._planner.build_plan.return_value = [
        {"action_name": "create_section_conflict_task", "action_type": "workflow_task", "payload": {"section_id": 200}},
    ]
    svc._policy_guard.validate.return_value = MagicMock(
        approved=True,
        reason="operational_decision_approved",
        requires_approval=False,
        approval_role="dean_office",
    )
    dispatch_result = [{"status": "dispatched", "action_name": "create_section_conflict_task"}]
    svc._dispatcher.dispatch.return_value = dispatch_result
    svc._outcome_tracker.record_dispatch_outcome = MagicMock()
    svc._quality_tracker.record = MagicMock()
    svc._policy_tuner.tune = MagicMock(return_value={})

    signal = {
        "tenant_id": 15,
        "event_type": "scheduling.section.conflict_detected",
        "subject": {"section_id": 200},
        "payload": {"conflict_type": "room_conflict", "section_id": 200},
    }
    result = svc.process_signal(signal)
    assert result.get("status") == "processed"
    assert (result.get("decision") or {}).get("status") == "dispatched"
    svc._dispatcher.dispatch.assert_called_once()
    dispatch_call = svc._dispatcher.dispatch.call_args
    assert dispatch_call.kwargs.get("tenant_id") == 15
    assert dispatch_call.kwargs.get("actions") == svc._planner.build_plan.return_value


# ---------------------------------------------------------------------------
# 6. Cross-tenant payload cannot override dispatch tenant_id
# ---------------------------------------------------------------------------

def test_cross_tenant_scheduling_payload_cannot_override_dispatch_tenant() -> None:
    """Dispatcher must always receive the signal's tenant_id (15), not payload's spoofed tenant (999)."""
    svc = _make_service()

    svc._context_builder.build_context.return_value = {
        "tenant_id": 15,
        "event_type": "scheduling.section.conflict_detected",
        "scheduling": {"section_id": 201, "tenant_id": 15},
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
        "recommended_actions": ["create_section_conflict_task"],
        "requires_approval": False,
        "confidence_score": 0.9,
        "severity_score": 0.9,
        "urgency_score": 0.9,
        "ai_reasoning_enabled": False,
        "ai_reasoning_trace": [],
        "knowledge_guidance": [],
    }
    svc._planner.build_plan.return_value = [
        {"action_name": "create_section_conflict_task", "action_type": "workflow_task", "payload": {}},
    ]
    svc._policy_guard.validate.return_value = MagicMock(
        approved=True, reason="ok", requires_approval=False, approval_role="dean_office"
    )
    svc._dispatcher.dispatch.return_value = [{"status": "dispatched", "action_name": "create_section_conflict_task"}]
    svc._outcome_tracker.record_dispatch_outcome = MagicMock()
    svc._quality_tracker.record = MagicMock()
    svc._policy_tuner.tune = MagicMock(return_value={})

    signal = {
        "tenant_id": 15,
        "event_type": "scheduling.section.conflict_detected",
        "subject": {"section_id": 201},
        "payload": {"conflict_type": "room_conflict", "tenant_id": 999},  # spoofed
    }
    svc.process_signal(signal)

    dispatch_call = svc._dispatcher.dispatch.call_args
    dispatched_tenant = dispatch_call.kwargs.get("tenant_id")
    assert dispatched_tenant == 15, (
        f"Dispatcher must receive signal's tenant_id=15, not spoofed tenant_id=999. Got: {dispatched_tenant}"
    )


# ---------------------------------------------------------------------------
# 7. enrollment.capacity_risk.detected context is tenant-scoped
# ---------------------------------------------------------------------------

def test_enrollment_capacity_risk_context_is_tenant_scoped() -> None:
    ctx = fetch_scheduling_context(
        tenant_id=33,
        subject={"section_id": 99, "course_id": 11},
        payload={
            "enrolled_count": 50,
            "max_capacity": 50,
            "risk_type": "capacity_full",
        },
    )
    assert ctx["tenant_id"] == 33
    assert ctx["section_id"] == 99
    # fill_rate should be 1.0 when at capacity
    assert ctx["fill_rate"] == 1.0
    assert ctx["risk_type"] == "capacity_full"
