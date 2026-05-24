from __future__ import annotations

from pathlib import Path

from app.modules.quality_accreditation import models, permissions


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "qa38a2rt01_a0382_quality_accreditation_tables.py"

EXPECTED_TABLES = {
    "qa_quality_frameworks",
    "qa_quality_policy_registry",
    "qa_accreditation_standards",
    "qa_standard_criteria",
    "qa_standards_evidence_requirements",
    "qa_quality_evidence_registry",
    "qa_evidence_review",
    "qa_evidence_limitations",
    "qa_program_accreditation_readiness",
    "qa_institutional_accreditation_readiness",
    "qa_self_assessment_reports",
    "qa_self_assessment_sections",
    "qa_quality_improvement_plans",
    "qa_quality_improvement_actions",
    "qa_internal_quality_audits",
    "qa_quality_audit_findings",
    "qa_program_review_cycles",
    "qa_learning_outcomes_assessment",
    "qa_stakeholder_feedback_metadata",
    "qa_survey_quality_metadata",
    "qa_external_expert_reviews",
    "qa_expert_recommendation_response_plans",
    "qa_accreditation_committee_workflow",
    "qa_compliance_gap_analysis",
    "qa_accreditation_calendar",
    "qa_quality_risk_register",
    "qa_quality_bridge_metadata",
    "qa_quality_dashboard_snapshots",
    "qa_quality_brain_signals",
    "qa_quality_audit_events",
    "qa_quality_status_history",
    "qa_quality_limitations",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "quality_accreditation"
    assert models.TABLE_PREFIX == "qa_"
    assert models.TARGET_LEVEL == "L3"
    assert models.CONTRACT_VERSION == "A-038.2"
    assert models.FOUNDATION_STATUS == "QUALITY_ACCREDITATION_METADATA_EVIDENCE_BACKEND_FOUNDATION"
    assert models.SOURCE_PRODUCT_MAP_COMMIT == "1253e19"
    assert models.SOURCE_VERTICAL_SELECTION_COMMIT == "7da0c70"
    assert models.MASTER_MATRIX_COMMIT == "c79cc31"
    assert models.MASTER_MATRIX_ROW_COUNT == 467
    assert models.RUNTIME_MODE == "METADATA_EVIDENCE_ONLY"


def test_metadata_contains_expected_32_tables() -> None:
    qa_tables = {name for name in models.Base.metadata.tables if name.startswith("qa_")}
    assert qa_tables == EXPECTED_TABLES


def test_permissions_cover_runtime_slice() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 55
    assert permissions.STANDARDS_CREATE in permissions.ALL_PERMISSIONS
    assert permissions.EVIDENCE_LIMITATIONS_MANAGE in permissions.ALL_PERMISSIONS
    assert permissions.ADMIN_CONFIGURE in permissions.ALL_PERMISSIONS


def test_migration_contains_all_foundation_tables() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text
    assert 'down_revision = "rs37a2rt01"' in text
    assert "create_table" in text