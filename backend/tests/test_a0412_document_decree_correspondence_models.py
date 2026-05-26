from __future__ import annotations

from app.modules.document_decree_correspondence import models, permissions


def test_table_inventory_is_exact_26() -> None:
    assert len(models.TABLE_NAMES) == 26


def test_permission_inventory_is_exact_50() -> None:
    assert permissions.DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT == 50
    assert len(permissions.ALL_PERMISSIONS) == 50


def test_module_constants_match_contract() -> None:
    assert models.MODULE_NAME == "document_decree_correspondence"
    assert models.API_PREFIX == "/api/admin/document-decree-correspondence"
    assert models.RUNTIME_MODE == "METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY"
    assert models.EXPECTED_TABLE_COUNT == 26
    assert models.EXPECTED_ROUTE_COUNT == 53
    assert models.EXPECTED_PERMISSION_COUNT == 50
    assert models.TABLE_PREFIX == "ddc_"


def test_all_table_names_have_ddc_prefix() -> None:
    assert all(name.startswith("ddc_") for name in models.TABLE_NAMES)


def test_forbidden_table_patterns_absent() -> None:
    forbidden = {
        "official_signed_documents",
        "legal_effect_decree_execution",
        "external_delivery_execution",
        "external_ministry_submission",
        "hidden_staff_score",
        "hidden_department_score",
    }
    assert not (models.TABLE_NAMES & forbidden)


def test_safety_flags_are_explicit_false_true() -> None:
    assert models.FAKE_DOCUMENTS is False
    assert models.FAKE_DECREES is False
    assert models.FAKE_SIGNATURES is False
    assert models.FAKE_DELIVERY_CONFIRMATIONS is False
    assert models.FAKE_ARCHIVE_LEGAL_RECORD is False
    assert models.OFFICIAL_LEGAL_EFFECT is False
    assert models.EXTERNAL_SUBMISSION_ENABLED is False
    assert models.AUTOMATIC_RECTOR_DECISION_ENABLED is False
    assert models.AUTOMATIC_DECREE_APPROVAL_ENABLED is False
    assert models.AUTOMATIC_DOCUMENT_SIGNING_ENABLED is False
    assert models.HIDDEN_SCORE_PRESENT is False
    assert models.HUMAN_REVIEW_REQUIRED is True
