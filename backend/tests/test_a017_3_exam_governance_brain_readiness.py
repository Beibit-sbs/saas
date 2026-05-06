"""A-017.3 — exam_governance brain-readiness alignment tests.

Ensures exam governance risk signals flow into the existing exam integrity
Brain path (no new engine/scenario), with tenant-safe fail-closed behavior and
Wave 4 KPI/event contract alignment.
"""

from __future__ import annotations

from contextlib import ExitStack
from uuid import uuid4

import pytest

from app.modules.brain_core.service import BrainCoreService
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.kpi import service as kpi_service


@pytest.fixture(autouse=True)
def _stub_context_sources() -> None:
    """Keep tests deterministic and independent from optional DB context sources."""
    from unittest.mock import patch

    with ExitStack() as p:
        p.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_academic_context",
                return_value={"student_profile": None, "academic_health_snapshot": {}},
            )
        )
        p.enter_context(
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
        p.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_faculty_context",
                return_value={"faculty_health_snapshot": {}},
            )
        )
        p.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_finance_context",
                return_value={"billing_health_snapshot": {}, "procurement_health_snapshot": {}},
            )
        )
        p.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_operations_context",
                return_value={"operations_health_snapshot": {}},
            )
        )
        p.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_platform_context",
                return_value={"platform_health_snapshot": {}},
            )
        )
        p.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_scheduling_context",
                return_value={"scheduling_health_snapshot": {}},
            )
        )
        yield


def _exam_governance_signal(
    *,
    tenant_id: int = 1,
    student_id: str = "STU-EXG-1",
    exam_id: str = "EXAM-GOV-1",
    risk_level: str = "high",
    violation_type: str = "proctoring_risk",
) -> dict:
    return {
        "signal_id": f"a0173-{tenant_id}-{exam_id}-{uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-a0173-{tenant_id}-{exam_id}",
        "event_type": "exam.violation_detected",
        "source_entity_type": "exam_governance",
        "source_entity_id": exam_id,
        "payload": {
            "student_id": student_id,
            "exam_id": exam_id,
            "risk_level": risk_level,
            "violation_type": violation_type,
            "source_module": "exam_governance",
        },
        "metadata": {},
    }


def test_a017_3_exam_governance_event_routes_to_existing_exam_integrity_path() -> None:
    service = BrainCoreService()
    result = service.process_signal(_exam_governance_signal())

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "exam_integrity_review"


def test_a017_3_exam_governance_high_risk_requires_human_approval() -> None:
    service = BrainCoreService()
    result = service.process_signal(_exam_governance_signal(risk_level="high"))

    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "exam_integrity_review"
    assert result["decision"]["requires_approval"] is True
    assert result["decision"]["priority"] in {"high", "critical"}


def test_a017_3_exam_governance_has_no_automatic_punitive_actions() -> None:
    service = BrainCoreService()
    result = service.process_signal(_exam_governance_signal(risk_level="high"))

    assert result["status"] == "processed"
    actions = [str(x).lower() for x in result["decision"].get("recommended_actions", [])]
    forbidden_tokens = ("grade", "fail", "suspend", "expel", "sanction", "penalt")
    assert all(not any(token in action for token in forbidden_tokens) for action in actions)


def test_a017_3_exam_governance_missing_tenant_fails_closed() -> None:
    service = BrainCoreService()
    signal = _exam_governance_signal()
    signal["tenant_id"] = 0

    result = service.process_signal(signal)

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_tenant_context"


def test_a017_3_exam_governance_tenant_context_is_preserved_in_decision() -> None:
    service = BrainCoreService()
    signal = _exam_governance_signal(tenant_id=77, exam_id="EXAM-GOV-77", student_id="STU-77")

    result = service.process_signal(signal)

    assert result["status"] == "processed"
    assert int(result["decision"]["tenant_id"]) == 77


def test_a017_3_exam_governance_event_is_allowed_in_ingestion_types() -> None:
    assert "exam.violation_detected" in VALID_EVENT_TYPES


def test_a017_3_exam_governance_event_is_mapped_in_kpi_lineage() -> None:
    assert "exam.violation_detected" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["exam_proctoring_violations_count"]
    assert "exam.violation_detected" in kpi_service.EVENT_DERIVED_METRIC_LINEAGE["exam_integrity_requires_approval_count"]


def test_a017_3_exam_governance_lineage_preserves_existing_exam_proctoring_sources() -> None:
    violations_sources = set(kpi_service.EVENT_DERIVED_METRIC_LINEAGE["exam_proctoring_violations_count"])
    approval_sources = set(kpi_service.EVENT_DERIVED_METRIC_LINEAGE["exam_integrity_requires_approval_count"])

    assert "exam.violation_detected" in violations_sources
    assert "exam.proctoring.violation_detected" in violations_sources
    assert "faculty.proctoring.violation_detected" in violations_sources

    assert "exam.violation_detected" in approval_sources
    assert "exam.proctoring.violation_detected" in approval_sources
