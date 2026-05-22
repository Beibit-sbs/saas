from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.academic_operations import models, permissions, router as router_module
from app.modules.rbac import service as rbac_service


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "ao36rt52uv71_a0362_academic_operations_tables.py"

EXPECTED_TABLES = {
    "ao_academic_groups",
    "ao_cohorts",
    "ao_course_registration_metadata",
    "ao_gradebook_metadata",
    "ao_retake_plans",
    "ao_summer_semester_terms",
    "ao_advisor_tutor_assignments",
    "ao_canonical_module_bridges",
    "ao_student_lifecycle_bridge_metadata",
    "ao_document_workflow_bridge_metadata",
    "ao_executive_governance_bridge_metadata",
    "ao_quality_accreditation_bridge_metadata",
    "ao_academic_operations_dashboard_snapshots",
    "ao_academic_operations_audit_events",
    "ao_academic_operations_evidence_metadata",
    "ao_academic_operations_limitations",
    "ao_academic_operations_status_history",
    "ao_gradebook_status_history",
    "ao_retake_status_history",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "academic_operations"
    assert models.TABLE_PREFIX == "ao_"
    assert models.TARGET_LEVEL == "L3"
    assert models.CONTRACT_VERSION == "A-036.2"
    assert models.FOUNDATION_STATUS == "MATRIX_GUIDED_CANONICAL_AWARE_BACKEND_FOUNDATION"
    assert models.MASTER_MATRIX_COMMIT == "c79cc31"
    assert models.MATRIX_ROW_COUNT == 467
    assert models.DUPLICATE_MODULE_POLICY == "REUSE_CANONICALS_AND_BRIDGE_ONLY"


def test_metadata_contains_expected_19_tables() -> None:
    ao_tables = {name for name in models.Base.metadata.tables if name.startswith("ao_")}
    assert ao_tables == EXPECTED_TABLES


@pytest.mark.parametrize("table_name", sorted(EXPECTED_TABLES))
def test_table_names_use_ao_prefix(table_name: str) -> None:
    assert table_name.startswith("ao_")


@pytest.mark.parametrize(
    ("table", "required_columns"),
    [
        (models.AcademicOperationsAcademicGroup.__table__.c, {"tenant_id", "status", "human_review_required", "automated_decision", "provider_integration_enabled", "platonus_sync_enabled", "sis_sync_enabled", "hidden_score_present", "official_grade_publication_enabled"}),
        (models.AcademicOperationsGradebookMetadata.__table__.c, {"gradebook_key", "automated_grading_enabled", "official_grade_publication_enabled", "hidden_score_present", "source_matrix_row_id", "source_capability_id"}),
        (models.AcademicOperationsRetakePlan.__table__.c, {"plan_code", "automatic_sanction_enabled", "hidden_score_present", "source_matrix_row_id", "source_capability_id"}),
        (models.AcademicOperationsDashboardSnapshot.__table__.c, {"tenant_id", "fake_metrics", "incomplete_data", "data_source", "summary_json"}),
        (models.AcademicOperationsAuditEvent.__table__.c, {"tenant_id", "entity_type", "event_type", "action", "payload_json"}),
    ],
)
def test_key_tables_contain_safety_and_matrix_columns(table, required_columns: set[str]) -> None:
    assert required_columns.issubset(set(table.keys()))


def test_router_prefix_and_route_count() -> None:
    routes = [route for route in router_module.router.routes if getattr(route, "path", "").startswith(router_module.router.prefix)]
    assert router_module.router.prefix == "/api/admin/academic-operations"
    assert len(routes) == 40


def test_permissions_cover_runtime_slice() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 40
    assert permissions.OVERVIEW_READ in permissions.ALL_PERMISSIONS
    assert permissions.CANONICAL_BRIDGE_CREATE in permissions.ALL_PERMISSIONS
    assert permissions.DEGREE_AUDIT_BRIDGE_READ in permissions.ALL_PERMISSIONS
    assert permissions.ADMIN_CONFIGURE in permissions.ALL_PERMISSIONS


def test_admin_superadmin_and_auditor_receive_permissions() -> None:
    assert permissions.ACADEMIC_GROUPS_CREATE in rbac_service.BASELINE_ROLE_PERMISSIONS["admin"]
    assert permissions.CANONICAL_BRIDGE_UPDATE in rbac_service.BASELINE_ROLE_PERMISSIONS["superadmin"]
    assert permissions.AUDIT_READ in rbac_service.BASELINE_ROLE_PERMISSIONS["auditor"]
    assert permissions.COURSE_CATALOG_BRIDGE_READ in rbac_service.BASELINE_ROLE_PERMISSIONS["auditor"]


@pytest.mark.parametrize(
    "missing_dir",
    [
        "course_catalog",
        "elective_course_selection_duplicate",
        "committee_decision_duplicate",
        "prerequisite_validation",
        "thesis_supervision_management",
        "academic_committee_decisions",
    ],
)
def test_no_duplicate_module_directories_created(missing_dir: str) -> None:
    assert not (BACKEND_DIR / "app" / "modules" / missing_dir).exists()


def test_migration_contains_all_foundation_tables() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text
    assert 'down_revision = "uq35sl24rt80"' in text
    assert "create_table" in text