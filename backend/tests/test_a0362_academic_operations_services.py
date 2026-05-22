from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.academic_operations import schemas
from app.modules.academic_operations import service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


@pytest.mark.parametrize(
    ("create_func", "repo_path", "payload_obj", "expected_event"),
    [
        (service.create_academic_group_service, "create_academic_group", schemas.AcademicGroupCreateRequest(group_code="GRP-1", group_name="Group 1", source_capability_id="VRT-301", source_matrix_row_id="VRT-301", limitations=[]), "ACADEMIC_GROUP_CREATED"),
        (service.create_cohort_service, "create_cohort", schemas.CohortCreateRequest(cohort_code="COH-1", cohort_name="Cohort 1", academic_group_ref=None, source_capability_id="VRT-302", source_matrix_row_id="VRT-302", limitations=[]), "COHORT_CREATED"),
        (service.create_course_registration_metadata_service, "create_course_registration_metadata", schemas.CourseRegistrationMetadataCreateRequest(student_ref="S-1", course_ref="C-1", canonical_module_ref="enrollments", metadata={}, source_capability_id="VRT-306", source_matrix_row_id="VRT-306", limitations=[]), "COURSE_REGISTRATION_METADATA_CREATED"),
        (service.create_gradebook_metadata_service, "create_gradebook_metadata", schemas.GradebookMetadataCreateRequest(student_ref="S-1", course_ref="C-1", gradebook_key="GB-1", metadata={}, source_capability_id="VRT-315", source_matrix_row_id="VRT-315", limitations=[]), "GRADEBOOK_METADATA_CREATED"),
        (service.create_retake_plan_service, "create_retake_plan", schemas.RetakePlanCreateRequest(student_ref="S-1", course_ref="C-1", plan_code="RET-1", retake_window="2026-SUMMER", source_capability_id="VRT-319", source_matrix_row_id="VRT-319", limitations=[]), "RETAKE_PLAN_CREATED"),
        (service.create_summer_semester_term_service, "create_summer_semester_term", schemas.SummerSemesterTermCreateRequest(term_code="SUM-2026", display_name="Summer 2026", calendar_ref=None, source_capability_id="VRT-320", source_matrix_row_id="VRT-320", limitations=[]), "SUMMER_SEMESTER_CREATED"),
        (service.create_advisor_tutor_assignment_service, "create_advisor_tutor_assignment", schemas.AdvisorTutorAssignmentCreateRequest(student_ref="S-1", faculty_ref="F-1", assignment_code="AT-1", source_capability_id="VRT-326", source_matrix_row_id="VRT-326", limitations=[]), "ADVISOR_TUTOR_ASSIGNMENT_CREATED"),
        (service.create_canonical_module_bridge_service, "create_canonical_module_bridge", schemas.CanonicalModuleBridgeCreateRequest(bridge_type="student_lifecycle", canonical_module_ref="academic_records", metadata={}, source_capability_id="BRG-101", source_matrix_row_id="BRG-101", limitations=[]), "CANONICAL_BRIDGE_CREATED"),
    ],
)
def test_create_services_enforce_safety_defaults(create_func, repo_path: str, payload_obj, expected_event: str) -> None:
    db = _db()
    created = SimpleNamespace(id=1, status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False)
    with (
        patch(f"app.modules.academic_operations.service.repository.{repo_path}", return_value=created) as mock_create,
        patch("app.modules.academic_operations.service.repository.create_audit_event") as mock_audit,
    ):
        result = create_func(db, 1, "actor-1", payload_obj)
    assert result is created
    kwargs = mock_create.call_args.kwargs
    assert kwargs["human_review_required"] is True
    assert kwargs["automated_decision"] is False
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["platonus_sync_enabled"] is False
    assert kwargs["sis_sync_enabled"] is False
    assert kwargs["hidden_score_present"] is False
    assert kwargs["official_grade_publication_enabled"] is False
    assert kwargs["automated_grading_enabled"] is False
    assert kwargs["automatic_sanction_enabled"] is False
    assert mock_audit.call_args.kwargs["event_type"] == expected_event


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "1", "bad"])  # type: ignore[list-item]
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    db = _db()
    request = SimpleNamespace(group_code="GRP-1", group_name="Group", source_capability_id="VRT-301", source_matrix_row_id="VRT-301", limitations=[])
    with pytest.raises(TenantRequiredError):
        service.create_academic_group_service(db, tenant_id, "actor-1", request)  # type: ignore[arg-type]


def test_empty_actor_fails_closed() -> None:
    db = _db()
    request = SimpleNamespace(group_code="GRP-1", group_name="Group", source_capability_id="VRT-301", source_matrix_row_id="VRT-301", limitations=[])
    with pytest.raises(DomainValidationError):
        service.create_academic_group_service(db, 1, "", request)


@pytest.mark.parametrize(
    ("update_func", "getter_path", "repo_path", "payload_obj"),
    [
        (service.update_academic_group_service, "get_academic_group_service", "update_academic_group", schemas.AcademicGroupUpdateRequest(group_name="Updated", limitations=[])),
        (service.update_gradebook_metadata_service, "get_gradebook_metadata_service", "update_gradebook_metadata", schemas.GradebookMetadataUpdateRequest(metadata={"review": "required"}, limitations=[])),
        (service.update_retake_plan_service, "get_retake_plan_service", "update_retake_plan", schemas.RetakePlanUpdateRequest(retake_window="2026-FALL", limitations=[])),
        (service.update_summer_semester_term_service, "get_summer_semester_term_service", "update_summer_semester_term", schemas.SummerSemesterTermUpdateRequest(display_name="Updated Summer", limitations=[])),
        (service.update_advisor_tutor_assignment_service, "get_advisor_tutor_assignment_service", "update_advisor_tutor_assignment", schemas.AdvisorTutorAssignmentUpdateRequest(assignment_code="AT-1", notes="manual", limitations=[])),
    ],
)
def test_update_services_keep_runtime_safety_false(update_func, getter_path: str, repo_path: str, payload_obj) -> None:
    db = _db()
    current = SimpleNamespace(id=7, status="DRAFT")
    updated = SimpleNamespace(id=7, status="ACTIVE", human_review_required=True)
    with (
        patch(f"app.modules.academic_operations.service.{getter_path}", return_value=current),
        patch(f"app.modules.academic_operations.service.repository.{repo_path}", return_value=updated) as mock_update,
        patch("app.modules.academic_operations.service.repository.create_audit_event"),
    ):
        result = update_func(db, 1, "actor-2", 7, payload_obj)
    assert result is updated
    kwargs = mock_update.call_args.kwargs
    assert kwargs["automated_decision"] is False
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["platonus_sync_enabled"] is False
    assert kwargs["sis_sync_enabled"] is False
    assert kwargs["hidden_score_present"] is False
    assert kwargs["official_grade_publication_enabled"] is False
    assert kwargs["automated_grading_enabled"] is False
    assert kwargs["automatic_sanction_enabled"] is False


def test_getters_fail_on_missing_resource() -> None:
    db = _db()
    with patch("app.modules.academic_operations.service.repository.get_academic_group", return_value=None):
        with pytest.raises(DomainValidationError):
            service.get_academic_group_service(db, 1, 99)


def test_dashboard_contract_is_matrix_guided() -> None:
    db = _db()
    with (
        patch("app.modules.academic_operations.service.repository.compute_dashboard_summary", return_value={
            "academic_groups": {"ACTIVE": 1},
            "cohorts": {"ACTIVE": 2},
            "gradebook_metadata": {"REVIEW_REQUIRED": 1},
            "retake_plans": {"DRAFT": 1},
            "summer_semester_terms": {"ACTIVE": 1},
            "advisor_tutor_assignments": {"ACTIVE": 1},
            "canonical_bridges": {"student_lifecycle": 2},
        }),
        patch("app.modules.academic_operations.service.repository.get_canonical_bridge_summary", return_value={"student_lifecycle": 2}),
        patch("app.modules.academic_operations.service.repository.create_dashboard_snapshot"),
    ):
        result = service.get_academic_operations_dashboard_service(db, 1)
    assert result.fake_metrics is False
    assert result.data_source == "computed_from_academic_operations_metadata"
    assert result.master_matrix_commit == "c79cc31"
    assert result.master_matrix_rows == 467
    assert result.incomplete_data is False


def test_dashboard_marks_incomplete_when_bridges_missing() -> None:
    db = _db()
    with (
        patch("app.modules.academic_operations.service.repository.compute_dashboard_summary", return_value={
            "academic_groups": {},
            "cohorts": {},
            "gradebook_metadata": {},
            "retake_plans": {},
            "summer_semester_terms": {},
            "advisor_tutor_assignments": {},
            "canonical_bridges": {},
        }),
        patch("app.modules.academic_operations.service.repository.get_canonical_bridge_summary", return_value={}),
        patch("app.modules.academic_operations.service.repository.create_dashboard_snapshot"),
    ):
        result = service.get_academic_operations_dashboard_service(db, 1)
    assert result.incomplete_data is True
    assert result.fake_metrics is False


def test_matrix_summary_contract() -> None:
    db = _db()
    with patch("app.modules.academic_operations.service.repository.create_audit_event"):
        result = service.get_academic_operations_matrix_summary_service(db, 1)
    assert result.master_matrix_commit == "c79cc31"
    assert result.master_matrix_rows == 467
    assert result.duplicate_module_policy == "REUSE_CANONICALS_AND_BRIDGE_ONLY"
    assert "course_catalog" in result.canonical_reuse_map
    assert "student_lifecycle" in result.bridge_map
    assert "official_grade_publication" in result.forbidden_runtime_claims


def test_canonical_reuse_summary_contract() -> None:
    db = _db()
    with patch("app.modules.academic_operations.service.repository.get_canonical_bridge_summary", return_value={"student_lifecycle": 3}):
        result = service.get_canonical_reuse_summary_service(db, 1)
    assert result["reuse_policy"] == "REUSE_EXISTING_CANONICAL_MODULES_ONLY"
    assert result["duplicate_policy"] == "REUSE_CANONICALS_AND_BRIDGE_ONLY"
    assert result["canonical_reuse_map"]["academic_committee_decisions"] == "committee_decision_registry"
    assert result["bridge_counts"]["student_lifecycle"] == 3


def test_attach_evidence_metadata_service_is_metadata_only() -> None:
    db = _db()
    request = schemas.AcademicOperationsEvidenceCreateRequest(entity_type="gradebook_metadata", entity_id=7, evidence_kind="note", metadata={}, source_capability_id="VRT-315", source_matrix_row_id="VRT-315", limitations=[])
    attached = SimpleNamespace(id=1, status="DRAFT")
    with (
        patch("app.modules.academic_operations.service.repository.attach_evidence_metadata", return_value=attached) as mock_attach,
        patch("app.modules.academic_operations.service.repository.create_audit_event"),
    ):
        result = service.attach_evidence_metadata_service(db, 1, "actor-1", request)
    assert result is attached
    kwargs = mock_attach.call_args.kwargs
    assert kwargs["provider_integration_enabled"] is False
    assert kwargs["platonus_sync_enabled"] is False
    assert kwargs["sis_sync_enabled"] is False


def test_health_contract_is_fail_closed() -> None:
    db = _db()
    with (
        patch("app.modules.academic_operations.service.repository.get_health_summary", return_value={"tenant_id": 1, "total_records": 0, "bridge_records": 0}),
        patch("app.modules.academic_operations.service.repository.create_audit_event"),
    ):
        result = service.get_academic_operations_health_service(db, 1)
    assert result.provider_integration_enabled is False
    assert result.platonus_sync_enabled is False
    assert result.sis_sync_enabled is False
    assert result.hidden_score_present is False
    assert result.fake_metrics is False
    assert result.route_count == 39
    assert result.table_count == 19