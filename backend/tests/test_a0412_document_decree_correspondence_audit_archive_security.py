from __future__ import annotations

from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "document_decree_correspondence"


def _module_text() -> str:
    return "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))


def test_no_hard_delete_patterns_present() -> None:
    text = _module_text().lower()
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "delete from" not in text


def test_no_external_delivery_or_submission_execution_present() -> None:
    text = _module_text().lower()
    forbidden = [
        "send_external_delivery",
        "externalministrysubmission",
        "submit_to_ministry",
        "smtplib",
        "send_email",
        "send_sms",
        "httpx",
        "requests.post",
    ]
    for marker in forbidden:
        assert marker not in text


def test_no_autonomy_or_signing_execution_present() -> None:
    text = _module_text().lower()
    forbidden = [
        "automatic_rector_decision_enabled = true",
        "automatic_decree_approval_enabled = true",
        "automatic_document_signing_enabled = true",
        "def sign_document",
        "def issue_official_decree",
        "def approve_decree_auto",
        "def rector_decision_auto",
    ]
    for marker in forbidden:
        assert marker not in text


def test_safety_constants_present() -> None:
    text = _module_text()
    required = [
        "FAKE_DOCUMENTS = False",
        "FAKE_DECREES = False",
        "FAKE_SIGNATURES = False",
        "FAKE_DELIVERY_CONFIRMATIONS = False",
        "FAKE_ARCHIVE_LEGAL_RECORD = False",
        "OFFICIAL_LEGAL_EFFECT = False",
        "EXTERNAL_SUBMISSION_ENABLED = False",
        "AUTOMATIC_RECTOR_DECISION_ENABLED = False",
        "AUTOMATIC_DECREE_APPROVAL_ENABLED = False",
        "AUTOMATIC_DOCUMENT_SIGNING_ENABLED = False",
        "HIDDEN_SCORE_PRESENT = False",
        "HUMAN_REVIEW_REQUIRED = True",
    ]
    for marker in required:
        assert marker in text


def test_no_hidden_score_schema_model_route_markers() -> None:
    text = _module_text().lower()
    assert "hiddenstaffscore" not in text
    assert "hiddendepartmentscore" not in text
