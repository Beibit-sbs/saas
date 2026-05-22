from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.academic_operations import schemas
from app.modules.academic_operations import service


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "academic_operations"


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
        patch("app.modules.academic_operations.service.get_academic_group_service", return_value=current),
        patch("app.modules.academic_operations.service.repository.update_academic_group", return_value=updated),
        patch("app.modules.academic_operations.service.repository.create_audit_event") as mock_audit,
    ):
        result = service.update_academic_group_service(db, 1, "actor-10", 10, schemas.AcademicGroupUpdateRequest(group_name="Updated", limitations=[]))
    assert result.status == "ACTIVE"
    assert mock_audit.called


def test_evidence_attach_uses_metadata_only() -> None:
    db = _db()
    attached = SimpleNamespace(id=1, status="DRAFT")
    request = schemas.AcademicOperationsEvidenceCreateRequest(entity_type="gradebook_metadata", entity_id=7, evidence_kind="note", metadata={}, source_capability_id="VRT-315", source_matrix_row_id="VRT-315", limitations=[])
    with (
        patch("app.modules.academic_operations.service.repository.attach_evidence_metadata", return_value=attached),
        patch("app.modules.academic_operations.service.repository.create_audit_event") as mock_audit,
    ):
        result = service.attach_evidence_metadata_service(db, 1, "actor-1", request)
    assert result is attached
    assert mock_audit.called


def test_no_hard_delete_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "DELETE FROM" not in text


def test_no_provider_or_external_call_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in ["requests.post", "httpx", "smtp", "twilio", "send_sms", "send_email", "external_submission"]:
        assert marker not in text


def test_no_positive_forbidden_claim_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in ["production-ready", "sales-ready", "GCC-ready", "official transcript update", "official order generated"]:
        assert marker not in text


def test_explicit_false_safety_flags_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "official_grade_publication_enabled=False" in text or 'official_grade_publication_enabled": False' in text
    assert "automated_grading_enabled=False" in text or 'automated_grading_enabled": False' in text
    assert "automatic_sanction_enabled=False" in text or 'automatic_sanction_enabled": False' in text
    assert "hidden_score_present=False" in text or 'hidden_score_present": False' in text
    assert "fake_metrics=False" in text or 'fake_metrics": False' in text


def test_no_duplicate_module_creation_claims() -> None:
    forbidden_dirs = [
        BACKEND_DIR / "app" / "modules" / "academic_committee_decisions",
        BACKEND_DIR / "app" / "modules" / "prerequisite_validation",
        BACKEND_DIR / "app" / "modules" / "thesis_supervision_management",
        BACKEND_DIR / "app" / "modules" / "summer_semester_management",
    ]
    for path in forbidden_dirs:
        assert not path.exists()


def test_dashboard_contract_has_no_fake_kpi() -> None:
    db = _db()
    with (
        patch("app.modules.academic_operations.service.repository.compute_dashboard_summary", return_value={
            "academic_groups": {"ACTIVE": 1},
            "cohorts": {},
            "gradebook_metadata": {},
            "retake_plans": {},
            "summer_semester_terms": {},
            "advisor_tutor_assignments": {},
            "canonical_bridges": {"student_lifecycle": 1},
        }),
        patch("app.modules.academic_operations.service.repository.get_canonical_bridge_summary", return_value={"student_lifecycle": 1}),
        patch("app.modules.academic_operations.service.repository.create_dashboard_snapshot"),
    ):
        result = service.get_academic_operations_dashboard_service(db, 1)
    assert result.fake_metrics is False
    assert result.master_matrix_commit == "c79cc31"
    assert result.master_matrix_rows == 467


def test_health_has_no_provider_or_hidden_score() -> None:
    db = _db()
    with (
        patch("app.modules.academic_operations.service.repository.get_health_summary", return_value={"tenant_id": 1, "total_records": 1, "bridge_records": 0}),
        patch("app.modules.academic_operations.service.repository.create_audit_event"),
    ):
        result = service.get_academic_operations_health_service(db, 1)
    assert result.provider_integration_enabled is False
    assert result.platonus_sync_enabled is False
    assert result.sis_sync_enabled is False
    assert result.hidden_score_present is False