from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.research_science import schemas, service


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "research_science"


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_update_creates_audit_event() -> None:
    db = _db()
    current = SimpleNamespace(id=10, status="DRAFT")
    updated = SimpleNamespace(id=10, status="ACTIVE", human_review_required=True)
    with (
        patch("app.modules.research_science.service.get_research_project_service", return_value=current),
        patch("app.modules.research_science.service.repository.update_research_project", return_value=updated),
        patch("app.modules.research_science.service.repository.create_research_audit_event") as mock_audit,
    ):
        result = service.update_research_project_service(db, 1, "actor-10", 10, schemas.ResearchProjectUpdateRequest(title="Updated", limitations=[]))
    assert result.status == "ACTIVE"
    assert mock_audit.called


def test_evidence_attach_uses_metadata_only() -> None:
    db = _db()
    attached = SimpleNamespace(id=1, status="DRAFT")
    request = schemas.ResearchEvidenceCreateRequest(source_entity_type="publication_metadata", source_entity_id=7, evidence_type="note", title="Accepted draft", metadata={}, source_capability_id="RS-401", source_matrix_row_id="RS-401", limitations=[])
    with (
        patch("app.modules.research_science.service.repository.attach_research_evidence", return_value=attached),
        patch("app.modules.research_science.service.repository.create_research_audit_event") as mock_audit,
    ):
        result = service.attach_research_evidence_service(db, 1, "actor-1", request)
    assert result is attached
    assert mock_audit.called


def test_no_hard_delete_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "DELETE FROM" not in text


def test_no_provider_or_external_call_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in ["requests.post", "httpx", "smtp", "twilio", "send_sms", "send_email"]:
        assert marker not in text


def test_explicit_false_safety_flags_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "official_verification_enabled=False" in text or 'official_verification_enabled": False' in text
    assert "external_database_sync_enabled=False" in text or 'external_database_sync_enabled": False' in text
    assert "hidden_score_present=False" in text or 'hidden_score_present": False' in text
    assert "provider_integration_enabled=False" in text or 'provider_integration_enabled": False' in text


def test_dashboard_contract_has_no_fake_metrics() -> None:
    db = _db()
    with (
        patch("app.modules.research_science.service.repository.compute_research_dashboard_summary", return_value={
            "projects_summary": {"ACTIVE": 1},
            "student_research_summary": {},
            "supervision_summary": {},
            "publications_summary": {},
            "conferences_summary": {},
            "grants_summary": {},
            "ethics_summary": {},
            "evidence_summary": {},
            "bridge_summary": {"ACADEMIC_OPERATIONS": 1},
        }),
        patch("app.modules.research_science.service.repository.get_research_bridge_summary", return_value={"ACADEMIC_OPERATIONS": 1}),
        patch("app.modules.research_science.service.repository.create_dashboard_snapshot"),
        patch("app.modules.research_science.service.repository.create_research_audit_event"),
    ):
        result = service.get_research_dashboard_service(db, 1)
    assert result.fake_metrics is False
    assert result.master_matrix_commit == "c79cc31"
    assert result.master_matrix_rows == 467


def test_health_has_no_provider_or_hidden_score() -> None:
    db = _db()
    with patch("app.modules.research_science.service.repository.get_research_health_summary", return_value={"tenant_id": 1, "total_records": 1, "bridge_records": 0}):
        result = service.get_research_health_service(db, 1)
    assert result.provider_integration_enabled is False
    assert result.external_database_sync_enabled is False
    assert result.official_verification_enabled is False
    assert result.hidden_score_present is False