from __future__ import annotations

import pytest

from app.modules.security_access_compliance import models, permissions


def test_table_inventory_is_exact_24() -> None:
    assert len(models.TABLE_NAMES) == 24


def test_permission_inventory_is_exact_44() -> None:
    assert permissions.SECURITY_ACCESS_COMPLIANCE_PERMISSION_COUNT == 44
    assert len(permissions.ALL_PERMISSIONS) == 44


def test_module_constants_match_contract() -> None:
    assert models.MODULE_NAME == "security_access_compliance"
    assert models.API_PREFIX == "/api/admin/security-access-compliance"
    assert models.RUNTIME_MODE == "GOVERNANCE_READINESS_EVIDENCE_AUDIT_CONTROL_METADATA_HUMAN_REVIEW_ONLY"
    assert models.EXPECTED_TABLE_COUNT == 24
    assert models.EXPECTED_ROUTE_COUNT == 47
    assert models.EXPECTED_PERMISSION_COUNT == 44
    assert models.TABLE_PREFIX == "sac_"


@pytest.mark.parametrize("table_name", sorted(models.TABLE_NAMES))
def test_all_table_names_have_sac_prefix(table_name: str) -> None:
    assert table_name.startswith("sac_")


@pytest.mark.parametrize(
    "forbidden",
    [
        "certified_compliance",
        "certified_security",
        "soc_siem",
        "incident_closure_official",
        "audit_proof_generated",
        "penetration_test_result",
        "vulnerability_scan_result",
        "hidden_user_risk_score",
        "discriminatory_ranking",
        "autonomous_enforcement",
        "external_regulator_submission",
    ],
)
def test_forbidden_table_names_are_absent(forbidden: str) -> None:
    assert all(forbidden not in name for name in models.TABLE_NAMES)


def test_safety_flags_are_fail_closed() -> None:
    assert models.FAKE_SECURITY_CERTIFICATION is False
    assert models.FAKE_COMPLIANCE_CERTIFICATION is False
    assert models.LEGAL_REGULATORY_COMPLIANCE_CLAIMED is False
    assert models.SOC_SIEM_REPLACEMENT_CLAIMED is False
    assert models.FAKE_INCIDENT_RESOLUTION is False
    assert models.FAKE_AUDIT_PROOF is False
    assert models.FAKE_PENETRATION_TEST_RESULT is False
    assert models.FAKE_VULNERABILITY_SCAN_RESULT is False
    assert models.FAKE_RISK_SCORE is False
    assert models.HIDDEN_USER_RISK_SCORE_PRESENT is False
    assert models.DISCRIMINATORY_RANKING_PRESENT is False
    assert models.AUTONOMOUS_ENFORCEMENT_ENABLED is False
    assert models.AUTOMATIC_USER_BLOCKING_ENABLED is False
    assert models.AUTOMATIC_USER_SANCTION_ENABLED is False
    assert models.AUTOMATIC_DATA_DELETION_ENABLED is False
    assert models.EXTERNAL_REGULATOR_SUBMISSION_ENABLED is False
    assert models.PRODUCTION_SECURITY_CLAIMED is False
    assert models.HUMAN_REVIEW_REQUIRED is True
