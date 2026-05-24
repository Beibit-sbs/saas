from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.quality_accreditation import schemas, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_create_framework_enforces_safety_defaults() -> None:
    db = _db()
    created = SimpleNamespace(id=1, status="DRAFT", human_review_required=True, provider_integration_enabled=False)
    request = schemas.QualityRecordRequest(framework_ref="QF-1", title="Institutional QA", source_capability_id="QA-101", source_family_id="QA-F1", limitations=[])
    with (
        patch("app.modules.quality_accreditation.service.repository.create_resource", return_value=created) as mock_create,
        patch("app.modules.quality_accreditation.service.repository.create_quality_audit_event"),
        patch("app.modules.quality_accreditation.service.repository.create_quality_status_history"),
    ):
        result = service.create_resource_service(db, 1, "actor-1", "frameworks", request)
    assert result is created
    kwargs = mock_create.call_args.kwargs
    assert kwargs["human_review_required"] is True
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["external_database_sync_enabled"] is False
    assert kwargs["official_accreditation_approval_enabled"] is False
    assert kwargs["official_ministry_submission_enabled"] is False
    assert kwargs["official_ranking_claim_enabled"] is False
    assert kwargs["hidden_score_present"] is False


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "1", "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    db = _db()
    request = schemas.QualityRecordRequest(framework_ref="QF-1", title="Institutional QA")
    with pytest.raises(TenantRequiredError):
        service.create_resource_service(db, tenant_id, "actor-1", "frameworks", request)  # type: ignore[arg-type]


def test_empty_actor_fails_closed() -> None:
    db = _db()
    request = schemas.QualityRecordRequest(framework_ref="QF-1", title="Institutional QA")
    with pytest.raises(DomainValidationError):
        service.create_resource_service(db, 1, "", "frameworks", request)


def test_dashboard_contract_is_metadata_only() -> None:
    db = _db()
    with (
        patch("app.modules.quality_accreditation.service.repository.compute_dashboard_summary", return_value={
            "frameworks_summary": {"ACTIVE_METADATA_ONLY": 1},
            "standards_summary": {"ACTIVE_METADATA_ONLY": 2},
            "evidence_summary": {"REVIEWED_METADATA_ONLY": 4},
            "readiness_summary": {"READY_FOR_INTERNAL_REVIEW": 2},
            "self_assessment_summary": {"QA_REVIEW": 1},
            "improvement_summary": {"ACTIVE": 1},
            "audit_summary": {"IN_PROGRESS": 1},
            "program_review_summary": {"DRAFT": 1},
            "bridge_summary": {"ACADEMIC_OPERATIONS": 1},
            "brain_signal_summary": {"COMPLIANCE_ALERT": 1},
        }),
        patch("app.modules.quality_accreditation.service.repository.create_dashboard_snapshot"),
        patch("app.modules.quality_accreditation.service.repository.create_quality_audit_event"),
    ):
        result = service.get_quality_dashboard_service(db, 1)
    assert result.fake_metrics is False
    assert result.data_source == "computed_from_quality_accreditation_metadata"
    assert result.master_matrix_commit == "c79cc31"
    assert result.master_matrix_rows == 467
    assert result.incomplete_data is False


def test_health_contract_is_fail_closed() -> None:
    db = _db()
    result = service.get_quality_health_service(db, 1)
    assert result.provider_integration_enabled is False
    assert result.external_database_sync_enabled is False
    assert result.official_accreditation_approval_enabled is False
    assert result.official_ministry_submission_enabled is False
    assert result.official_ranking_claim_enabled is False
    assert result.hidden_score_present is False
    assert result.fake_metrics is False
    assert result.route_count == 70
    assert result.table_count == 32