from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.quality_accreditation import service


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "quality_accreditation"


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


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
    assert "official_accreditation_approval_enabled=False" in text or 'official_accreditation_approval_enabled": False' in text
    assert "official_ministry_submission_enabled=False" in text or 'official_ministry_submission_enabled": False' in text
    assert "external_database_sync_enabled=False" in text or 'external_database_sync_enabled": False' in text
    assert "provider_integration_enabled=False" in text or 'provider_integration_enabled": False' in text
    assert "hidden_score_present=False" in text or 'hidden_score_present": False' in text


def test_dashboard_and_health_have_no_fake_metrics_or_hidden_scores() -> None:
    db = _db()
    with (
        patch("app.modules.quality_accreditation.service.repository.compute_dashboard_summary", return_value={
            "frameworks_summary": {"ACTIVE_METADATA_ONLY": 1},
            "standards_summary": {},
            "evidence_summary": {"REVIEWED_METADATA_ONLY": 1},
            "readiness_summary": {"READY_FOR_INTERNAL_REVIEW": 1},
            "self_assessment_summary": {},
            "improvement_summary": {},
            "audit_summary": {},
            "program_review_summary": {},
            "bridge_summary": {"ACADEMIC_OPERATIONS": 1},
            "brain_signal_summary": {},
        }),
        patch("app.modules.quality_accreditation.service.repository.create_dashboard_snapshot"),
        patch("app.modules.quality_accreditation.service.repository.create_quality_audit_event"),
    ):
        dashboard = service.get_quality_dashboard_service(db, 1)
    health = service.get_quality_health_service(db, 1)
    assert dashboard.fake_metrics is False
    assert dashboard.boundary_summary["hidden_score_present"] is False
    assert health.fake_metrics is False
    assert health.hidden_score_present is False