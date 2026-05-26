from __future__ import annotations

from pathlib import Path

from app.modules.hr_staff_governance import models, permissions


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "hr39a2rt01_a0392_hr_staff_governance_tables.py"


EXPECTED_TABLES = {
    "hr_staff_profiles",
    "hr_employee_records",
    "hr_staff_status_history",
    "hr_position_assignments",
    "hr_department_assignments",
    "hr_faculty_profiles",
    "hr_recruitment_requests",
    "hr_recruitment_pipeline_items",
    "hr_candidate_shortlist_metadata",
    "hr_hiring_committee_reviews",
    "hr_hiring_evidence_packs",
    "hr_onboarding_cases",
    "hr_onboarding_checklist_items",
    "hr_probation_reviews",
    "hr_leave_requests",
    "hr_absence_metadata",
    "hr_leave_balance_snapshots",
    "hr_staff_attendance_metadata",
    "hr_staff_requests",
    "hr_staff_appeals",
    "hr_policy_exceptions",
    "hr_performance_appraisal_cycles",
    "hr_appraisal_review_evidence",
    "hr_training_certifications",
    "hr_certification_expiry_tracking",
    "hr_staff_development_plans",
    "hr_disciplinary_cases",
    "hr_disciplinary_review_evidence",
    "hr_exit_offboarding_cases",
    "hr_access_lifecycle_reviews",
    "hr_workload_bridge_records",
    "hr_payroll_readiness_profiles",
    "hr_provider_readiness_evidence",
    "hr_staff_compliance_dashboard_snapshots",
    "hr_audit_events",
    "hr_evidence_repository",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "hr_staff_governance"
    assert models.TABLE_PREFIX == "hr_"
    assert models.TARGET_LEVEL == "L3"
    assert models.CONTRACT_VERSION == "A-039.2"
    assert models.FOUNDATION_STATUS == "HR_STAFF_GOVERNANCE_METADATA_EVIDENCE_BACKEND_FOUNDATION"
    assert models.SOURCE_SPEC_COMMIT == "09e968b"
    assert models.SOURCE_PRODUCT_MAP_COMMIT == "eaff24f"
    assert models.SOURCE_VERTICAL_SELECTION_COMMIT == "449a407"
    assert models.RUNTIME_MODE == "METADATA_EVIDENCE_HUMAN_REVIEW_ONLY"


def test_metadata_contains_expected_36_tables() -> None:
    hr_tables = {name for name in models.Base.metadata.tables if name.startswith("hr_")}
    assert hr_tables == EXPECTED_TABLES
    assert models.TABLE_NAMES == EXPECTED_TABLES


def test_permissions_cover_runtime_slice() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 56
    assert permissions.STAFF_PROFILES_CREATE in permissions.ALL_PERMISSIONS
    assert permissions.DISCIPLINARY_CASES_REVIEW in permissions.ALL_PERMISSIONS
    assert permissions.PROVIDER_READINESS_READ in permissions.ALL_PERMISSIONS


def test_migration_contains_all_foundation_tables() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text
    assert 'down_revision = "qa38a2rt01"' in text
    assert "create_table" in text