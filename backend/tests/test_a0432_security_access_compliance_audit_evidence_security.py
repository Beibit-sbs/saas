from __future__ import annotations

from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "security_access_compliance"


def _module_text() -> str:
    return "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))


def test_no_hard_delete_patterns_present() -> None:
    text = _module_text().lower()
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "delete from" not in text


@pytest.mark.parametrize(
    "forbidden",
    [
        "certify_compliance",
        "certify_security",
        "close_incident_officially",
        "auto_block_user",
        "auto_sanction_user",
        "auto_delete_data",
        "submit_to_regulator",
        "publish_risk_score",
        "hidden_user_score",
        "securitycertificationrequest",
        "compliancecertificationrequest",
        "legalregulatorycomplianceclaimrequest",
        "socsiemreplacementrequest",
        "autoblockuserrequest",
        "autosanctionuserrequest",
        "autodeletedatarequest",
        "regulatorsubmissionrequest",
        "fakeauditproofrequest",
        "fakeincidentresolutionrequest",
        "fakepentestresultrequest",
        "fakevulnerabilityscanrequest",
    ],
)
def test_forbidden_markers_absent(forbidden: str) -> None:
    assert forbidden not in _module_text().replace("_", "").replace(" ", "").lower()


@pytest.mark.parametrize(
    "required",
    [
        "FAKE_SECURITY_CERTIFICATION = False",
        "FAKE_COMPLIANCE_CERTIFICATION = False",
        "LEGAL_REGULATORY_COMPLIANCE_CLAIMED = False",
        "SOC_SIEM_REPLACEMENT_CLAIMED = False",
        "FAKE_INCIDENT_RESOLUTION = False",
        "FAKE_AUDIT_PROOF = False",
        "FAKE_PENETRATION_TEST_RESULT = False",
        "FAKE_VULNERABILITY_SCAN_RESULT = False",
        "FAKE_RISK_SCORE = False",
        "HIDDEN_USER_RISK_SCORE_PRESENT = False",
        "DISCRIMINATORY_RANKING_PRESENT = False",
        "AUTONOMOUS_ENFORCEMENT_ENABLED = False",
        "AUTOMATIC_USER_BLOCKING_ENABLED = False",
        "AUTOMATIC_USER_SANCTION_ENABLED = False",
        "AUTOMATIC_DATA_DELETION_ENABLED = False",
        "EXTERNAL_REGULATOR_SUBMISSION_ENABLED = False",
        "PRODUCTION_SECURITY_CLAIMED = False",
        "HUMAN_REVIEW_REQUIRED = True",
    ],
)
def test_required_safety_markers_present(required: str) -> None:
    assert required in _module_text()


def test_no_secret_or_token_logging_patterns() -> None:
    lowered = _module_text().lower()
    forbidden = [
        "access_token",
        "refresh_token",
        "session_secret",
        "jwt_secret",
        "authorization:",
        "password=",
    ]
    for marker in forbidden:
        assert marker not in lowered


def test_metadata_only_runtime_markers_present() -> None:
    text = _module_text()
    assert "metadata" in text.lower()
    assert "human_review_required" in text.lower()
    assert "incomplete_data" in text.lower()
