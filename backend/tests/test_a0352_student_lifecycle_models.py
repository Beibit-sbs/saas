from __future__ import annotations

from pathlib import Path

from app.modules.rbac import service as rbac_service
from app.modules.student_lifecycle import permissions
from app.modules.student_lifecycle import router as router_module
from app.modules.student_lifecycle import models


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "uq35sl24rt80_a0352_student_lifecycle_tables.py"

EXPECTED_TABLES = {
    "sl_applicants",
    "sl_applicant_status_history",
    "sl_student_profiles",
    "sl_student_status_history",
    "sl_student_enrollments",
    "sl_enrollment_status_history",
    "sl_academic_records",
    "sl_transcript_previews",
    "sl_degree_progress_snapshots",
    "sl_student_requests",
    "sl_student_appeals",
    "sl_intervention_plans",
    "sl_student_lifecycle_audit_events",
    "sl_student_lifecycle_evidence_metadata",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "student_lifecycle"
    assert models.TABLE_PREFIX == "sl_"
    assert models.PROVIDER_INTEGRATION_ENABLED is False
    assert models.SIS_SYNC_ENABLED is False
    assert models.PLATONUS_LIVE_INTEGRATION_ENABLED is False
    assert models.AUTONOMOUS_DECISION_ENABLED is False
    assert models.FAKE_TRANSCRIPT_ENABLED is False
    assert models.HIDDEN_SCORE_ENABLED is False
    assert models.FAKE_METRICS_ENABLED is False


def test_metadata_contains_expected_14_tables() -> None:
    sl_tables = {name for name in models.Base.metadata.tables if name.startswith("sl_")}
    assert sl_tables == EXPECTED_TABLES


def test_table_names_use_sl_prefix() -> None:
    for name in EXPECTED_TABLES:
        assert name.startswith("sl_")


def test_core_columns_exist_on_key_tables() -> None:
    applicants = models.StudentLifecycleApplicant.__table__.c
    assert "tenant_id" in applicants
    assert "status" in applicants
    assert "human_review_required" in applicants
    assert "automated_decision" in applicants
    assert "provider_integration_enabled" in applicants
    assert "archived_at" in applicants

    transcript = models.StudentLifecycleTranscriptPreview.__table__.c
    assert "official_document" in transcript
    assert "automated_decision" in transcript
    assert "provider_integration_enabled" in transcript

    degree_progress = models.StudentLifecycleDegreeProgressSnapshot.__table__.c
    assert "hidden_score_present" in degree_progress
    assert "incomplete_data" in degree_progress
    assert "data_source" in degree_progress


def test_enum_values_exist_for_controlled_subset() -> None:
    assert models.ApplicantStatus.SUBMITTED in models.ApplicantStatus.ALL
    assert models.StudentStatus.ACTIVE in models.StudentStatus.ALL
    assert models.EnrollmentStatus.REGISTRAR_REVIEW in models.EnrollmentStatus.ALL
    assert models.AcademicRecordStatus.OPENED in models.AcademicRecordStatus.ALL
    assert models.TranscriptPreviewStatus.GENERATED_UNOFFICIAL_PREVIEW in models.TranscriptPreviewStatus.ALL
    assert models.DegreeProgressStatus.HUMAN_REVIEW_REQUIRED in models.DegreeProgressStatus.ALL
    assert models.StudentRequestStatus.RESPONSE_ISSUED in models.StudentRequestStatus.ALL
    assert models.StudentAppealStatus.ELIGIBILITY_CHECK in models.StudentAppealStatus.ALL
    assert models.InterventionStatus.OUTCOME_METADATA_RECORDED in models.InterventionStatus.ALL
    assert models.StudentLifecycleAuditEventType.EVIDENCE_METADATA_ATTACHED in models.StudentLifecycleAuditEventType.ALL


def test_router_prefix_and_route_count() -> None:
    routes = [route for route in router_module.router.routes if getattr(route, "path", "").startswith(router_module.router.prefix)]
    assert router_module.router.prefix == "/api/admin/student-lifecycle"
    assert len(routes) == 44


def test_permissions_cover_initial_runtime_slice() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 36
    assert permissions.APPLICANTS_READ in permissions.ALL_PERMISSIONS
    assert permissions.TRANSCRIPTS_PREVIEW in permissions.ALL_PERMISSIONS
    assert permissions.DASHBOARD_READ in permissions.ALL_PERMISSIONS


def test_admin_and_superadmin_receive_student_lifecycle_permissions() -> None:
    admin_perms = rbac_service.BASELINE_ROLE_PERMISSIONS["admin"]
    superadmin_perms = rbac_service.BASELINE_ROLE_PERMISSIONS["superadmin"]
    assert permissions.APPLICANTS_CREATE in admin_perms
    assert permissions.HEALTH_READ in admin_perms
    assert permissions.APPEALS_REVIEW in superadmin_perms
    assert permissions.EVIDENCE_ATTACH in superadmin_perms


def test_migration_contains_all_foundation_tables() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text
    assert "down_revision = (" in text
