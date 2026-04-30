"""Tests for RiskClassifier coverage of all 5 lifecycle signals.

Audit item #14 DoD: each of the 5 lifecycle signals (admissions, enrollment,
scheduling, academic_integrity, financial_aid) must produce a specific
situation_type from RiskClassifier — not the generic default.
"""
from __future__ import annotations

import pytest

from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier


@pytest.fixture()
def classifier() -> RiskClassifier:
    return RiskClassifier()


def _sig(event_type: str, payload: dict | None = None) -> dict:
    return {
        "event_type": event_type,
        "tenant_id": 1,
        "source_entity_type": "student",
        "source_entity_id": "stu-001",
        "payload": payload or {},
    }


# ---------------------------------------------------------------------------
# 1. admissions.decision.made
# ---------------------------------------------------------------------------

class TestAdmissionsDecisionMade:
    def test_rejected_outcome_is_high_severity(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("admissions.decision.made", {"decision_outcome": "rejected"}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "admissions_decision_high"

    def test_conditional_outcome_is_high_severity(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("admissions.decision.made", {"decision_outcome": "conditional"}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "admissions_decision_high"

    def test_high_risk_score_is_high_severity(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("admissions.decision.made", {"decision_outcome": "admitted", "risk_score": 0.85}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "admissions_decision_high"

    def test_admitted_without_risk_is_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("admissions.decision.made", {"decision_outcome": "admitted"}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "medium"
        assert result["reasoning_path"] == "admissions_decision_medium"

    def test_empty_payload_returns_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(_sig("admissions.decision.made"), {})
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "medium"

    def test_not_default_operational_risk(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(_sig("admissions.decision.made"), {})
        assert result["situation_type"] != "operational_risk"
        assert result["reasoning_path"] != "default"


# ---------------------------------------------------------------------------
# 2. enrollments.dropout_risk.detected  (already wired — regression guard)
# ---------------------------------------------------------------------------

class TestEnrollmentDropoutRisk:
    def test_withdrawn_status_is_high(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("enrollments.dropout_risk.detected", {"to_status": "withdrawn"}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "enrollment_dropout_high"

    def test_no_status_is_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(_sig("enrollments.dropout_risk.detected"), {})
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "medium"


# ---------------------------------------------------------------------------
# 3. scheduling.section.scheduled
# ---------------------------------------------------------------------------

class TestSchedulingSectionScheduled:
    def test_overload_flag_is_high(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("scheduling.section.scheduled", {"overload_flag": True}), {}
        )
        assert result["situation_type"] == "faculty_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "scheduling_overload_high"

    def test_sections_exceed_threshold_is_high(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("scheduling.section.scheduled", {
                "current_sections": 6,
                "max_sections_threshold": 4,
            }), {}
        )
        assert result["situation_type"] == "faculty_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "scheduling_overload_high"

    def test_normal_schedule_is_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("scheduling.section.scheduled", {
                "current_sections": 3,
                "max_sections_threshold": 4,
            }), {}
        )
        assert result["situation_type"] == "faculty_risk"
        assert result["severity"] == "medium"
        assert result["reasoning_path"] == "scheduling_section_scheduled_medium"

    def test_empty_payload_returns_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(_sig("scheduling.section.scheduled"), {})
        assert result["situation_type"] == "faculty_risk"
        assert result["severity"] == "medium"

    def test_not_default_operational_risk(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(_sig("scheduling.section.scheduled"), {})
        assert result["situation_type"] != "operational_risk"
        assert result["reasoning_path"] != "default"


# ---------------------------------------------------------------------------
# 4. academic_integrity.case.escalated  (already wired — regression guard)
# ---------------------------------------------------------------------------

class TestAcademicIntegrityCaseEscalated:
    def test_plagiarism_is_high(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("academic_integrity.case.escalated", {"case_type": "plagiarism"}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "academic_integrity_high"

    def test_other_case_type_is_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("academic_integrity.case.escalated", {"case_type": "other"}), {}
        )
        assert result["situation_type"] == "academic_risk"
        assert result["severity"] == "medium"


# ---------------------------------------------------------------------------
# 5. financial_aid.warning.detected  (already wired — regression guard)
# ---------------------------------------------------------------------------

class TestFinancialAidWarningDetected:
    def test_rejected_status_is_high(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("financial_aid.warning.detected", {"to_status": "rejected"}), {}
        )
        assert result["situation_type"] == "student_success_risk"
        assert result["severity"] == "high"
        assert result["reasoning_path"] == "financial_aid_warning_high"

    def test_other_status_is_medium(self, classifier: RiskClassifier) -> None:
        result = classifier.classify(
            _sig("financial_aid.warning.detected", {"to_status": "under_review"}), {}
        )
        assert result["situation_type"] == "student_success_risk"
        assert result["severity"] == "medium"
