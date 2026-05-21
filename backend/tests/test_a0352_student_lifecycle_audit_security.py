from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.student_lifecycle import service


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "student_lifecycle"


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_transition_creates_audit_event() -> None:
    db = _db()
    current = SimpleNamespace(id=10, status="DRAFT", archived_at=None)
    updated = SimpleNamespace(id=10, status="SUBMITTED", human_review_required=True, archived_at=None)
    with (
        patch("app.modules.student_lifecycle.service.get_applicant_service", return_value=current),
        patch("app.modules.student_lifecycle.service.repository.update_applicant", return_value=updated),
        patch("app.modules.student_lifecycle.service.repository.record_applicant_status") as mock_history,
        patch("app.modules.student_lifecycle.service.repository.create_audit_event") as mock_audit,
    ):
        result = service.update_applicant_status_service(db, 1, "actor-10", 10, "SUBMITTED", "ok")
    assert result.status == "SUBMITTED"
    assert mock_history.called
    assert mock_audit.called


def test_evidence_attach_uses_metadata_only() -> None:
    db = _db()
    request = SimpleNamespace(audit_event_id=5, entity_type="student_request", entity_id=7, evidence_type="note", evidence_ref="E-1", limitations=[])
    attached = SimpleNamespace(id=1, tenant_id=1, audit_event_id=5, entity_type="student_request", entity_id=7, evidence_type="note", evidence_ref="E-1", limitations_json=[], created_by_user_id="actor-1", created_at="2026-01-01T00:00:00Z")
    with (
        patch("app.modules.student_lifecycle.service.repository.attach_evidence_metadata", return_value=attached),
        patch("app.modules.student_lifecycle.service.repository.create_audit_event") as mock_audit,
    ):
        result = service.attach_evidence_metadata_service(db, 1, "actor-1", request)
    assert result.evidence_ref == "E-1"
    assert mock_audit.called


def test_no_hard_delete_source_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "DELETE FROM" not in text
    assert "hard delete" not in text.lower()


def test_no_provider_or_external_call_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    forbidden = [
        "requests.post",
        "httpx",
        "smtp",
        "twilio",
        "send_sms",
        "send_email",
        "external_submission",
    ]
    for marker in forbidden:
        assert marker not in text


def test_no_hidden_score_or_fake_transcript_behavior() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "official_document=False" in text or 'official_document = False' in text
    assert "hidden_score_present=False" in text or 'hidden_score_present = False' in text
    assert "fake_metrics=False" in text or 'fake_metrics = False' in text


def test_router_source_is_permission_gated() -> None:
    text = (MODULE_DIR / "router.py").read_text()
    assert text.count("permission_dependency(") >= 30
