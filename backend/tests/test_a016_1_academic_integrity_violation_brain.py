"""A-016.1 — Academic Integrity Violation Detection Brain tests.

Validates deterministic severity classification, Brain Core signal routing,
tenant isolation, fail-closed behavior, no-punitive-action guarantee, and
idempotent deduplication for all 6 new academic integrity violation events.
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import pytest

from app.modules.brain_core.registry import SignalRegistry
from app.modules.brain_core.service import BrainCoreService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------

def _plagiarism_signal(
    *,
    tenant_id: int,
    student_id: str = "STU-001",
    submission_id: str = "SUB-001",
    similarity_score: float | None = 80.0,
    risk_level: str = "high",
) -> dict:
    return {
        "signal_id": f"sig-plag-{tenant_id}-{submission_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-plag-{tenant_id}-{submission_id}",
        "event_type": "plagiarism.similarity.high_detected",
        "source_entity_type": "submission",
        "source_entity_id": submission_id,
        "payload": {
            "student_id": student_id,
            "course_id": "CRS-001",
            "submission_id": submission_id,
            "similarity_score": similarity_score,
            "risk_level": risk_level,
            "risk_source": "plagiarism.similarity.high_detected",
            "evidence": {"checker": "internal", "run_id": "run-001"},
        },
        "metadata": {},
    }


def _integrity_violation_signal(
    *,
    tenant_id: int,
    student_id: str = "STU-002",
    exam_id: str = "EXAM-001",
    confirmed: bool = False,
    repeated: bool = False,
) -> dict:
    return {
        "signal_id": f"sig-int-{tenant_id}-{exam_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-int-{tenant_id}-{exam_id}",
        "event_type": "academic_integrity.violation.detected",
        "source_entity_type": "exam",
        "source_entity_id": exam_id,
        "payload": {
            "student_id": student_id,
            "course_id": "CRS-002",
            "exam_id": exam_id,
            "confirmed_violation": confirmed,
            "repeated_incident": repeated,
            "risk_source": "academic_integrity.violation.detected",
            "evidence": {"report_id": "rpt-001"},
        },
        "metadata": {},
    }


def _proctoring_signal(
    *,
    tenant_id: int,
    student_id: str = "STU-003",
    exam_id: str = "EXAM-002",
    proctoring_flags: list | None = None,
) -> dict:
    if proctoring_flags is None:
        proctoring_flags = ["gaze_away"]
    return {
        "signal_id": f"sig-proc-{tenant_id}-{exam_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-proc-{tenant_id}-{exam_id}",
        "event_type": "exam.proctoring.violation_detected",
        "source_entity_type": "exam",
        "source_entity_id": exam_id,
        "payload": {
            "student_id": student_id,
            "course_id": "CRS-003",
            "exam_id": exam_id,
            "proctoring_flags": proctoring_flags,
            "risk_source": "exam.proctoring.violation_detected",
        },
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# Task 4/5 — Registry / signal support tests
# ---------------------------------------------------------------------------

def test_all_integrity_violation_event_types_are_registered() -> None:
    """All 6 A-016.1 event types must be in SignalRegistry."""
    expected = {
        "academic_integrity.violation.detected",
        "academic_integrity.risk_detected",
        "plagiarism.similarity.high_detected",
        "exam.proctoring.violation_detected",
        "coursework.submission.suspicious_detected",
        "ai_plagiarism.risk_detected",
    }
    for et in expected:
        assert SignalRegistry.is_supported(et), f"{et} not in SignalRegistry"
        assert SignalRegistry.signals[et]["scenario"] == "academic_integrity_violation"


# ---------------------------------------------------------------------------
# Task 5.1 — Plagiarism high-similarity signal routes through Brain Core
# ---------------------------------------------------------------------------

def test_plagiarism_high_similarity_signal_is_processed() -> None:
    service = BrainCoreService()
    result = service.process_signal(_plagiarism_signal(tenant_id=301, similarity_score=80.0))
    assert result["status"] == "processed"


# ---------------------------------------------------------------------------
# Task 5.2 — Brain decision is created with decision_type="academic_integrity_review"
# ---------------------------------------------------------------------------

def test_brain_decision_type_is_academic_integrity_review() -> None:
    service = BrainCoreService()
    result = service.process_signal(_plagiarism_signal(tenant_id=302, similarity_score=80.0))
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "academic_integrity_review"


# ---------------------------------------------------------------------------
# Task 5.3 — similarity_score >= 90 produces critical risk
# ---------------------------------------------------------------------------

def test_similarity_score_90_produces_critical_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(_plagiarism_signal(tenant_id=303, similarity_score=92.0))
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "critical"


def test_similarity_score_as_ratio_090_produces_critical_risk() -> None:
    """similarity_score passed as 0.0-1.0 ratio must be normalized correctly."""
    service = BrainCoreService()
    result = service.process_signal(_plagiarism_signal(tenant_id=304, similarity_score=0.91))
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "critical"


# ---------------------------------------------------------------------------
# Task 5.4 — similarity_score >= 75 produces high risk
# ---------------------------------------------------------------------------

def test_similarity_score_75_produces_high_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _plagiarism_signal(tenant_id=305, submission_id="SUB-075", similarity_score=78.0)
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "high"


# ---------------------------------------------------------------------------
# Task 5.5 — proctoring violation signal maps to integrity review decision
# ---------------------------------------------------------------------------

def test_proctoring_violation_maps_to_integrity_review() -> None:
    service = BrainCoreService()
    result = service.process_signal(_proctoring_signal(tenant_id=306, proctoring_flags=["gaze_away", "phone_detected"]))
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "academic_integrity_review"


# ---------------------------------------------------------------------------
# Task 5.6 — missing optional context does not crash
# ---------------------------------------------------------------------------

def test_missing_optional_context_does_not_crash() -> None:
    service = BrainCoreService()
    signal = {
        "signal_id": "sig-minimal-701",
        "tenant_id": 307,
        "correlation_id": "corr-minimal-701",
        "event_type": "plagiarism.similarity.high_detected",
        "source_entity_type": "submission",
        "source_entity_id": "SUB-MIN-001",
        "payload": {
            "student_id": "STU-MIN-001",
            # No similarity_score, no proctoring_flags, no course_id
        },
        "metadata": {},
    }
    result = service.process_signal(signal)
    # Should process (no score = low risk), not raise
    assert result["status"] in {"processed", "ignored", "deduplicated"}


# ---------------------------------------------------------------------------
# Task 5.7 — missing tenant_id fails closed
# ---------------------------------------------------------------------------

def test_missing_tenant_id_fails_closed() -> None:
    service = BrainCoreService()
    signal = _plagiarism_signal(tenant_id=0, similarity_score=85.0)
    signal["tenant_id"] = None
    result = service.process_signal(signal)
    assert result["status"] == "rejected"
    assert result["reason"] == "missing_tenant_context"


def test_zero_tenant_id_fails_closed() -> None:
    service = BrainCoreService()
    signal = _plagiarism_signal(tenant_id=0, similarity_score=85.0)
    result = service.process_signal(signal)
    assert result["status"] == "rejected"


# ---------------------------------------------------------------------------
# Task 5.8 — cross-tenant leakage is impossible
# ---------------------------------------------------------------------------

def test_cross_tenant_isolation() -> None:
    service = BrainCoreService()

    result_a = service.process_signal(
        _plagiarism_signal(tenant_id=401, student_id="STU-A", submission_id="SUB-X", similarity_score=80.0)
    )
    result_b = service.process_signal(
        _plagiarism_signal(tenant_id=402, student_id="STU-B", submission_id="SUB-X", similarity_score=80.0)
    )

    assert result_a["status"] == "processed"
    assert result_b["status"] == "processed"

    decisions_a = service.list_decisions(tenant_id=401)
    decisions_b = service.list_decisions(tenant_id=402)

    assert len(decisions_a) == 1
    assert len(decisions_b) == 1
    assert decisions_a[0]["decision_id"] != decisions_b[0]["decision_id"]
    # Tenant A decisions must not appear for Tenant B
    for d in decisions_b:
        assert int(d["tenant_id"]) == 402


# ---------------------------------------------------------------------------
# Task 5.9 — duplicate integrity signal is deduplicated
# ---------------------------------------------------------------------------

def test_duplicate_integrity_signal_is_deduplicated() -> None:
    service = BrainCoreService()

    first = service.process_signal(
        _plagiarism_signal(tenant_id=501, submission_id="SUB-DEDUP", similarity_score=80.0)
    )
    second = service.process_signal(
        _plagiarism_signal(tenant_id=501, submission_id="SUB-DEDUP", similarity_score=80.0)
    )

    assert first["status"] == "processed"
    assert second["status"] == "deduplicated"
    assert second["reason"] == "duplicate_signal_within_window"


# ---------------------------------------------------------------------------
# Task 5.10 — no automatic punitive action is taken
# ---------------------------------------------------------------------------

def test_no_automatic_punitive_action_in_critical_decision() -> None:
    """Critical integrity decision must not include punitive academic status changes."""
    service = BrainCoreService()
    result = service.process_signal(_integrity_violation_signal(tenant_id=601, confirmed=True))
    assert result["status"] == "processed"

    action_names = {item["name"] for item in result["action_plan"]}
    punitive_actions = {
        "suspend_student",
        "expel_student",
        "change_academic_status",
        "apply_grade_penalty",
        "revoke_enrollment",
        "mark_cheating_in_transcript",
        "fail_course_automatically",
    }
    overlap = action_names & punitive_actions
    assert not overlap, f"Punitive actions found in action plan: {overlap}"


def test_no_automatic_punitive_action_in_high_decision() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _plagiarism_signal(tenant_id=602, submission_id="SUB-HIGH-NOPU", similarity_score=78.0)
    )
    assert result["status"] == "processed"

    action_names = {item["name"] for item in result["action_plan"]}
    punitive_actions = {"suspend_student", "expel_student", "apply_grade_penalty"}
    assert not (action_names & punitive_actions)


# ---------------------------------------------------------------------------
# Additional coverage: confirmed violation → critical
# ---------------------------------------------------------------------------

def test_confirmed_violation_produces_critical_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(_integrity_violation_signal(tenant_id=701, confirmed=True))
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "critical"


def test_repeated_incident_produces_critical_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _integrity_violation_signal(tenant_id=702, exam_id="EXAM-RPT", repeated=True)
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "critical"


def test_three_proctoring_flags_produces_critical_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _proctoring_signal(
            tenant_id=703,
            exam_id="EXAM-3FLAGS",
            proctoring_flags=["gaze_away", "phone_detected", "multiple_faces"],
        )
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "critical"


def test_single_proctoring_flag_produces_medium_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _proctoring_signal(tenant_id=704, exam_id="EXAM-1FLAG", proctoring_flags=["gaze_away"])
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "medium"


def test_similarity_score_50_produces_medium_risk() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _plagiarism_signal(tenant_id=705, submission_id="SUB-50", similarity_score=55.0, risk_level="medium")
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "medium"


def test_ai_plagiarism_risk_detected_routes_correctly() -> None:
    service = BrainCoreService()
    signal = {
        "signal_id": "sig-aip-901",
        "tenant_id": 801,
        "correlation_id": "corr-aip-901",
        "event_type": "ai_plagiarism.risk_detected",
        "source_entity_type": "submission",
        "source_entity_id": "SUB-AIP-001",
        "payload": {
            "student_id": "STU-AIP-001",
            "course_id": "CRS-AIP",
            "submission_id": "SUB-AIP-001",
            "similarity_score": 82.0,
            "risk_level": "high",
        },
        "metadata": {},
    }
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "academic_integrity_review"
    assert result["decision"]["priority"] in {"high", "critical"}


def test_coursework_suspicious_signal_routes_correctly() -> None:
    service = BrainCoreService()
    signal = {
        "signal_id": "sig-cs-901",
        "tenant_id": 802,
        "correlation_id": "corr-cs-901",
        "event_type": "coursework.submission.suspicious_detected",
        "source_entity_type": "submission",
        "source_entity_id": "SUB-SUS-001",
        "payload": {
            "student_id": "STU-SUS-001",
            "course_id": "CRS-SUS",
            "submission_id": "SUB-SUS-001",
            "risk_level": "medium",
        },
        "metadata": {},
    }
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "academic_integrity_review"


# ---------------------------------------------------------------------------
# Task 5.11 — existing academic integrity escalation tests remain unbroken
# ---------------------------------------------------------------------------

def test_existing_integrity_escalation_still_works() -> None:
    """The old academic_integrity.case.escalated path must remain functional."""
    service = BrainCoreService()
    signal = {
        "signal_id": "sig-old-esc-001",
        "tenant_id": 901,
        "correlation_id": "corr-old-esc-001",
        "event_type": "academic_integrity.case.escalated",
        "source_entity_type": "integrity_case",
        "source_entity_id": "CASE-001",
        "payload": {
            "case_id": "CASE-001",
            "student_id": "STU-ESC-001",
            "case_type": "plagiarism",
        },
        "metadata": {},
    }
    result = service.process_signal(signal)
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] in {"compliance", "academic_integrity_review"}
