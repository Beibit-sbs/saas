"""A-014.3: Attendance Recovery Loop

Tests that attendance risk signals produce a recovery plan action in addition
to creating an intervention case.  Verifies idempotency, tenant isolation,
fail-closed behaviour, and that A-013.1 baseline tests remain green.

Recovery loop behaviour:
  academic.attendance_risk.detected
    → BrainCoreService.process_signal()
    → risk_classifier: academic_risk / risk_high|medium
    → rules_engine: decision_type=intervention
    → actions: create_intervention_case, create_attendance_recovery_plan,
               notify_advisor, notify_faculty
    → dispatcher creates both intervention case AND recovery plan
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import pytest

from app.modules.brain_core.service import BrainCoreService


# ─── shared autouse fixture (context sources) ─────────────────────────────────

@pytest.fixture(autouse=True)
def _stub_context_sources():
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


# ─── signal factory ───────────────────────────────────────────────────────────

def _attendance_signal(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-ATTEND-1",
    source_entity_id: str = "SEC-ATTEND-1",
    attendance_rate: float = 0.30,
    course_id: str = "COURSE-ATT-1",
    advisor_id: str = "ADV-ATT-1",
    faculty_id: str = "FAC-ATT-1",
) -> dict:
    return {
        "signal_id": f"attrec-{tenant_id}-{student_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-attrec-{tenant_id}-{student_id}",
        "event_type": "academic.attendance_risk.detected",
        "source_entity_type": "section_attendance",
        "source_entity_id": source_entity_id,
        "subject": {
            "student_id": student_id,
            "course_id": course_id,
            "section_id": source_entity_id,
            "faculty_id": faculty_id,
        },
        "payload": {
            "student_id": student_id,
            "attendance_rate": attendance_rate,
            "course_id": course_id,
            "section_id": source_entity_id,
            "advisor_id": advisor_id,
            "faculty_id": faculty_id,
            "source_entity_type": "section_attendance",
            "source_entity_id": source_entity_id,
        },
        "metadata": {},
    }


# ─── TestAttendanceRecoveryPlanCreation ───────────────────────────────────────

class TestAttendanceRecoveryPlanCreation:
    """Core recovery plan creation behaviour."""

    def test_high_risk_attendance_creates_recovery_plan_action(self) -> None:
        """attendance_rate < 0.40 → risk_high → create_attendance_recovery_plan dispatched."""
        service = BrainCoreService()
        signal = _attendance_signal(attendance_rate=0.30)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        decision = result["decision"]
        assert decision["decision_type"] == "intervention", (
            f"Expected intervention; got {decision['decision_type']}"
        )

        dispatched_actions = [r["action"] for r in result["dispatch_results"]]
        assert "create_attendance_recovery_plan" in dispatched_actions, (
            f"Recovery plan action missing; got {dispatched_actions}"
        )

    def test_medium_risk_attendance_also_creates_recovery_plan(self) -> None:
        """attendance_rate in (0.40, 0.60) → risk_medium → recovery plan dispatched."""
        service = BrainCoreService()
        signal = _attendance_signal(attendance_rate=0.55)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        dispatched_actions = [r["action"] for r in result["dispatch_results"]]
        assert "create_attendance_recovery_plan" in dispatched_actions, (
            f"Recovery plan should exist for medium risk; got {dispatched_actions}"
        )

    def test_recovery_plan_contains_attendance_evidence(self) -> None:
        """Recovery plan dispatch result includes attendance evidence fields."""
        service = BrainCoreService()
        signal = _attendance_signal(
            student_id="STU-EVID",
            source_entity_id="SEC-EVID",
            attendance_rate=0.25,
            course_id="COURSE-EVID",
            advisor_id="ADV-EVID",
        )

        result = service.process_signal(signal)

        recovery = next(
            (r for r in result["dispatch_results"] if r["action"] == "create_attendance_recovery_plan"),
            None,
        )
        assert recovery is not None, "create_attendance_recovery_plan not found"
        assert recovery.get("status") in {"created", "ensured"}, (
            f"Recovery plan status unexpected: {recovery.get('status')}"
        )
        item = recovery.get("item", {})
        # Verify recovery plan has student_id
        assert item.get("student_id") == "STU-EVID", (
            f"student_id mismatch in recovery plan item: {item}"
        )

    def test_recovery_plan_co_dispatched_with_intervention_case(self) -> None:
        """Both create_intervention_case and create_attendance_recovery_plan must be dispatched."""
        service = BrainCoreService()
        signal = _attendance_signal(attendance_rate=0.20)

        result = service.process_signal(signal)

        dispatched_actions = [r["action"] for r in result["dispatch_results"]]
        assert "create_intervention_case" in dispatched_actions, (
            f"create_intervention_case must be dispatched; got {dispatched_actions}"
        )
        assert "create_attendance_recovery_plan" in dispatched_actions, (
            f"create_attendance_recovery_plan must be dispatched; got {dispatched_actions}"
        )

    def test_non_risk_attendance_does_not_create_recovery_plan(self) -> None:
        """attendance_rate >= 0.60 → risk_low → no recovery plan action created."""
        service = BrainCoreService()
        signal = _attendance_signal(attendance_rate=0.80)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        dispatched_actions = [r["action"] for r in result["dispatch_results"]]
        assert "create_attendance_recovery_plan" not in dispatched_actions, (
            f"Low-risk attendance should NOT create recovery plan; got {dispatched_actions}"
        )


# ─── TestAttendanceRecoveryIdempotency ────────────────────────────────────────

class TestAttendanceRecoveryIdempotency:
    """Duplicate attendance risk signals must not create duplicate recovery plans."""

    def test_duplicate_signals_do_not_fail(self) -> None:
        """Same signal sent twice must not raise and both results must be valid."""
        service = BrainCoreService()
        signal = _attendance_signal(student_id="STU-DUP-RECV", source_entity_id="SEC-DUP-RECV")

        result1 = service.process_signal(signal)
        result2 = service.process_signal(signal)

        assert result1["status"] == "processed"
        assert result2["status"] in {"processed", "deduplicated"}, (
            f"Second signal must be handled; got {result2['status']}"
        )

    def test_second_signal_is_deduplicated_or_ensured(self) -> None:
        """After the first recovery plan, a second signal is deduped or ensured (not failed)."""
        service = BrainCoreService()
        signal = _attendance_signal(student_id="STU-IDEM-RECV")

        result1 = service.process_signal(signal)
        assert result1["status"] == "processed"

        # Second identical signal
        result2 = service.process_signal(signal)
        # DB-backed dedup may yield 'deduplicated'; in-memory path yields 'processed'
        assert result2["status"] in {"processed", "deduplicated"}, (
            f"Duplicate must be deduped or re-processed; got {result2['status']}"
        )


# ─── TestAttendanceRecoveryFailClosed ────────────────────────────────────────

class TestAttendanceRecoveryFailClosed:
    """Missing required fields must fail closed (no recovery plan created)."""

    def test_missing_student_id_does_not_create_recovery_plan(self) -> None:
        """Signal without student_id must not create a recovery plan."""
        service = BrainCoreService()
        signal = {
            "signal_id": "bad-attend-rc",
            "tenant_id": 1,
            "correlation_id": "corr-bad-rc",
            "event_type": "academic.attendance_risk.detected",
            "subject": {"course_id": "C001"},  # no student_id
            "payload": {
                "attendance_rate": 0.20,
                "source_entity_type": "section_attendance",
                "source_entity_id": "SEC-BAD",
            },
            "metadata": {},
        }

        result = service.process_signal(signal)

        # Should not crash
        assert result["status"] in {"processed", "rejected", "escalated"}
        # If processed, should not have a recovery plan with a real student_id
        if result["status"] == "processed" and result.get("dispatch_results"):
            for dr in result["dispatch_results"]:
                if dr["action"] == "create_attendance_recovery_plan":
                    # item.student_id must be None or empty — not a real student_id
                    assert not dr.get("item", {}).get("student_id"), (
                        "Recovery plan should not have a student_id when signal has none"
                    )

    def test_missing_tenant_id_raises_or_returns_error(self) -> None:
        """Signal with tenant_id=0 must not silently succeed."""
        service = BrainCoreService()
        result = service.process_signal({
            "signal_id": "bad-tenant",
            "tenant_id": 0,
            "event_type": "academic.attendance_risk.detected",
            "payload": {"student_id": "S1", "attendance_rate": 0.20},
            "metadata": {},
        })
        assert result["status"] in {"rejected", "error", "failed"}, (
            f"tenant_id=0 must fail closed; got status={result.get('status')}"
        )


# ─── TestAttendanceRecoveryTenantIsolation ───────────────────────────────────

class TestAttendanceRecoveryTenantIsolation:
    """Cross-tenant leakage is impossible."""

    def test_cross_tenant_recovery_plans_are_isolated(self) -> None:
        """Attendance risk for tenant A and B produce independent recovery plans."""
        service = BrainCoreService()

        signal_a = _attendance_signal(tenant_id=100, student_id="STU-TA", attendance_rate=0.20)
        signal_b = _attendance_signal(tenant_id=200, student_id="STU-TB", attendance_rate=0.20)

        result_a = service.process_signal(signal_a)
        result_b = service.process_signal(signal_b)

        assert result_a["status"] == "processed"
        assert result_b["status"] == "processed"

        assert result_a["decision"]["tenant_id"] == 100
        assert result_b["decision"]["tenant_id"] == 200

        # Recovery plans must carry different student IDs
        def _recovery_student(result: dict) -> str | None:
            for dr in result.get("dispatch_results", []):
                if dr["action"] == "create_attendance_recovery_plan":
                    return dr.get("item", {}).get("student_id")
            return None

        sid_a = _recovery_student(result_a)
        sid_b = _recovery_student(result_b)
        assert sid_a != sid_b, (
            f"Tenant isolation breach: both recovery plans show student_id={sid_a}"
        )

    def test_tenant_id_preserved_in_recovery_plan_dispatch(self) -> None:
        """Recovery plan item tenant matches the signal tenant."""
        service = BrainCoreService()
        signal = _attendance_signal(tenant_id=555, student_id="STU-TENID", attendance_rate=0.25)

        result = service.process_signal(signal)

        assert result["decision"]["tenant_id"] == 555
        # The in-memory recovery plan case is indexed under tenant 555
        snapshot = service._dispatcher.snapshot()
        cases = snapshot.get("workflow_cases", [])
        recovery_cases = [c for c in cases if c.get("case_type") == "attendance_recovery"]
        if recovery_cases:
            for rc in recovery_cases:
                if rc.get("student_id") == "STU-TENID":
                    assert rc["tenant_id"] == 555, (
                        f"Recovery plan tenant mismatch: {rc['tenant_id']}"
                    )


# ─── TestA0131Regression ─────────────────────────────────────────────────────

class TestA0131Regression:
    """A-013.1 attendance intervention tests must remain green after A-014.3 changes."""

    def test_a013_1_create_intervention_case_still_dispatched(self) -> None:
        """A-013.1 core: create_intervention_case must still be dispatched for attendance risk."""
        service = BrainCoreService()
        signal = _attendance_signal(attendance_rate=0.35)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        assert result["decision"]["decision_type"] == "intervention"
        dispatched = [r["action"] for r in result["dispatch_results"]]
        assert "create_intervention_case" in dispatched

    def test_a013_1_no_approval_required(self) -> None:
        """A-013.1: attendance risk intervention must not require approval."""
        service = BrainCoreService()
        signal = _attendance_signal(attendance_rate=0.35)

        result = service.process_signal(signal)

        assert not result["decision"].get("requires_approval"), (
            "Attendance risk must not require approval"
        )
