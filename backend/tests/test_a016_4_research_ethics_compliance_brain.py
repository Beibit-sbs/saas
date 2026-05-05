"""A-016.4: Research Ethics / Compliance Review Brain.

Ensures research ethics/compliance signals route through Brain Core into the
research_ethics_compliance scenario with deterministic, explainable severity.

Safety invariants:
- no automatic approval/rejection/sanction
- high/critical requires human approval
- missing tenant fails closed
- missing source/subject identifiers fail closed
- cross-wave regressions remain green (A-016.1/2/3 paths)
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
            pytest.MonkeyPatch.context()
        )
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


def _ethics_signal(
    *,
    tenant_id: int = 1,
    event_type: str = "research_ethics.application.submitted",
    researcher_id: str = "FAC-001",
    project_id: str = "PROJ-001",
    ethics_application_id: str = "ETH-001",
    risk_level: str | None = None,
    documents_missing: list[str] | None = None,
    consent_required: bool | None = None,
    consent_present: bool | None = None,
    data_privacy_risk: bool | None = None,
    conflict_of_interest: bool | None = None,
    conflict_confirmed: bool | None = None,
    study_type: str | None = None,
    days_pending: int | None = None,
    violation_confirmed: bool | None = None,
) -> dict:
    payload: dict = {
        "researcher_id": researcher_id,
        "project_id": project_id,
        "ethics_application_id": ethics_application_id,
        "risk_category": "ethics_compliance",
        "source_entity_type": "research_ethics_review",
        "source_entity_id": ethics_application_id,
    }
    if risk_level is not None:
        payload["risk_level"] = risk_level
    if documents_missing is not None:
        payload["documents_missing"] = documents_missing
    if consent_required is not None:
        payload["consent_required"] = consent_required
    if consent_present is not None:
        payload["consent_present"] = consent_present
    if data_privacy_risk is not None:
        payload["data_privacy_risk"] = data_privacy_risk
    if conflict_of_interest is not None:
        payload["conflict_of_interest"] = conflict_of_interest
    if conflict_confirmed is not None:
        payload["conflict_confirmed"] = conflict_confirmed
    if study_type is not None:
        payload["study_type"] = study_type
    if days_pending is not None:
        payload["days_pending"] = days_pending
    if violation_confirmed is not None:
        payload["violation_confirmed"] = violation_confirmed

    return {
        "signal_id": f"ethics-{tenant_id}-{uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-ethics-{tenant_id}",
        "event_type": event_type,
        "source_entity_type": "research_ethics_review",
        "source_entity_id": ethics_application_id,
        "payload": payload,
        "metadata": {},
    }


def test_ethics_high_risk_routes_through_brain_core() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=1,
            event_type="research_ethics.high_risk.detected",
            risk_level="high",
        )
    )
    assert result["status"] == "processed"


def test_ethics_decision_type_is_research_ethics_review() -> None:
    service = BrainCoreService()
    result = service.process_signal(_ethics_signal(tenant_id=2))
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "research_ethics_review"


def test_missing_consent_human_subjects_is_critical() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=3,
            event_type="research_ethics.missing_consent.detected",
            study_type="human_subjects",
            consent_required=True,
            consent_present=False,
        )
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] == "critical"
    assert result["decision"]["requires_approval"] is True


def test_document_missing_one_is_medium() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=4,
            event_type="research_ethics.document_missing.detected",
            documents_missing=["consent_form"],
            risk_level="medium",
        )
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] in {"medium", "high"}


def test_document_missing_many_is_high_or_critical() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=5,
            event_type="research_ethics.document_missing.detected",
            documents_missing=["consent_form", "data_plan", "coi_disclosure"],
        )
    )
    assert result["status"] == "processed"
    assert result["decision"]["priority"] in {"high", "critical"}


def test_review_overdue_thresholds_high_and_critical() -> None:
    service = BrainCoreService()
    high_result = service.process_signal(
        _ethics_signal(
            tenant_id=6,
            event_type="research_ethics.review.overdue",
            days_pending=35,
        )
    )
    critical_result = service.process_signal(
        _ethics_signal(
            tenant_id=6,
            event_type="research_ethics.review.overdue",
            days_pending=75,
            ethics_application_id="ETH-006B",
        )
    )
    assert high_result["status"] == "processed"
    assert critical_result["status"] == "processed"
    assert high_result["decision"]["priority"] in {"high", "critical"}
    assert critical_result["decision"]["priority"] == "critical"


def test_conflict_of_interest_maps_to_ethics_review_decision() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=7,
            event_type="research_ethics.conflict_of_interest.detected",
            conflict_of_interest=True,
        )
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "research_ethics_review"


def test_missing_optional_context_does_not_crash_and_is_recorded() -> None:
    service = BrainCoreService()
    signal = _ethics_signal(
        tenant_id=8,
        event_type="compliance.review.required",
        risk_level="low",
    )
    signal["payload"].pop("documents_missing", None)
    signal["payload"].pop("consent_required", None)
    signal["payload"].pop("consent_present", None)
    signal["payload"].pop("data_privacy_risk", None)
    signal["payload"].pop("conflict_of_interest", None)

    result = service.process_signal(signal)
    assert result["status"] == "processed"
    normalized_payload = result["signal"]["payload"]
    assert "documents_missing_evidence" in normalized_payload
    assert "consent_required_evidence" in normalized_payload


def test_missing_tenant_fails_closed() -> None:
    service = BrainCoreService()
    result = service.process_signal(_ethics_signal(tenant_id=0))
    assert result["status"] == "rejected"
    assert "missing_tenant" in result["reason"]


def test_missing_source_identifier_fails_closed() -> None:
    service = BrainCoreService()
    signal = {
        "signal_id": "ethics-nosubject-1",
        "tenant_id": 9,
        "correlation_id": "corr-nosubject",
        "event_type": "research_ethics.application.submitted",
        "source_entity_type": "",
        "source_entity_id": "",
        "payload": {
            "risk_level": "medium",
            "source_entity_type": "",
            "source_entity_id": "",
        },
        "metadata": {},
    }
    result = service.process_signal(signal)
    assert result["status"] == "rejected"
    assert "missing_subject" in result["reason"]


def test_duplicate_signal_deduplicated() -> None:
    service = BrainCoreService()
    signal = _ethics_signal(tenant_id=10)
    signal["signal_id"] = "ethics-dup-10"

    first = service.process_signal(signal)
    second = service.process_signal(signal)

    assert first["status"] == "processed"
    assert second["status"] == "deduplicated"


def test_no_auto_approval_rejection_or_sanction() -> None:
    forbidden_actions = {
        "auto_approve_research",
        "auto_reject_research",
        "reject_research",
        "approve_research",
        "sanction_researcher",
        "suspend_research_activity",
    }
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=11,
            event_type="research_ethics.violation.reported",
            violation_confirmed=True,
            risk_level="critical",
        )
    )
    assert result["status"] == "processed"
    actions = set(result["decision"].get("recommended_actions") or [])
    assert not (actions & forbidden_actions)


def test_high_and_critical_require_approval() -> None:
    service = BrainCoreService()
    high_result = service.process_signal(
        _ethics_signal(
            tenant_id=12,
            event_type="research_ethics.high_risk.detected",
            risk_level="high",
        )
    )
    critical_result = service.process_signal(
        _ethics_signal(
            tenant_id=12,
            event_type="research_ethics.missing_consent.detected",
            study_type="human_subjects",
            consent_required=True,
            consent_present=False,
            ethics_application_id="ETH-012B",
        )
    )
    assert high_result["decision"]["priority"] == "high"
    assert high_result["decision"]["requires_approval"] is True
    assert critical_result["decision"]["priority"] == "critical"
    assert critical_result["decision"]["requires_approval"] is True


def test_a016_1_regression_academic_integrity_path() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        {
            "signal_id": "reg-a0161-ethics",
            "tenant_id": 13,
            "correlation_id": "corr-reg-a0161",
            "event_type": "academic_integrity.violation.detected",
            "source_entity_type": "submission",
            "source_entity_id": "SUB-13",
            "payload": {"student_id": "STU-13", "similarity_score": 86.0, "risk_level": "high"},
            "metadata": {},
        }
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "academic_integrity_review"


def test_a016_2_regression_thesis_governance_path() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        {
            "signal_id": "reg-a0162-ethics",
            "tenant_id": 14,
            "correlation_id": "corr-reg-a0162",
            "event_type": "thesis.supervisor.assignment_needed",
            "source_entity_type": "thesis",
            "source_entity_id": "TH-14",
            "payload": {"thesis_id": "TH-14", "student_id": "STU-14", "days_without_supervisor": 20},
            "metadata": {},
        }
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "thesis_supervisor_assignment"


def test_a016_3_regression_exam_proctoring_path() -> None:
    service = BrainCoreService()
    result = service.process_signal(
        {
            "signal_id": "reg-a0163-ethics",
            "tenant_id": 15,
            "correlation_id": "corr-reg-a0163",
            "event_type": "exam.proctoring.forbidden_app_detected",
            "source_entity_type": "exam_proctoring",
            "source_entity_id": "EX-15",
            "payload": {"student_id": "STU-15", "exam_id": "EX-15", "violation_type": "forbidden_app"},
            "metadata": {},
        }
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "exam_integrity_review"


@pytest.mark.parametrize(
    "event_type",
    [
        "research_ethics.application.submitted",
        "research_ethics.review.overdue",
        "research_ethics.high_risk.detected",
        "research_ethics.missing_consent.detected",
        "research_ethics.document_missing.detected",
        "research_ethics.conflict_of_interest.detected",
        "research_ethics.violation.reported",
        "research.compliance.risk_detected",
        "research.data_privacy.risk_detected",
        "compliance.review.required",
    ],
)
def test_all_a0164_events_registered(event_type: str) -> None:
    assert SignalRegistry.is_supported(event_type)
    assert SignalRegistry.signals[event_type]["scenario"] == "research_ethics_compliance"


@pytest.mark.parametrize(
    "event_type",
    [
        "research_ethics.application.submitted",
        "research_ethics.review.overdue",
        "research_ethics.high_risk.detected",
        "research_ethics.missing_consent.detected",
        "research_ethics.document_missing.detected",
        "research_ethics.conflict_of_interest.detected",
        "research_ethics.violation.reported",
        "research.compliance.risk_detected",
        "research.data_privacy.risk_detected",
        "compliance.review.required",
    ],
)
def test_all_a0164_events_produce_research_ethics_review_decision(event_type: str) -> None:
    service = BrainCoreService()
    result = service.process_signal(
        _ethics_signal(
            tenant_id=16,
            event_type=event_type,
            ethics_application_id=f"ETH-{event_type.split('.')[1][:4]}-{uuid4().hex[:4]}",
        )
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "research_ethics_review"
