from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.research_science import schemas, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_create_project_enforces_safety_defaults() -> None:
    db = _db()
    created = SimpleNamespace(id=1, status="DRAFT", human_review_required=True, autonomous_decision=False, provider_integration_enabled=False)
    request = schemas.ResearchProjectCreateRequest(project_ref="RP-1", title="Cancer Biology", source_capability_id="RS-101", source_matrix_row_id="RS-101", limitations=[])
    with (
        patch("app.modules.research_science.service.repository.create_research_project", return_value=created) as mock_create,
        patch("app.modules.research_science.service.repository.create_research_audit_event"),
        patch("app.modules.research_science.service.repository.create_status_history"),
    ):
        result = service.create_research_project_service(db, 1, "actor-1", request)
    assert result is created
    kwargs = mock_create.call_args.kwargs
    assert kwargs["human_review_required"] is True
    assert kwargs["autonomous_decision"] is False
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["external_database_sync_enabled"] is False
    assert kwargs["official_verification_enabled"] is False
    assert kwargs["hidden_score_present"] is False


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "1", "bad"])  # type: ignore[list-item]
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    db = _db()
    request = SimpleNamespace(project_ref="RP-1", title="Cancer Biology", source_capability_id="RS-101", source_matrix_row_id="RS-101", limitations=[])
    with pytest.raises(TenantRequiredError):
        service.create_research_project_service(db, tenant_id, "actor-1", request)  # type: ignore[arg-type]


def test_empty_actor_fails_closed() -> None:
    db = _db()
    request = SimpleNamespace(project_ref="RP-1", title="Cancer Biology", source_capability_id="RS-101", source_matrix_row_id="RS-101", limitations=[])
    with pytest.raises(DomainValidationError):
        service.create_research_project_service(db, 1, "", request)


def test_update_project_keeps_runtime_safety_false() -> None:
    db = _db()
    current = SimpleNamespace(id=7, status="DRAFT")
    updated = SimpleNamespace(id=7, status="ACTIVE", human_review_required=True)
    with (
        patch("app.modules.research_science.service.get_research_project_service", return_value=current),
        patch("app.modules.research_science.service.repository.update_research_project", return_value=updated) as mock_update,
        patch("app.modules.research_science.service.repository.create_research_audit_event"),
    ):
        result = service.update_research_project_service(db, 1, "actor-2", 7, schemas.ResearchProjectUpdateRequest(title="Updated", limitations=[]))
    assert result is updated
    kwargs = mock_update.call_args.kwargs
    assert kwargs["autonomous_decision"] is False
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["external_database_sync_enabled"] is False
    assert kwargs["official_verification_enabled"] is False
    assert kwargs["hidden_score_present"] is False


def test_dashboard_contract_is_metadata_only() -> None:
    db = _db()
    with (
        patch("app.modules.research_science.service.repository.compute_research_dashboard_summary", return_value={
            "projects_summary": {"ACTIVE": 1},
            "student_research_summary": {"IN_PROGRESS": 2},
            "supervision_summary": {"ACTIVE": 1},
            "publications_summary": {"SUBMITTED_FOR_REVIEW": 1},
            "conferences_summary": {"SUBMITTED": 1},
            "grants_summary": {"INTERNAL_REVIEW": 1},
            "ethics_summary": {"IN_COMMITTEE_REVIEW": 1},
            "evidence_summary": {"METADATA_ONLY": 4},
            "bridge_summary": {"ACADEMIC_OPERATIONS": 1},
        }),
        patch("app.modules.research_science.service.repository.get_research_bridge_summary", return_value={"ACADEMIC_OPERATIONS": 1}),
        patch("app.modules.research_science.service.repository.create_dashboard_snapshot"),
        patch("app.modules.research_science.service.repository.create_research_audit_event"),
    ):
        result = service.get_research_dashboard_service(db, 1)
    assert result.fake_metrics is False
    assert result.data_source == "computed_from_research_science_metadata"
    assert result.master_matrix_commit == "c79cc31"
    assert result.master_matrix_rows == 467
    assert result.incomplete_data is False


def test_attach_evidence_service_is_metadata_only() -> None:
    db = _db()
    request = schemas.ResearchEvidenceCreateRequest(source_entity_type="publication_metadata", source_entity_id=7, evidence_type="file_note", title="Accepted manuscript", metadata={}, source_capability_id="RS-401", source_matrix_row_id="RS-401", limitations=[])
    attached = SimpleNamespace(id=1, status="DRAFT")
    with (
        patch("app.modules.research_science.service.repository.attach_research_evidence", return_value=attached) as mock_attach,
        patch("app.modules.research_science.service.repository.create_research_audit_event"),
    ):
        result = service.attach_research_evidence_service(db, 1, "actor-1", request)
    assert result is attached
    kwargs = mock_attach.call_args.kwargs
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["official_verification_enabled"] is False
    assert kwargs["provider_verified"] is False
    assert kwargs["fake_evidence"] is False


def test_health_contract_is_fail_closed() -> None:
    db = _db()
    with patch("app.modules.research_science.service.repository.get_research_health_summary", return_value={"tenant_id": 1, "total_records": 0, "bridge_records": 0}):
        result = service.get_research_health_service(db, 1)
    assert result.provider_integration_enabled is False
    assert result.external_database_sync_enabled is False
    assert result.official_verification_enabled is False
    assert result.hidden_score_present is False
    assert result.fake_metrics is False
    assert result.route_count == 43
    assert result.table_count == 15