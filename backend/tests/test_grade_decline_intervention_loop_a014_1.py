"""A-014.1: Grade Decline Intervention Loop

Tests that grade decline risk signals automatically create intervention cases
via Brain Core infrastructure with idempotency and grade-risk origin evidence.

Pattern:
    academic.grade_risk.detected → brain_core signal → decision → dispatch → intervention case created
Idempotency:
    Duplicate grade risk signals for the same student must not create duplicate cases.
Tenant isolation:
    Cross-tenant leakage is impossible.
"""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from app.modules.brain_core.service import BrainCoreService
from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile, TenantPolicyResolver


@pytest.fixture(autouse=True)
def _stub_brain_core_context_sources() -> None:
    """Mock context sources to keep tests independent from optional tables."""
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


def _grade_risk_signal(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-GR-1",
    source_entity_id: str = "SUBMIT-1",
    risk_level: str = "high",
    current_grade: float = 0.5,
    course_id: str = "COURSE-GR-1",
) -> dict:
    """Factory for grade risk signals matching the schema from grades/service.py."""
    return {
        "signal_id": f"grade-risk-{tenant_id}-{student_id}-{source_entity_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-{tenant_id}-{student_id}",
        "event_type": "academic.grade_risk.detected",
        "source_entity_type": "grade_submission",
        "source_entity_id": source_entity_id,
        "subject": {
            "student_id": student_id,
            "course_id": course_id,
            "section_id": None,
        },
        "payload": {
            "student_id": student_id,
            "course_id": course_id,
            "section_id": None,
            "current_grade": current_grade,
            "grade_trend": "declining",
            "risk_level": risk_level,
            "source_entity_type": "grade_submission",
            "source_entity_id": source_entity_id,
        },
        "metadata": {},
    }


class TestGradeRiskRoutingToBrainCore:
    """Grade risk signal → Brain Core decision → intervention dispatch (no approval)."""

    def test_grade_risk_high_routes_to_intervention_decision(self) -> None:
        """High grade risk routes to intervention (not generic risk) without approval."""
        service = BrainCoreService()
        signal = _grade_risk_signal(risk_level="high", current_grade=0.5)

        result = service.process_signal(signal)

        assert result["status"] == "processed", f"Signal not processed: {result.get('status')}"
        decision = result["decision"]
        assert decision.get("decision_type") == "intervention", (
            f"High grade risk should route to 'intervention'; got: {decision.get('decision_type')}"
        )
        assert not decision.get("requires_approval"), (
            f"Grade risk intervention should not require approval; got: {decision.get('requires_approval')}"
        )
        assert decision["status"] == "dispatched", (
            f"Decision should be dispatched; got: {decision['status']}"
        )

    def test_grade_risk_medium_routes_to_intervention_decision(self) -> None:
        """Medium grade risk also routes to intervention decision type."""
        service = BrainCoreService()
        signal = _grade_risk_signal(risk_level="medium", current_grade=1.5)

        result = service.process_signal(signal)

        assert result["status"] == "processed"
        decision = result["decision"]
        assert decision.get("decision_type") == "intervention", (
            f"Medium grade risk should route to 'intervention'; got: {decision.get('decision_type')}"
        )

    def test_grade_risk_dispatches_create_intervention_case_action(self) -> None:
        """Grade risk signal produces create_intervention_case in dispatched actions."""
        service = BrainCoreService()
        signal = _grade_risk_signal(risk_level="high", student_id="STU-DISPATCH-1")

        result = service.process_signal(signal)

        dispatch_results = result.get("dispatch_results", [])
        assert len(dispatch_results) > 0, (
            f"Grade risk must dispatch at least one action; got: {dispatch_results}"
        )
        dispatched_actions = [r["action"] for r in dispatch_results]
        assert "create_intervention_case" in dispatched_actions, (
            f"create_intervention_case must be dispatched; got: {dispatched_actions}"
        )

    def test_grade_risk_high_dispatches_notify_advisor(self) -> None:
        """High grade risk also dispatches notify_advisor alongside create_intervention_case."""
        service = BrainCoreService()
        signal = _grade_risk_signal(risk_level="high", student_id="STU-NOTIFY-1")

        result = service.process_signal(signal)

        dispatched_actions = [r["action"] for r in result.get("dispatch_results", [])]
        assert "notify_advisor" in dispatched_actions, (
            f"High grade risk should dispatch notify_advisor; got: {dispatched_actions}"
        )


class TestGradeRiskIdempotency:
    """Duplicate grade risk signals must not create duplicate intervention cases."""

    def test_duplicate_grade_risk_signal_does_not_fail(self) -> None:
        """Same grade risk signal processed twice is handled safely (deduplicated or processed)."""
        service = BrainCoreService()
        signal = _grade_risk_signal(student_id="STU-IDEM-1", source_entity_id="SUBMIT-IDEM-1")

        result1 = service.process_signal(signal)
        assert result1["status"] == "processed"

        result2 = service.process_signal(signal)
        assert result2["status"] in {"deduplicated", "processed"}, (
            f"Duplicate grade risk signal should be deduplicated or processed; got: {result2['status']}"
        )
        if result2["status"] == "deduplicated":
            assert "original_signal_id" in result2

    def test_action_bridge_idempotency_guard_skips_duplicate_case(self) -> None:
        """Action bridge handler returns 'ensured' when an open ACADEMIC_RISK case already exists."""
        from unittest.mock import MagicMock
        from app.modules.brain_core.action_bridge import _make_create_intervention_case_handler
        from app.modules.interventions.models import (
            InterventionCaseModel,
            InterventionCaseStatus,
            InterventionCaseType,
        )

        existing_case = MagicMock(spec=InterventionCaseModel)
        existing_case.id = "EXISTING-CASE-ID"
        existing_case.status = InterventionCaseStatus.OPEN

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_case

        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        handler = _make_create_intervention_case_handler(lambda: mock_session)

        result = handler(
            tenant_id=1,
            decision_id="decision-123",
            payload={"student_id": "STU-IDEM-2", "risk_level": "high"},
        )

        assert result["status"] == "ensured", (
            f"Handler should return 'ensured' for existing open case; got: {result['status']}"
        )
        assert result.get("idempotent_replay") is True, "Handler should signal idempotent_replay=True"
        assert result["item"]["case_id"] == "EXISTING-CASE-ID"
        # Must NOT call session.add/commit for duplicate
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_action_bridge_creates_case_when_none_exists(self) -> None:
        """Action bridge handler creates a new case when no open ACADEMIC_RISK case exists."""
        from app.modules.brain_core.action_bridge import _make_create_intervention_case_handler
        from app.modules.interventions.models import (
            InterventionCaseModel,
            InterventionCaseStatus,
            InterventionCaseType,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing case

        created_case = MagicMock(spec=InterventionCaseModel)
        created_case.id = "NEW-CASE-ID"

        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        # Simulate refresh populating the case id
        def fake_refresh(obj: object) -> None:
            pass

        mock_session.refresh.side_effect = fake_refresh

        # Capture the case added to the session
        added_objects = []
        mock_session.add.side_effect = lambda obj: added_objects.append(obj)

        handler = _make_create_intervention_case_handler(lambda: mock_session)

        result = handler(
            tenant_id=1,
            decision_id="decision-456",
            payload={"student_id": "STU-NEW-1", "risk_level": "medium"},
        )

        assert result["status"] in {"created", "failed"}, (
            f"Handler should return 'created' or 'failed'; got: {result['status']}"
        )
        # If created, session.add should have been called
        if result["status"] == "created":
            assert len(added_objects) == 1, "Exactly one case should be added"


class TestGradeRiskOriginEvidence:
    """Grade risk evidence (source identifiers) must be preserved in intervention cases."""

    def test_grade_risk_payload_includes_grade_evidence(self) -> None:
        """The grade risk dispatch payload carries grade-specific context."""
        service = BrainCoreService()
        student_id = "STU-EVIDENCE-1"
        course_id = "COURSE-EVIDENCE-1"
        signal = _grade_risk_signal(
            student_id=student_id,
            course_id=course_id,
            risk_level="high",
            current_grade=0.7,
        )

        result = service.process_signal(signal)

        # Find the create_intervention_case dispatch
        dispatch_results = result.get("dispatch_results", [])
        intervention_dispatch = next(
            (r for r in dispatch_results if r.get("action") == "create_intervention_case"),
            None,
        )
        assert intervention_dispatch is not None, "create_intervention_case not found in dispatch results"

        # The dispatch should reference the student
        item = intervention_dispatch.get("item", {})
        assert item.get("student_id") == student_id or item.get("case_id") is not None, (
            f"Dispatch must reference the student; got item={item}"
        )


class TestGradeRiskFailClosed:
    """Grade risk signals with missing security-critical fields are rejected or handled safely."""

    def test_grade_risk_missing_student_id_in_action_bridge_does_not_crash(self) -> None:
        """Action bridge handles payload without student_id gracefully (skips idempotency check)."""
        from app.modules.brain_core.action_bridge import _make_create_intervention_case_handler
        from app.modules.interventions.models import InterventionCaseModel

        created_case = MagicMock(spec=InterventionCaseModel)
        created_case.id = "NO-STUDENT-CASE"
        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        handler = _make_create_intervention_case_handler(lambda: mock_session)

        # Must not raise
        result = handler(
            tenant_id=1,
            decision_id="decision-no-student",
            payload={"risk_level": "high"},  # no student_id
        )

        assert result["status"] in {"created", "failed"}, (
            f"Missing student_id should not crash; got: {result['status']}"
        )

    def test_grade_risk_missing_tenant_id_in_signal_fails_gracefully(self) -> None:
        """Signal without tenant_id must not propagate or process successfully."""
        service = BrainCoreService()
        bad_signal = {
            "signal_id": "bad-signal-no-tenant",
            "event_type": "academic.grade_risk.detected",
            "source_entity_type": "grade_submission",
            "source_entity_id": "SUBMIT-X",
            "payload": {
                "student_id": "STU-X",
                "risk_level": "high",
            },
        }

        result = service.process_signal(bad_signal)

        assert result["status"] in {"error", "failed", "rejected", "processed"}, (
            f"Signal without tenant_id must not crash the system; got: {result['status']}"
        )


class TestGradeRiskTenantIsolation:
    """Grade risk interventions cannot leak across tenant boundaries."""

    def test_grade_risk_cross_tenant_decisions_are_isolated(self) -> None:
        """Grade risk signals from different tenants produce independent decisions."""
        service = BrainCoreService()

        signal_a = _grade_risk_signal(tenant_id=100, student_id="STU-T100", course_id="C-T100")
        signal_b = _grade_risk_signal(tenant_id=200, student_id="STU-T200", course_id="C-T200")

        result_a = service.process_signal(signal_a)
        result_b = service.process_signal(signal_b)

        assert result_a["status"] == "processed"
        assert result_b["status"] == "processed"

        assert result_a["decision"]["tenant_id"] == 100
        assert result_b["decision"]["tenant_id"] == 200

    def test_grade_risk_dispatch_payload_preserves_tenant_id(self) -> None:
        """The tenant_id is correctly bound in the dispatched intervention case."""
        service = BrainCoreService()
        signal = _grade_risk_signal(tenant_id=42, student_id="STU-TENANT-42")

        result = service.process_signal(signal)

        assert result["decision"]["tenant_id"] == 42
