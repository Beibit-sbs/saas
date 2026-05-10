from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.brain_core.kpi_signal_candidates import (
    ALLOWED_ACTION_TYPES,
    ALLOWED_CONFIDENCE_LEVELS,
    ALLOWED_SEVERITIES,
    ALLOWED_SIGNAL_TYPES,
    FORBIDDEN_ACTIONS,
    build_brain_signal_candidate,
    classify_signal_confidence,
    classify_signal_severity,
    classify_signal_type_for_domain,
    map_rector_kpi_drilldown_to_brain_signal_candidates,
    validate_brain_signal_tenant,
)
from app.modules.brain_core.schemas import BrainSignalCandidateSummarySchema
from app.modules.auth.token_service import create_access_token
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
from app.modules.tenants import service as module_tenant_service


def _create_tenant(name_prefix: str) -> int:
    slug = f"{name_prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{name_prefix} Tenant"})
    return int(tenant["id"])


def _emit_analytics_event(*, tenant_id: int, event_type: str, event_id: int) -> None:
    event = OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id=str(event_id),
        payload_json={"id": event_id},
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )
    with UnitOfWork() as uow:
        AnalyticsEventHandler().handle(event, uow=uow)


def test_a0261_module_imports_successfully() -> None:
    import importlib

    importlib.import_module("app.modules.brain_core.kpi_signal_candidates")
    importlib.import_module("app.modules.brain_core.schemas")


@pytest.mark.parametrize("bad_tenant_id", [0, -1, -99])
def test_a0261_validate_brain_signal_tenant_fail_closed(bad_tenant_id: int) -> None:
    with pytest.raises(ValueError):
        validate_brain_signal_tenant(bad_tenant_id)


@pytest.mark.parametrize("domain_key,signal_type", sorted({
    "academic-governance": "quality",
    "finance-procurement-assets": "cost",
    "campus-operations": "readiness",
    "security-visitor-operations": "risk",
    "room-allocation-scheduling-intelligence": "readiness",
    "brain-review-required": "compliance",
    "student-risk-interventions": "risk",
    "research-accreditation-quality": "gap",
}.items()))
def test_a0261_signal_type_mapping_is_deterministic(domain_key: str, signal_type: str) -> None:
    assert classify_signal_type_for_domain(domain_key) == signal_type


@pytest.mark.parametrize(
    "drilldown,available_count,total_count,expected_severity,expected_confidence",
    [
        ({"risk_level": "unavailable", "review_required": False}, 0, 4, "info", "unknown"),
        ({"risk_level": "low", "review_required": False}, 1, 4, "watch", "low"),
        ({"risk_level": "medium", "review_required": True}, 4, 4, "review_required", "high"),
        ({"risk_level": "high", "review_required": True}, 4, 4, "high", "high"),
        ({"risk_level": "critical", "review_required": True}, 4, 4, "critical", "high"),
    ],
)
def test_a0261_signal_severity_and_confidence_rules(
    drilldown: dict[str, object],
    available_count: int,
    total_count: int,
    expected_severity: str,
    expected_confidence: str,
) -> None:
    severity = classify_signal_severity(drilldown=drilldown, available_count=available_count, total_count=total_count)
    confidence = classify_signal_confidence(
        available_count=available_count,
        total_count=total_count,
        severity=severity,
    )
    assert severity == expected_severity
    assert confidence == expected_confidence


@pytest.mark.parametrize(
    "drilldown",
    [
        {
            "domain_id": "academic-governance",
            "evidence_summary": "evidence available",
            "risk_level": "high",
            "review_required": True,
            "source_metrics": ["total_students", "total_enrollments"],
            "evidence_sources": [
                {
                    "metric_key": "total_students",
                    "label": "Total Students",
                    "value_label": "12",
                    "source_domain": "academic",
                    "interpretation": "Evidence supports visibility of this KPI/risk/alert.",
                    "available": True,
                    "lineage": {},
                },
                {
                    "metric_key": "total_enrollments",
                    "label": "Total Enrollments",
                    "value_label": "3",
                    "source_domain": "academic",
                    "interpretation": "Evidence supports visibility of this KPI/risk/alert.",
                    "available": True,
                    "lineage": {},
                },
            ],
        },
        {
            "domain_id": "brain-review-required",
            "evidence_summary": "Evidence unavailable in current tenant snapshot.",
            "risk_level": "unavailable",
            "review_required": False,
            "source_metrics": ["faculty_workload_overload_count"],
            "evidence_sources": [],
        },
    ],
)
def test_a0261_build_brain_signal_candidate_contract(drilldown: dict[str, object]) -> None:
    candidate = build_brain_signal_candidate(tenant_id=7, drilldown=drilldown)

    assert candidate["tenant_id"] == 7
    assert candidate["signal_id"].startswith("brain-signal-candidate-")
    assert candidate["signal_type"] in ALLOWED_SIGNAL_TYPES
    assert candidate["severity"] in ALLOWED_SEVERITIES
    assert candidate["confidence_level"] in ALLOWED_CONFIDENCE_LEVELS
    assert candidate["allowed_action_type"] in ALLOWED_ACTION_TYPES
    assert candidate["forbidden_actions"] == list(FORBIDDEN_ACTIONS)
    assert candidate["no_autonomous_execution"] is True
    assert candidate["no_policy_enforcement"] is True
    assert candidate["no_remediation_action"] is True
    assert candidate["no_fake_signal"] is True
    assert candidate["generated_from_evidence"] is True
    assert candidate["read_only"] is True
    assert candidate["tenant_scoped"] is True
    assert candidate["evidence_refs"]
    assert candidate["rationale"]

    if candidate["severity"] in {"review_required", "high", "critical"}:
        assert candidate["human_approval_required"] is True
        assert candidate["allowed_action_type"] == "human_review_queue"
    else:
        assert candidate["human_approval_required"] is False


def test_a0261_low_or_missing_evidence_does_not_fake_high_confidence() -> None:
    candidate = build_brain_signal_candidate(
        tenant_id=7,
        drilldown={
            "domain_id": "research_output",
            "evidence_summary": "Evidence unavailable in current tenant snapshot.",
            "risk_level": "unavailable",
            "review_required": False,
            "source_metrics": ["research_publications_count"],
            "evidence_sources": [],
        },
    )

    assert candidate["confidence_level"] in {"low", "unknown"}
    assert candidate["severity"] == "info"
    assert candidate["human_approval_required"] is False


def test_a0261_signal_summary_is_deterministic(reset_shared_state) -> None:
    tenant_id = _create_tenant("brain-signal-summary")
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=8001)
    _emit_analytics_event(tenant_id=tenant_id, event_type="enrollment.created", event_id=8002)
    _emit_analytics_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=8003)

    with UnitOfWork() as uow:
        summary_one = map_rector_kpi_drilldown_to_brain_signal_candidates(tenant_id=tenant_id, uow=uow)
        summary_two = map_rector_kpi_drilldown_to_brain_signal_candidates(tenant_id=tenant_id, uow=uow)

    assert summary_one == summary_two
    validated = BrainSignalCandidateSummarySchema.model_validate(summary_one)
    assert validated.tenant_id == tenant_id
    assert validated.source == "rector_kpi_drilldown"
    assert validated.total_signals == 8
    assert validated.generated_from_existing_drilldowns is True
    assert validated.generated_from_evidence is True
    assert validated.read_only is True
    assert validated.tenant_scoped is True
    assert validated.no_autonomous_action is True
    assert validated.no_policy_enforcement is True
    assert validated.no_remediation_action is True
    assert validated.no_fake_signal is True
    assert validated.no_fake_kpi is True
    assert validated.no_fake_event is True
    assert validated.source_domains == sorted(validated.source_domains)
    assert validated.source_domains == [
        "academic-governance",
        "brain-review-required",
        "campus-operations",
        "finance-procurement-assets",
        "research-accreditation-quality",
        "room-allocation-scheduling-intelligence",
        "security-visitor-operations",
        "student-risk-interventions",
    ]

    signal_ids = {signal["signal_id"] for signal in summary_one["signals"]}
    assert len(signal_ids) == 8
    assert all(signal["signal_id"].startswith("brain-signal-candidate-") for signal in summary_one["signals"])
    assert all(signal["source_domain"] in {
        "academic-governance",
        "student-risk-interventions",
        "research-accreditation-quality",
        "finance-procurement-assets",
        "brain-review-required",
        "campus-operations",
        "security-visitor-operations",
        "room-allocation-scheduling-intelligence",
    } for signal in summary_one["signals"])

    for signal in summary_one["signals"]:
        assert signal["confidence_level"] in ALLOWED_CONFIDENCE_LEVELS
        assert signal["severity"] in ALLOWED_SEVERITIES
        assert signal["allowed_action_type"] in ALLOWED_ACTION_TYPES
        assert signal["forbidden_actions"] == list(FORBIDDEN_ACTIONS)
        assert signal["read_only"] is True
        assert signal["tenant_scoped"] is True
        assert signal["no_autonomous_execution"] is True
        assert signal["no_policy_enforcement"] is True
        assert signal["no_remediation_action"] is True
        assert signal["no_fake_signal"] is True
        assert signal["generated_from_evidence"] is True
        assert signal["evidence_refs"]
        assert signal["kpi_refs"]
        if signal["severity"] in {"review_required", "high", "critical"}:
            assert signal["human_approval_required"] is True
            assert signal["allowed_action_type"] == "human_review_queue"
        else:
            assert signal["human_approval_required"] is False

    assert summary_one["review_required_count"] == sum(
        1 for signal in summary_one["signals"] if signal["severity"] in {"review_required", "high", "critical"}
    )
    assert summary_one["high_priority_count"] == sum(
        1 for signal in summary_one["signals"] if signal["severity"] in {"high", "critical"}
    )


def test_a0261_summary_uses_rector_drilldown_as_source_of_truth(reset_shared_state) -> None:
    tenant_id = _create_tenant("brain-signal-source")
    _emit_analytics_event(tenant_id=tenant_id, event_type="student.created", event_id=8101)

    with UnitOfWork() as uow:
        rector_drilldown = kpi_service.get_rector_kpi_drilldown(tenant_id=tenant_id, uow=uow)
        summary = map_rector_kpi_drilldown_to_brain_signal_candidates(tenant_id=tenant_id, uow=uow)

    assert rector_drilldown["tenant_id"] == tenant_id
    assert summary["source"] == "rector_kpi_drilldown"
    assert summary["generated_from_existing_drilldowns"] is True
    assert len(summary["signals"]) == len(rector_drilldown["domains"])
    assert {signal["source_domain"] for signal in summary["signals"]} == {domain["domain_id"] for domain in rector_drilldown["domains"]}
    assert all(signal["evidence_refs"] for signal in summary["signals"])
