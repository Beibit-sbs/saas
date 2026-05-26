from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.hr_staff_governance import service


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "hr_staff_governance"


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
    for marker in ["requests.post", "requests.get", "httpx", "boto3", "smtplib", "send_email", "send_sms", "1c", "payroll_run"]:
        assert marker not in text.lower()


def test_explicit_false_safety_flags_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in [
        'AUTOMATIC_HIRING_DECISION_ENABLED = False',
        'AUTOMATIC_FIRING_DECISION_ENABLED = False',
        'AUTOMATIC_HR_DISCIPLINARY_DECISION_ENABLED = False',
        'AUTOMATIC_LEAVE_APPROVAL_ENABLED = False',
        'AUTOMATIC_LEAVE_REJECTION_ENABLED = False',
        'AUTOMATIC_PAYROLL_DECISION_ENABLED = False',
        'AUTONOMOUS_ACCESS_REVOCATION_ENABLED = False',
        'PROVIDER_LIVE_INTEGRATION_ENABLED = False',
        'ONE_C_LIVE_SYNC_ENABLED = False',
        'PAYROLL_LIVE_SYNC_ENABLED = False',
        'EXTERNAL_DB_SYNC_ENABLED = False',
        'HIDDEN_EMPLOYEE_SCORE_PRESENT = False',
        'HIDDEN_FACULTY_SCORE_PRESENT = False',
        'DISCRIMINATORY_SCORE_PRESENT = False',
        'FAKE_HR_DATA = False',
    ]:
        assert marker in text


def test_dashboard_and_health_have_no_fake_metrics_or_hidden_scores() -> None:
    db = _db()
    with patch(
        "app.modules.hr_staff_governance.service.repository.repo_compute_dashboard_summary",
        return_value={
            "staff_lifecycle_summary": {"DRAFT": 1},
            "recruitment_readiness": {},
            "onboarding_progress": {},
            "employee_record_completeness": {},
            "leave_request_review_status": {},
            "training_certification_risk": {},
            "disciplinary_human_review_queue": {},
            "offboarding_access_review": {},
            "workload_bridge_visibility": {},
            "payroll_readiness_profile": {},
            "provider_readiness_status": {},
        },
    ):
        dashboard = service.get_hr_dashboard_summary(db, 1)
    health = service.get_health_summary(db, 1)
    assert dashboard.fake_metrics is False
    assert dashboard.fake_hr_data is False
    assert dashboard.hidden_score_present is False
    assert health["fake_metrics"] is False
    assert health["hidden_score_present"] is False