"""A-016.5: Academic Integrity Case Resolution Automation Brain.

Ensures case resolution signals route through Brain Core into the
academic_integrity_case_resolution scenario with deterministic, explainable
severity.

Safety invariants:
- no automatic punitive action (no grade change, suspension, expulsion)
- no automatic approval, rejection, or sanction
- high/critical requires human approval (requires_approval=True)
- missing tenant_id fails closed
- missing case reference (source_decision_id/case_id/source_entity_id) fails closed
- missing optional context (reviewer_id, committee_id) does not crash
- cross-wave regressions remain green (A-016.1/2/3/4 paths)
"""

from __future__ import annotations

from contextlib import ExitStack
from uuid import uuid4

import pytest

from app.modules.brain_core.registry import SignalRegistry
from app.modules.brain_core.service import BrainCoreService


@pytest.fixture(autouse=True)
def _stub_context_sources() -> None:
    with ExitStack() as stack:
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_academic_context",
                return_value={"student_profile": None, "academic_health_snapshot": {}},
            )
        )
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_student_success_context",
                return_value={"active_interventions": 0, "open_advising_tasks": 0},
            )
        )
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_faculty_context",
                return_value={"faculty_health_snapshot": {}},
            )
        )
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_finance_context",
                return_value={"billing_health_snapshot": {}, "procurement_health_snapshot": {}},
            )
        )
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_operations_context",
                return_value={"operations_health_snapshot": {}},
            )
        )
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_platform_context",
                return_value={"platform_health_snapshot": {}},
            )
        )
        stack.enter_context(
            __import__("unittest.mock").mock.patch(
                "app.modules.brain_core.context_builder.fetch_scheduling_context",
                return_value={"scheduling_health_snapshot": {}},
            )
        )
        yield


# ---------------------------------------------------------------------------
# Signal factory helpers
# ---------------------------------------------------------------------------

def _case_resolution_signal(
    *,
    tenant_id: int = 1,
    event_type: str = "academic_integrity.case.opened",
    source_decision_id: str = "DEC-001",
    case_id: str = "CASE-001",
    source_entity_id: str | None = None,
    source_decision_type: str = "academic_integrity_review",
    source_scenario: str = "academic_integrity_violation",
    student_id: str = "STU-001",
    risk_level: str | None = None,
    days_open: int | None = None,
    evidence_items: list | None = None,
    reviewer_id: str | None = None,
    committee_id: str | None = None,
    signal_id: str | None = None,
) -> dict:
    payload: dict = {
        "source_decision_id": source_decision_id,
        "case_id": case_id,
        "source_decision_type": source_decision_type,
        "source_scenario": source_scenario,
        "student_id": student_id,
        "source_entity_type": "integrity_case",
        "source_entity_id": source_entity_id or case_id,
    }
    if risk_level is not None:
        payload["risk_level"] = risk_level
    if days_open is not None:
        payload["days_open"] = days_open
    if evidence_items is not None:
        payload["evidence_items"] = evidence_items
    if reviewer_id is not None:
        payload["reviewer_id"] = reviewer_id
    if committee_id is not None:
        payload["committee_id"] = committee_id

    return {
        "event_type": event_type,
        "tenant_id": tenant_id,
        "signal_id": signal_id or str(uuid4()),
        "source_entity_type": "integrity_case",
        "source_entity_id": source_entity_id or case_id,
        "source_module": "academic_integrity",
        "correlation_id": str(uuid4()),
        "payload": payload,
    }


def _decision(result: dict) -> dict:
    return result.get("decision", {})


# ---------------------------------------------------------------------------
# Test 1-3: All three source decision types route to integrity_case_resolution
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("event_type", [
    "academic_integrity.case.opened",
    "academic_integrity.case.evidence_requested",
    "academic_integrity.case.review_required",
    "academic_integrity.case.resolved",
    "academic_integrity.case.dismissed",
    "integrity.resolution.workflow_needed",
])
def test_all_case_resolution_events_route_to_correct_scenario(event_type: str) -> None:
    """All 6 A-016.5 event types route to academic_integrity_case_resolution scenario."""
    assert event_type in SignalRegistry.signals
    assert SignalRegistry.signals[event_type]["scenario"] == "academic_integrity_case_resolution"


def test_academic_integrity_review_source_opens_review_case() -> None:
    """A signal from academic_integrity_review source decision produces case resolution decision."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        source_decision_type="academic_integrity_review",
    ))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "integrity_case_resolution"


def test_exam_integrity_review_source_opens_review_case() -> None:
    """A signal from exam_integrity_review source decision produces case resolution decision."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        source_decision_type="exam_integrity_review",
        source_scenario="exam_proctoring_violation",
    ))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "integrity_case_resolution"


def test_research_ethics_review_source_opens_review_case() -> None:
    """A signal from research_ethics_review source decision produces case resolution decision."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        source_decision_type="research_ethics_review",
        source_scenario="research_ethics_compliance",
    ))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "integrity_case_resolution"


# ---------------------------------------------------------------------------
# Test 4: Duplicate source decision does not duplicate case/action
# ---------------------------------------------------------------------------

def test_duplicate_source_decision_does_not_duplicate_case() -> None:
    """Same signal_id/source dedup key does not produce duplicate decisions."""
    svc = BrainCoreService()
    sig = _case_resolution_signal(signal_id="DEDUP-SIG-001")
    r1 = svc.process_signal(dict(sig))
    r2 = svc.process_signal(dict(sig))
    assert r1["status"] not in {"rejected", "ignored"}, r1
    # Second call should be a duplicate
    assert r2.get("status") == "deduplicated"


# ---------------------------------------------------------------------------
# Test 5: High/critical cases require human approval
# ---------------------------------------------------------------------------

def test_critical_case_requires_human_approval() -> None:
    """CRITICAL severity always requires_approval=True — human-in-the-loop mandatory."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        risk_level="critical",
    ))
    decision = _decision(result)
    assert result["status"] not in {"rejected", "ignored"}, result
    assert decision.get("decision_type") == "integrity_case_resolution"
    assert decision.get("priority") == "critical"
    assert decision.get("requires_approval") is True


def test_high_case_requires_human_approval() -> None:
    """HIGH severity always requires_approval=True — human-in-the-loop mandatory."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        risk_level="high",
        days_open=20,
    ))
    decision = _decision(result)
    assert result["status"] not in {"rejected", "ignored"}, result
    assert decision.get("decision_type") == "integrity_case_resolution"
    assert decision.get("priority") == "high"
    assert decision.get("requires_approval") is True


def test_overdue_30_days_critical_requires_approval() -> None:
    """Cases open >= 30 days are CRITICAL and require human approval."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(days_open=30))
    decision = _decision(result)
    assert result["status"] not in {"rejected", "ignored"}, result
    assert decision.get("priority") == "critical"
    assert decision.get("requires_approval") is True


def test_overdue_14_days_high_requires_approval() -> None:
    """Cases open >= 14 days are HIGH and require human approval."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(days_open=14))
    decision = _decision(result)
    assert result["status"] not in {"rejected", "ignored"}, result
    assert decision.get("priority") == "high"
    assert decision.get("requires_approval") is True


def test_medium_case_does_not_require_approval() -> None:
    """MEDIUM severity does NOT require automatic approval — still awaits human review."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        risk_level="medium",
        evidence_items=[],
    ))
    decision = _decision(result)
    assert result["status"] not in {"rejected", "ignored"}, result
    assert decision.get("priority") == "medium"
    assert decision.get("requires_approval") is False


# ---------------------------------------------------------------------------
# Test 6: No automatic punitive action
# ---------------------------------------------------------------------------

PUNITIVE_ACTIONS = {
    "change_grade",
    "fail_exam",
    "reject_thesis",
    "suspend_student",
    "expel_student",
    "approve_violation",
    "reject_ethics_application",
    "impose_disciplinary_sanction",
    "automatic_sanction",
}


def test_no_automatic_punitive_actions_in_critical_decision() -> None:
    """Critical case resolution must NOT include any punitive automated actions."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(risk_level="critical"))
    actions = set(_decision(result).get("recommended_actions") or [])
    assert not actions & PUNITIVE_ACTIONS, f"Punitive actions found: {actions & PUNITIVE_ACTIONS}"


def test_no_automatic_punitive_actions_in_high_decision() -> None:
    """High case resolution must NOT include any punitive automated actions."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(risk_level="high"))
    actions = set(_decision(result).get("recommended_actions") or [])
    assert not actions & PUNITIVE_ACTIONS, f"Punitive actions found: {actions & PUNITIVE_ACTIONS}"


def test_close_as_violation_action_requires_approval() -> None:
    """close_as_violation_requires_approval action only appears with requires_approval=True."""
    svc = BrainCoreService()
    # HIGH/CRITICAL path may include this action — check requires_approval is set
    result = svc.process_signal(_case_resolution_signal(risk_level="critical"))
    decision = _decision(result)
    if "close_as_violation_requires_approval" in (decision.get("recommended_actions") or []):
        assert decision.get("requires_approval") is True


# ---------------------------------------------------------------------------
# Test 7: Missing tenant_id fails closed
# ---------------------------------------------------------------------------

def test_missing_tenant_id_fails_closed() -> None:
    """Signal with tenant_id=0 must be rejected (fail-closed)."""
    svc = BrainCoreService()
    sig = _case_resolution_signal(tenant_id=0)
    result = svc.process_signal(sig)
    assert result["status"] == "rejected"
    assert "tenant" in result.get("reason", "")


def test_negative_tenant_id_fails_closed() -> None:
    """Signal with negative tenant_id must be rejected."""
    svc = BrainCoreService()
    sig = _case_resolution_signal(tenant_id=-1)
    result = svc.process_signal(sig)
    assert result["status"] == "rejected"


# ---------------------------------------------------------------------------
# Test 8: Missing case reference fails closed
# ---------------------------------------------------------------------------

def test_missing_all_case_references_fails_closed() -> None:
    """Signal with no source_decision_id, case_id, or source_entity_id must be rejected."""
    svc = BrainCoreService()
    sig = {
        "event_type": "academic_integrity.case.opened",
        "tenant_id": 1,
        "signal_id": str(uuid4()),
        "source_entity_type": "integrity_case",
        "source_entity_id": "",
        "source_module": "academic_integrity",
        "payload": {
            "source_decision_id": "",
            "case_id": "",
            "student_id": "STU-001",
            "source_entity_id": "",
        },
    }
    result = svc.process_signal(sig)
    assert result["status"] == "rejected"
    assert "case_reference" in result.get("reason", "")


# ---------------------------------------------------------------------------
# Test 9: Missing optional reviewer/committee does not crash
# ---------------------------------------------------------------------------

def test_missing_reviewer_does_not_crash() -> None:
    """reviewer_id absent does not raise — appears in payload defaults."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(reviewer_id=None, committee_id=None))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "integrity_case_resolution"


def test_missing_committee_does_not_crash() -> None:
    """committee_id absent does not raise — system proceeds with empty committee."""
    svc = BrainCoreService()
    sig = _case_resolution_signal()
    sig["payload"].pop("committee_id", None)
    result = svc.process_signal(sig)
    assert result["status"] not in {"rejected", "ignored"}, result


# ---------------------------------------------------------------------------
# Test 10: Overdue cases create escalation actionability
# ---------------------------------------------------------------------------

def test_overdue_case_escalation_action_present() -> None:
    """Cases open >= 30 days should have escalate_overdue_case in recommended_actions."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(days_open=30))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert "escalate_overdue_case" in (_decision(result).get("recommended_actions") or [])


# ---------------------------------------------------------------------------
# Test 11: Missing evidence creates request_evidence actionability
# ---------------------------------------------------------------------------

def test_missing_evidence_creates_request_evidence_action() -> None:
    """When evidence_items is empty, MEDIUM path should include request_evidence action."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        risk_level="medium",
        evidence_items=[],
    ))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert "request_evidence" in (_decision(result).get("recommended_actions") or [])


# ---------------------------------------------------------------------------
# Test 12: Decision type is correct
# ---------------------------------------------------------------------------

def test_decision_type_is_integrity_case_resolution() -> None:
    """All case resolution decisions must have decision_type='integrity_case_resolution'."""
    svc = BrainCoreService()
    for event_type in [
        "academic_integrity.case.opened",
        "academic_integrity.case.evidence_requested",
        "academic_integrity.case.review_required",
        "integrity.resolution.workflow_needed",
    ]:
        result = svc.process_signal(_case_resolution_signal(event_type=event_type))
        decision_type = _decision(result).get("decision_type")
        assert decision_type == "integrity_case_resolution", (
            f"event_type={event_type} got decision_type={decision_type}"
        )


# ---------------------------------------------------------------------------
# Test 13-16: Cross-wave A-016.1/2/3/4 regressions
# ---------------------------------------------------------------------------

def test_a016_1_academic_integrity_violation_regression() -> None:
    """A-016.1 academic integrity violation detection remains unaffected."""
    svc = BrainCoreService()
    result = svc.process_signal({
        "event_type": "academic_integrity.violation.detected",
        "tenant_id": 1,
        "signal_id": str(uuid4()),
        "source_entity_type": "student",
        "source_entity_id": "STU-REG1",
        "source_module": "academic_integrity",
        "payload": {
            "student_id": "STU-REG1",
            "course_id": "CRS-001",
            "violation_type": "plagiarism",
            "similarity_score": 0.85,
            "risk_category": "academic_integrity",
        },
    })
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "academic_integrity_review"


def test_a016_2_thesis_governance_regression() -> None:
    """A-016.2 thesis governance supervisor assignment remains unaffected."""
    svc = BrainCoreService()
    result = svc.process_signal({
        "event_type": "thesis.submission.created",
        "tenant_id": 1,
        "signal_id": str(uuid4()),
        "source_entity_type": "thesis",
        "source_entity_id": "THESIS-REG2",
        "source_module": "thesis",
        "payload": {
            "student_id": "STU-REG2",
            "thesis_id": "THESIS-REG2",
            "risk_category": "thesis_governance",
        },
    })
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "thesis_supervisor_assignment"


def test_a016_3_exam_proctoring_regression() -> None:
    """A-016.3 exam proctoring violation workflow remains unaffected."""
    svc = BrainCoreService()
    result = svc.process_signal({
        "event_type": "exam.proctoring.face_mismatch_detected",
        "tenant_id": 1,
        "signal_id": str(uuid4()),
        "source_entity_type": "exam",
        "source_entity_id": "EXAM-REG3",
        "source_module": "exam_proctoring",
        "payload": {
            "student_id": "STU-REG3",
            "exam_id": "EXAM-REG3",
            "face_mismatch": True,
            "risk_category": "exam_proctoring",
        },
    })
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "exam_integrity_review"


def test_a016_4_research_ethics_regression() -> None:
    """A-016.4 research ethics compliance review remains unaffected."""
    svc = BrainCoreService()
    result = svc.process_signal({
        "event_type": "research_ethics.high_risk.detected",
        "tenant_id": 1,
        "signal_id": str(uuid4()),
        "source_entity_type": "research_ethics_review",
        "source_entity_id": "ETH-REG4",
        "source_module": "research_ethics",
        "payload": {
            "researcher_id": "FAC-REG4",
            "project_id": "PROJ-REG4",
            "ethics_application_id": "ETH-REG4",
            "risk_level": "high",
            "risk_category": "ethics_compliance",
        },
    })
    assert result["status"] not in {"rejected", "ignored"}, result
    assert _decision(result).get("decision_type") == "research_ethics_review"


# ---------------------------------------------------------------------------
# Test: Tenant isolation — different tenants get independent decisions
# ---------------------------------------------------------------------------

def test_tenant_isolation_case_resolution() -> None:
    """Decisions for different tenants are independent."""
    svc = BrainCoreService()
    r1 = svc.process_signal(_case_resolution_signal(tenant_id=10, case_id="CASE-T10"))
    r2 = svc.process_signal(_case_resolution_signal(tenant_id=20, case_id="CASE-T20"))
    d1 = _decision(r1)
    d2 = _decision(r2)
    assert r1["status"] not in {"rejected", "ignored"}, r1
    assert r2["status"] not in {"rejected", "ignored"}, r2
    assert d1.get("decision_type") == "integrity_case_resolution"
    assert d2.get("decision_type") == "integrity_case_resolution"
    # Tenant IDs are preserved in the decision output
    assert int(d1.get("tenant_id", 0)) == 10
    assert int(d2.get("tenant_id", 0)) == 20


# ---------------------------------------------------------------------------
# Test: open_review_case action is always present at every severity level
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("risk_level,days_open,expected_priority", [
    ("critical", None, "critical"),
    ("high", None, "high"),
    ("medium", None, "medium"),
    ("low", None, "low"),
    (None, 30, "critical"),
    (None, 14, "high"),
])
def test_open_review_case_action_present_at_all_levels(
    risk_level: str | None, days_open: int | None, expected_priority: str
) -> None:
    """open_review_case is always in recommended_actions regardless of severity."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(
        risk_level=risk_level,
        days_open=days_open,
    ))
    decision = _decision(result)
    assert result["status"] not in {"rejected", "ignored"}, result
    assert decision.get("priority") == expected_priority
    assert "open_review_case" in (decision.get("recommended_actions") or [])


# ---------------------------------------------------------------------------
# Test: mark_ready_for_human_decision present for critical/high
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("risk_level", ["critical", "high"])
def test_mark_ready_for_human_decision_present_for_high_critical(risk_level: str) -> None:
    """mark_ready_for_human_decision action must be present for high/critical cases."""
    svc = BrainCoreService()
    result = svc.process_signal(_case_resolution_signal(risk_level=risk_level))
    assert result["status"] not in {"rejected", "ignored"}, result
    assert "mark_ready_for_human_decision" in (_decision(result).get("recommended_actions") or [])
