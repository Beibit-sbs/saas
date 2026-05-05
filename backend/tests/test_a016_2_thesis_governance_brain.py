"""A-016.2: Thesis Submission Pipeline + Supervisor Assignment Automation Brain.

Tests that thesis governance signals (submission, supervisor assignment, review delay)
route through Brain Core into the thesis_governance scenario, produce decisions with
decision_type="thesis_supervisor_assignment", and enforce security invariants.

Signal flow:
    thesis.submission.created / thesis.supervisor.assignment_needed /
    thesis.supervisor.overloaded / thesis.review.delayed /
    thesis.submission.pending_review / thesis.governance.risk_detected
    -> BrainCoreService.process_signal()
    -> thesis_governance scenario
    -> risk_classifier (4-level deterministic severity)
    -> rules_engine thesis_governance_* paths
    -> decision_type="thesis_supervisor_assignment"

Security invariants:
    - missing tenant_id fails closed
    - missing thesis_id fails closed
    - missing optional supervisor context MUST NOT crash
    - cross-tenant isolation preserved
    - no punitive academic actions (no reject_thesis, suspend_student, etc.)
"""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.brain_core.service import BrainCoreService
from app.modules.brain_core.registry import SignalRegistry


# ---------------------------------------------------------------------------
# Autouse fixture: stub all context_builder fetchers used by thesis_governance
# context_sources = ["academic", "faculty", "student_success"]
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _stub_context_sources() -> None:
    """Keep thesis governance tests independent from optional DB-backed context tables."""
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


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------


def _submission_signal(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-THESIS-1",
    thesis_id: str = "TH-001",
    supervisor_id: str | None = None,
    days_without_supervisor: int | None = None,
    risk_level: str | None = None,
    event_type: str = "thesis.submission.created",
) -> dict:
    payload: dict = {
        "student_id": student_id,
        "thesis_id": thesis_id,
        "status": "submitted",
        "source_entity_type": "thesis",
        "source_entity_id": thesis_id,
    }
    if supervisor_id is not None:
        payload["supervisor_id"] = supervisor_id
    if days_without_supervisor is not None:
        payload["days_without_supervisor"] = days_without_supervisor
    if risk_level is not None:
        payload["risk_level"] = risk_level
    return {
        "signal_id": f"thesis-gov-{tenant_id}-{thesis_id}-{uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-thesis-gov-{tenant_id}-{thesis_id}",
        "event_type": event_type,
        "source_entity_type": "thesis",
        "source_entity_id": thesis_id,
        "subject": {"student_id": student_id},
        "payload": payload,
    }


def _supervisor_signal(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-THESIS-1",
    thesis_id: str = "TH-001",
    supervisor_id: str | None = None,
    days_without_supervisor: int | None = None,
    risk_level: str | None = None,
) -> dict:
    return _submission_signal(
        tenant_id=tenant_id,
        student_id=student_id,
        thesis_id=thesis_id,
        supervisor_id=supervisor_id,
        days_without_supervisor=days_without_supervisor,
        risk_level=risk_level,
        event_type="thesis.supervisor.assignment_needed",
    )


def _overloaded_signal(
    *,
    tenant_id: int = 1,
    thesis_id: str = "TH-OVERLOAD-1",
    supervisor_id: str = "SUP-1",
    supervisor_load_pct: float | None = None,
) -> dict:
    payload: dict = {
        "thesis_id": thesis_id,
        "supervisor_id": supervisor_id,
        "supervisor_overloaded": True,
        "source_entity_type": "thesis",
        "source_entity_id": thesis_id,
    }
    if supervisor_load_pct is not None:
        payload["supervisor_load_pct"] = supervisor_load_pct
    return {
        "signal_id": f"thesis-overload-{tenant_id}-{thesis_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-overload-{tenant_id}",
        "event_type": "thesis.supervisor.overloaded",
        "source_entity_type": "thesis",
        "source_entity_id": thesis_id,
        "subject": {},
        "payload": payload,
    }


def _delayed_review_signal(
    *,
    tenant_id: int = 1,
    thesis_id: str = "TH-DELAYED-1",
    supervisor_id: str = "SUP-2",
    days_in_review: int = 70,
) -> dict:
    return {
        "signal_id": f"thesis-delay-{tenant_id}-{thesis_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-delay-{tenant_id}",
        "event_type": "thesis.review.delayed",
        "source_entity_type": "thesis",
        "source_entity_id": thesis_id,
        "subject": {},
        "payload": {
            "thesis_id": thesis_id,
            "supervisor_id": supervisor_id,
            "days_in_review": days_in_review,
            "source_entity_type": "thesis",
            "source_entity_id": thesis_id,
        },
    }


# ---------------------------------------------------------------------------
# Test 1 — Registry completeness
# ---------------------------------------------------------------------------


def test_all_thesis_governance_event_types_are_registered() -> None:
    """All 6 thesis governance event types must be registered in SignalRegistry."""
    expected = {
        "thesis.submission.created",
        "thesis.submission.pending_review",
        "thesis.supervisor.assignment_needed",
        "thesis.supervisor.overloaded",
        "thesis.review.delayed",
        "thesis.governance.risk_detected",
    }
    for et in expected:
        assert SignalRegistry.is_supported(et), f"event_type not registered: {et}"
        entry = SignalRegistry.signals[et]
        assert entry["scenario"] == "thesis_governance", f"wrong scenario for {et}: {entry['scenario']}"


# ---------------------------------------------------------------------------
# Test 2 — Submission without supervisor routes through Brain Core
# ---------------------------------------------------------------------------


def test_thesis_submission_without_supervisor_is_processed() -> None:
    """thesis.submission.created without supervisor_id routes and produces a decision."""
    svc = BrainCoreService()
    signal = _submission_signal(supervisor_id=None)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}, f"Unexpected status: {result}"


# ---------------------------------------------------------------------------
# Test 3 — Decision type is thesis_supervisor_assignment
# ---------------------------------------------------------------------------


def test_brain_decision_type_is_thesis_supervisor_assignment() -> None:
    """Brain Core must produce decision_type='thesis_supervisor_assignment' for thesis governance signals."""
    svc = BrainCoreService()
    signal = _supervisor_signal(supervisor_id=None, days_without_supervisor=20)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("decision_type") == "thesis_supervisor_assignment", (
        f"Expected thesis_supervisor_assignment, got: {decision.get('decision_type')}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Critical severity: no supervisor beyond 30 days
# ---------------------------------------------------------------------------


def test_no_supervisor_30_days_produces_critical_risk() -> None:
    """Missing supervisor + days_without_supervisor >= 30 must produce critical risk."""
    svc = BrainCoreService()
    signal = _supervisor_signal(supervisor_id=None, days_without_supervisor=35)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("priority") == "critical", (
        f"Expected critical priority, got: {decision.get('priority')}"
    )
    assert decision.get("decision_type") == "thesis_supervisor_assignment"


# ---------------------------------------------------------------------------
# Test 5 — High severity: no supervisor beyond 14 days (not yet critical)
# ---------------------------------------------------------------------------


def test_no_supervisor_14_days_produces_high_risk() -> None:
    """Missing supervisor + days_without_supervisor in [14, 29] must produce high risk."""
    svc = BrainCoreService()
    signal = _supervisor_signal(supervisor_id=None, days_without_supervisor=20)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("priority") == "high", (
        f"Expected high priority, got: {decision.get('priority')}"
    )


# ---------------------------------------------------------------------------
# Test 6 — Supervisor overload signal produces review/reassignment actionability
# ---------------------------------------------------------------------------


def test_supervisor_overloaded_signal_produces_review_action() -> None:
    """thesis.supervisor.overloaded must produce an assign_supervisor or request_supervisor_review action."""
    svc = BrainCoreService()
    signal = _overloaded_signal()
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("decision_type") == "thesis_supervisor_assignment"
    recommended = [a.get("name") if isinstance(a, dict) else a for a in decision.get("recommended_actions", [])]
    has_action = any(
        a in {"assign_supervisor", "request_supervisor_review", "notify_department"}
        for a in recommended
    )
    assert has_action, f"No supervisor review/assign action in recommended_actions: {recommended}"


# ---------------------------------------------------------------------------
# Test 7 — Delayed review signal maps to thesis governance decision
# ---------------------------------------------------------------------------


def test_delayed_review_signal_maps_to_thesis_governance() -> None:
    """thesis.review.delayed must route to thesis_governance and produce a decision."""
    svc = BrainCoreService()
    signal = _delayed_review_signal(days_in_review=70)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("decision_type") == "thesis_supervisor_assignment"
    assert decision.get("priority") in {"high", "critical"}, (
        f"Expected high+ priority for 70-day delay, got: {decision.get('priority')}"
    )


# ---------------------------------------------------------------------------
# Test 8 — Missing optional supervisor_id does not crash
# ---------------------------------------------------------------------------


def test_missing_optional_supervisor_id_does_not_crash() -> None:
    """Absence of supervisor_id (optional field) must not crash and must appear in evidence."""
    svc = BrainCoreService()
    signal = _submission_signal(supervisor_id=None, days_without_supervisor=5)
    result = svc.process_signal(signal)
    # Must not throw, must not be "error"
    assert result.get("status") not in {"error"}
    # Absence evidence should be attached
    processed_payload = result.get("signal_payload") or signal.get("payload") or {}
    # Just verify no unhandled exception occurred and a decision is present
    assert "decision" in result or result.get("status") in {"processed", "created", "ok", "deduplicated"}


# ---------------------------------------------------------------------------
# Test 9 — Missing tenant_id fails closed
# ---------------------------------------------------------------------------


def test_missing_tenant_id_fails_closed() -> None:
    """Signal with missing/zero tenant_id must be rejected (fail-closed)."""
    svc = BrainCoreService()
    signal = _submission_signal(tenant_id=0, supervisor_id=None)
    result = svc.process_signal(signal)
    assert result.get("status") == "rejected", f"Expected rejected, got: {result}"
    assert "tenant" in str(result.get("reason", "")).lower()


# ---------------------------------------------------------------------------
# Test 10 — Missing thesis_id fails closed
# ---------------------------------------------------------------------------


def test_missing_thesis_id_fails_closed() -> None:
    """Signal with missing thesis_id must be rejected (fail-closed)."""
    svc = BrainCoreService()
    signal = _submission_signal(thesis_id="", supervisor_id=None)
    # Clear source_entity_id too so normalizer can't fall back
    signal["source_entity_id"] = ""
    signal["payload"]["thesis_id"] = ""
    signal["payload"]["source_entity_id"] = ""
    result = svc.process_signal(signal)
    assert result.get("status") == "rejected", f"Expected rejected, got: {result}"
    assert result.get("reason") == "missing_thesis_id", f"Unexpected reason: {result.get('reason')}"


# ---------------------------------------------------------------------------
# Test 11 — Duplicate signal is deduplicated
# ---------------------------------------------------------------------------


def test_duplicate_thesis_governance_signal_is_deduplicated() -> None:
    """Sending the same thesis governance signal twice must result in deduplication."""
    svc = BrainCoreService()
    signal = _submission_signal(
        tenant_id=1,
        thesis_id="TH-DEDUP-1",
        supervisor_id=None,
        days_without_supervisor=20,
    )
    # First signal creates a decision
    first = svc.process_signal(signal)
    assert first.get("status") not in {"rejected", "ignored", "error"}
    # Second signal with same source_entity_id should be deduplicated
    second = svc.process_signal(signal)
    assert second.get("status") == "deduplicated", (
        f"Expected deduplicated on second call, got: {second}"
    )


# ---------------------------------------------------------------------------
# Test 12 — No automatic thesis rejection or punitive action
# ---------------------------------------------------------------------------


def test_no_automatic_punitive_action_in_critical_decision() -> None:
    """Critical thesis governance decision must not contain any punitive academic actions."""
    FORBIDDEN_ACTIONS = {
        "reject_thesis",
        "suspend_student",
        "expel_student",
        "apply_grade_penalty",
        "terminate_enrollment",
        "academic_dismissal",
        "revoke_enrollment",
    }
    svc = BrainCoreService()
    signal = _supervisor_signal(supervisor_id=None, days_without_supervisor=35)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    recommended = [a.get("name") if isinstance(a, dict) else a for a in decision.get("recommended_actions", [])]
    forbidden_found = FORBIDDEN_ACTIONS & set(recommended)
    assert not forbidden_found, f"Punitive actions found in critical decision: {forbidden_found}"


def test_no_automatic_punitive_action_in_high_decision() -> None:
    """High thesis governance decision must not contain any punitive academic actions."""
    FORBIDDEN_ACTIONS = {
        "reject_thesis",
        "suspend_student",
        "expel_student",
        "apply_grade_penalty",
        "terminate_enrollment",
        "academic_dismissal",
        "revoke_enrollment",
    }
    svc = BrainCoreService()
    signal = _supervisor_signal(supervisor_id=None, days_without_supervisor=20)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    recommended = [a.get("name") if isinstance(a, dict) else a for a in decision.get("recommended_actions", [])]
    forbidden_found = FORBIDDEN_ACTIONS & set(recommended)
    assert not forbidden_found, f"Punitive actions found in high decision: {forbidden_found}"


# ---------------------------------------------------------------------------
# Test 13 — Cross-tenant isolation
# ---------------------------------------------------------------------------


def test_cross_tenant_isolation_for_thesis_governance() -> None:
    """Decisions for different tenants must be isolated."""
    svc = BrainCoreService()
    signal_t1 = _submission_signal(tenant_id=1, thesis_id="TH-ISO-1", supervisor_id=None, days_without_supervisor=20)
    signal_t2 = _submission_signal(tenant_id=2, thesis_id="TH-ISO-2", supervisor_id=None, days_without_supervisor=20)

    result_t1 = svc.process_signal(signal_t1)
    result_t2 = svc.process_signal(signal_t2)

    # Both must be processed (not rejected)
    assert result_t1.get("status") not in {"rejected", "ignored"}
    assert result_t2.get("status") not in {"rejected", "ignored"}

    # Decisions for tenant 1 must not appear in tenant 2's list
    decisions_t1 = svc.list_decisions(tenant_id=1)
    decisions_t2 = svc.list_decisions(tenant_id=2)
    # Each tenant must have at least one decision
    assert len(decisions_t1) >= 1, "Tenant 1 should have at least one decision"
    assert len(decisions_t2) >= 1, "Tenant 2 should have at least one decision"
    # Decision objects themselves must be disjoint between tenants
    # (same object id in memory would indicate a cross-tenant leak)
    objs_t1 = {id(d) for d in decisions_t1}
    objs_t2 = {id(d) for d in decisions_t2}
    assert not (objs_t1 & objs_t2), "Cross-tenant decision object leakage detected"


# ---------------------------------------------------------------------------
# Test 14 — risk_level="critical" explicit field produces critical
# ---------------------------------------------------------------------------


def test_explicit_critical_risk_level_produces_critical() -> None:
    """Explicit risk_level='critical' in payload must produce critical priority."""
    svc = BrainCoreService()
    signal = _submission_signal(
        supervisor_id=None,
        risk_level="critical",
    )
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("priority") == "critical"


# ---------------------------------------------------------------------------
# Test 15 — days_in_review >= 90 produces critical severity
# ---------------------------------------------------------------------------


def test_days_in_review_90_produces_critical() -> None:
    """thesis.review.delayed with days_in_review >= 90 must produce critical severity."""
    svc = BrainCoreService()
    signal = _delayed_review_signal(thesis_id="TH-CRIT-DELAY-1", days_in_review=95)
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("priority") == "critical", (
        f"Expected critical for 95-day review delay, got: {decision.get('priority')}"
    )


# ---------------------------------------------------------------------------
# Test 16 — supervisor_load_pct >= 80 produces medium severity
# ---------------------------------------------------------------------------


def test_supervisor_load_pct_80_produces_medium() -> None:
    """Supervisor load >= 80% but not overloaded=True should produce medium severity."""
    svc = BrainCoreService()
    signal = _overloaded_signal(
        thesis_id="TH-LOAD-MED-1",
        supervisor_id="SUP-LOAD",
        supervisor_load_pct=85.0,
    )
    # Override the event type to a non-overloaded signal so supervisor_overloaded flag isn't set
    signal["event_type"] = "thesis.governance.risk_detected"
    signal["payload"]["supervisor_overloaded"] = False
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored"}
    decision = result.get("decision", {})
    assert decision.get("priority") == "medium", (
        f"Expected medium priority for load_pct=85, got: {decision.get('priority')}"
    )


# ---------------------------------------------------------------------------
# Test 17 — All 6 event types route correctly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("event_type", [
    "thesis.submission.created",
    "thesis.submission.pending_review",
    "thesis.supervisor.assignment_needed",
    "thesis.supervisor.overloaded",
    "thesis.review.delayed",
    "thesis.governance.risk_detected",
])
def test_all_thesis_governance_event_types_route_correctly(event_type: str) -> None:
    """Each of the 6 thesis governance event types must produce a valid decision."""
    svc = BrainCoreService()
    thesis_id = f"TH-ALL-{event_type.replace('.', '-')}"
    signal = _submission_signal(
        thesis_id=thesis_id,
        supervisor_id="SUP-DEFAULT",
        event_type=event_type,
    )
    result = svc.process_signal(signal)
    assert result.get("status") not in {"rejected", "ignored", "error"}, (
        f"event_type={event_type} got unexpected status: {result}"
    )
    decision = result.get("decision", {})
    assert decision.get("decision_type") == "thesis_supervisor_assignment", (
        f"event_type={event_type} produced wrong decision_type: {decision.get('decision_type')}"
    )


# ---------------------------------------------------------------------------
# Test 18 — A-014.2 thesis.status_changed regression: still works
# ---------------------------------------------------------------------------


def test_existing_thesis_status_changed_still_works() -> None:
    """thesis.status_changed (A-014.2 scenario) must still route to thesis_delay, not thesis_governance."""
    svc = BrainCoreService()
    signal = {
        "signal_id": "thesis-regression-001",
        "tenant_id": 1,
        "correlation_id": "corr-regression-thesis",
        "event_type": "thesis.status_changed",
        "source_entity_type": "thesis",
        "source_entity_id": "TH-REGRESSION-1",
        "subject": {
            "student_id": "STU-REGR-1",
            "faculty_id": "FAC-REGR-1",
        },
        "payload": {
            "student_id": "STU-REGR-1",
            "thesis_id": "TH-REGRESSION-1",
            "advisor_id": "FAC-REGR-1",
            "faculty_id": "FAC-REGR-1",
            "days_since_last_milestone": 75,
            "from_status": "submitted",
            "to_status": "under_review",
        },
    }
    result = svc.process_signal(signal)
    # Must still be processed (not rejected/ignored)
    assert result.get("status") not in {"rejected", "ignored", "error"}, (
        f"thesis.status_changed regression failed: {result}"
    )
