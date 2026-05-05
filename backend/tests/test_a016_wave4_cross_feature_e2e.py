"""A-016.7 — Wave 4 Cross-Feature E2E Tests.

Validates connected governance loops for Wave 4:
1) Academic Integrity Risk -> Review Decision -> Case Resolution -> KPI
2) Exam Proctoring Violation -> Exam Integrity Review -> Case Resolution -> KPI
3) Thesis Governance Risk -> Supervisor Assignment -> KPI
4) Research Ethics Risk -> Committee Review -> KPI
5) Case Resolution Governance (no punitive automation)
6) Cross-tenant isolation

Scope constraints:
- additive validation only (no new business features)
- deterministic test data
- tenant-scoped assertions
- no external dependencies
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.modules.brain_core.service import BrainCoreService
from app.modules.tenants import service as tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service


@pytest.fixture(autouse=True)
def _stub_brain_context_sources() -> None:
    """Stub Brain Core context builders to keep E2E tests deterministic."""
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
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_scheduling_context",
                return_value={"scheduling_health_snapshot": {}},
            )
        )
        yield


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    result = tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(result["id"])


def _emit_event(*, tenant_id: int, event_type: str, payload: dict | None = None, count: int = 1) -> None:
    base_payload = payload or {"source": "test-a0167"}
    for idx in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={**base_payload, "seq": idx + 1},
        )


def _refresh_metrics(*, tenant_id: int) -> None:
    from app.platform.uow import UnitOfWork

    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _kpi_cards(*, tenant_id: int) -> dict[str, dict]:
    from app.platform.uow import UnitOfWork

    with UnitOfWork() as uow:
        result = kpi_service.get_tenant_product_kpis(tenant_id=tenant_id, uow=uow)
    return {item["key"]: item for item in result["kpis"]}


def _decision(result: dict) -> dict:
    return result.get("decision", {})


def test_wave4_academic_integrity_to_review_case_to_kpi(reset_shared_state) -> None:
    """Academic integrity risk signal flows to review + case resolution + KPI representation."""
    tenant_id = _create_tenant("a0167-ai")
    svc = BrainCoreService()

    brain_result = svc.process_signal(
        {
            "event_type": "academic_integrity.violation.detected",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "student",
            "source_entity_id": "STU-AI-001",
            "source_module": "academic_integrity",
            "payload": {
                "student_id": "STU-AI-001",
                "course_id": "CRS-AI-001",
                "violation_type": "plagiarism",
                "similarity_score": 0.88,
                "risk_category": "academic_integrity",
            },
        }
    )
    assert brain_result["status"] not in {"rejected", "ignored"}, brain_result
    assert _decision(brain_result).get("decision_type") == "academic_integrity_review"

    resolution_result = svc.process_signal(
        {
            "event_type": "academic_integrity.case.review_required",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "integrity_case",
            "source_entity_id": "CASE-AI-001",
            "source_module": "academic_integrity",
            "payload": {
                "source_decision_id": "DEC-AI-001",
                "source_decision_type": "academic_integrity_review",
                "source_scenario": "academic_integrity_violation",
                "case_id": "CASE-AI-001",
                "student_id": "STU-AI-001",
                "risk_level": "high",
            },
        }
    )
    assert resolution_result["status"] not in {"rejected", "ignored"}, resolution_result
    assert _decision(resolution_result).get("decision_type") == "integrity_case_resolution"

    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.violation.detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.opened", count=1)
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.review_required", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    cards = _kpi_cards(tenant_id=tenant_id)
    assert int(cards["academic_integrity_risk_count"]["value"]) >= 2
    assert int(cards["academic_integrity_cases_pending_review"]["value"]) >= 1
    assert int(cards["integrity_cases_open_count"]["value"]) >= 1


def test_wave4_exam_proctoring_to_integrity_review_to_kpi(reset_shared_state) -> None:
    """Exam proctoring violation flows to exam review + case resolution + exam KPI representation."""
    tenant_id = _create_tenant("a0167-exam")
    svc = BrainCoreService()

    brain_result = svc.process_signal(
        {
            "event_type": "exam.proctoring.face_mismatch_detected",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "exam",
            "source_entity_id": "EXAM-001",
            "source_module": "exam_proctoring",
            "payload": {
                "student_id": "STU-EX-001",
                "exam_id": "EXAM-001",
                "face_mismatch": True,
                "risk_level": "high",
                "risk_category": "exam_proctoring",
            },
        }
    )
    assert brain_result["status"] not in {"rejected", "ignored"}, brain_result
    assert _decision(brain_result).get("decision_type") == "exam_integrity_review"

    resolution_result = svc.process_signal(
        {
            "event_type": "integrity.resolution.workflow_needed",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "integrity_case",
            "source_entity_id": "CASE-EX-001",
            "source_module": "academic_integrity",
            "payload": {
                "source_decision_id": "DEC-EX-001",
                "source_decision_type": "exam_integrity_review",
                "source_scenario": "exam_proctoring_violation",
                "case_id": "CASE-EX-001",
                "student_id": "STU-EX-001",
                "risk_level": "high",
            },
        }
    )
    assert resolution_result["status"] not in {"rejected", "ignored"}, resolution_result
    assert _decision(resolution_result).get("decision_type") == "integrity_case_resolution"

    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.violation_detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.face_mismatch_detected", count=1)
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.review_required", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    cards = _kpi_cards(tenant_id=tenant_id)
    assert int(cards["exam_proctoring_violations_count"]["value"]) >= 2
    assert int(cards["exam_integrity_high_risk_count"]["value"]) >= 1
    assert int(cards["integrity_case_resolution_sla_risk_count"]["value"]) >= 1


def test_wave4_thesis_governance_to_supervisor_assignment_to_kpi(reset_shared_state) -> None:
    """Thesis governance risk flows to supervisor assignment decision + thesis KPI representation."""
    tenant_id = _create_tenant("a0167-thesis")
    svc = BrainCoreService()

    brain_result = svc.process_signal(
        {
            "event_type": "thesis.supervisor.assignment_needed",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "thesis",
            "source_entity_id": "THESIS-001",
            "source_module": "thesis",
            "payload": {
                "student_id": "STU-TH-001",
                "thesis_id": "THESIS-001",
                "risk_category": "thesis_governance",
                "risk_level": "high",
            },
        }
    )
    assert brain_result["status"] not in {"rejected", "ignored"}, brain_result
    assert _decision(brain_result).get("decision_type") == "thesis_supervisor_assignment"

    _emit_event(tenant_id=tenant_id, event_type="thesis.governance.risk_detected", count=1)
    _emit_event(tenant_id=tenant_id, event_type="thesis.supervisor.assignment_needed", count=1)
    _emit_event(tenant_id=tenant_id, event_type="thesis.review.delayed", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    cards = _kpi_cards(tenant_id=tenant_id)
    assert int(cards["thesis_governance_risk_count"]["value"]) >= 1
    assert int(cards["thesis_supervisor_assignment_needed_count"]["value"]) >= 1
    assert int(cards["thesis_review_delayed_count"]["value"]) >= 1


def test_wave4_research_ethics_to_committee_review_to_kpi(reset_shared_state) -> None:
    """Research ethics risk flows to ethics review decision + ethics KPI representation."""
    tenant_id = _create_tenant("a0167-ethics")
    svc = BrainCoreService()

    brain_result = svc.process_signal(
        {
            "event_type": "research_ethics.high_risk.detected",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "research_ethics_review",
            "source_entity_id": "ETH-001",
            "source_module": "research_ethics",
            "payload": {
                "researcher_id": "FAC-ETH-001",
                "project_id": "PROJ-ETH-001",
                "ethics_application_id": "ETH-001",
                "risk_level": "high",
                "risk_category": "ethics_compliance",
            },
        }
    )
    assert brain_result["status"] not in {"rejected", "ignored"}, brain_result
    assert _decision(brain_result).get("decision_type") == "research_ethics_review"

    _emit_event(tenant_id=tenant_id, event_type="research_ethics.application.submitted", count=1)
    _emit_event(tenant_id=tenant_id, event_type="research_ethics.high_risk.detected", count=1)
    _emit_event(tenant_id=tenant_id, event_type="research_ethics.document_missing.detected", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    cards = _kpi_cards(tenant_id=tenant_id)
    assert int(cards["research_ethics_review_cases_count"]["value"]) >= 1
    assert int(cards["research_ethics_high_risk_count"]["value"]) >= 1
    assert int(cards["research_ethics_missing_documents_count"]["value"]) >= 1


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


def test_wave4_case_resolution_governance_no_punitive_action(reset_shared_state) -> None:
    """Case resolution remains human-in-the-loop and never emits punitive automatic actions."""
    tenant_id = _create_tenant("a0167-resolution")
    svc = BrainCoreService()

    result = svc.process_signal(
        {
            "event_type": "integrity.resolution.workflow_needed",
            "tenant_id": tenant_id,
            "signal_id": str(uuid4()),
            "source_entity_type": "integrity_case",
            "source_entity_id": "CASE-RES-001",
            "source_module": "academic_integrity",
            "payload": {
                "source_decision_id": "DEC-RES-001",
                "source_decision_type": "research_ethics_review",
                "source_scenario": "research_ethics_compliance",
                "case_id": "CASE-RES-001",
                "student_id": "STU-RES-001",
                "risk_level": "critical",
                "days_open": 31,
                "evidence_items": [],
            },
        }
    )
    assert result["status"] not in {"rejected", "ignored"}, result
    decision = _decision(result)
    assert decision.get("decision_type") == "integrity_case_resolution"
    assert decision.get("requires_approval") is True
    actions = set(decision.get("recommended_actions") or [])
    assert not actions & PUNITIVE_ACTIONS, f"Punitive actions found: {actions & PUNITIVE_ACTIONS}"

    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.review_required", count=1)
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.evidence_requested", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    cards = _kpi_cards(tenant_id=tenant_id)
    assert int(cards["integrity_cases_evidence_requested_count"]["value"]) >= 1
    assert int(cards["integrity_case_resolution_sla_risk_count"]["value"]) >= 1


def test_wave4_cross_tenant_isolation(reset_shared_state) -> None:
    """Signals/events from tenant A must not influence tenant B Wave 4 KPI values."""
    tenant_a = _create_tenant("a0167-tenant-a")
    tenant_b = _create_tenant("a0167-tenant-b")

    _emit_event(tenant_id=tenant_a, event_type="academic_integrity.violation.detected", count=3)
    _emit_event(tenant_id=tenant_a, event_type="exam.proctoring.violation_detected", count=2)

    _emit_event(tenant_id=tenant_b, event_type="thesis.supervisor.assignment_needed", count=1)

    _refresh_metrics(tenant_id=tenant_a)
    _refresh_metrics(tenant_id=tenant_b)

    cards_a = _kpi_cards(tenant_id=tenant_a)
    cards_b = _kpi_cards(tenant_id=tenant_b)

    assert int(cards_a["academic_integrity_risk_count"]["value"]) >= 3
    assert int(cards_b["academic_integrity_risk_count"]["value"]) == 0

    assert int(cards_a["exam_proctoring_violations_count"]["value"]) >= 2
    assert int(cards_b["exam_proctoring_violations_count"]["value"]) == 0

    assert int(cards_b["thesis_supervisor_assignment_needed_count"]["value"]) >= 1
    assert int(cards_a["thesis_supervisor_assignment_needed_count"]["value"]) == 0
