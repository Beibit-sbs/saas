#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

run_backend_checks() {
  "${COMPOSE[@]}" run --rm --no-deps backend-tests "$@"
}

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null
"${COMPOSE[@]}" up -d db redis

echo "[data-layer-gate] migration graph safety"
run_backend_checks alembic heads
run_backend_checks alembic upgrade head

echo "[data-layer-gate] tenant fail-closed and context integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/test_tenant_fail_closed_schema.py \
  tests/test_tenant_fail_closed.py \
  tests/test_feature_flags_tenant_isolation.py \
  tests/test_db_tenant_context.py \
  tests/test_auth_tenant_context.py

echo "[data-layer-gate] domain binding consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/students/test_lifecycle_service.py

echo "[data-layer-gate] transcript enrollment reconciliation integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/transcripts/test_transcript_service.py \
  tests/modules/transcripts/test_router_transcripts.py

echo "[data-layer-gate] grades enrollment reconciliation integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/grades/test_grade_lifecycle_service.py \
  tests/modules/grades/test_router_grades_phase3.py

echo "[data-layer-gate] scheduling section and attendance consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/scheduling/test_scheduling_service.py \
  tests/modules/scheduling/test_router_scheduling.py

echo "[data-layer-gate] interventions case and action consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/interventions/test_router_interventions_phase1.py

echo "[data-layer-gate] degree progress binding and requirement consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/degree_progress/test_degree_progress_service.py \
  tests/modules/degree_progress/test_router_degree_progress.py

echo "[data-layer-gate] enrollment reference consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/enrollments/test_enrollment_lifecycle_service.py \
  tests/modules/enrollments/test_router_enrollments.py

echo "[data-layer-gate] courses program reference consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/courses/test_courses_service.py::test_get_course_consistency_report_detects_missing_programs \
  tests/modules/courses/test_courses_service.py::test_get_course_consistency_report_detects_code_and_field_drift \
  tests/modules/courses/test_router_courses.py

echo "[data-layer-gate] programs code consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/programs/test_programs_service.py::test_get_program_consistency_report_detects_missing_and_duplicate_codes \
  tests/modules/programs/test_programs_service.py::test_get_program_consistency_report_detects_field_and_type_drift \
  tests/modules/programs/test_router_programs.py

echo "[data-layer-gate] profiles people consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/profiles/test_service.py::TestPersonService::test_list_tenant_person_consistency_report_detects_issues \
  tests/modules/profiles/test_router.py::test_list_people_consistency_success

echo "[data-layer-gate] org structure hierarchy consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/org_structure/test_org_structure.py::TestOrgUnitTree::test_consistency_endpoint_returns_issues \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_missing_parent_and_multiple_roots \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_multi_node_cycle \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_invalid_parent_type \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_active_child_with_inactive_parent \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_duplicate_codes \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_missing_root_unit \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_non_university_root_unit \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_multiple_university_roots \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_inactive_university_root \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_multiple_active_university_roots \
  tests/modules/org_structure/test_org_structure.py::TestTenantIsolation::test_consistency_report_detects_missing_university_root_without_roots

echo "[data-layer-gate] faculty data quality consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/faculty/test_faculty_service.py \
  tests/modules/faculty/test_router_faculty.py

echo "[data-layer-gate] academic records reference consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/academic_records/test_academic_records_service.py::test_get_record_consistency_report_detects_missing_references \
  tests/modules/academic_records/test_academic_records_service.py::test_get_record_consistency_report_detects_grade_and_field_drift \
  tests/modules/academic_records/test_academic_records_service.py::test_get_record_consistency_report_detects_duplicate_enrollments \
  tests/modules/academic_records/test_router_academic_records.py

echo "[data-layer-gate] admissions applicant and application consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/admissions/test_application_service.py::test_create_application_requires_tenant_scoped_applicant \
  tests/modules/admissions/test_application_service.py::test_create_application_creates_new_stage_application \
  tests/modules/admissions/test_application_service.py::test_list_applications_returns_tenant_scoped_page \
  tests/modules/admissions/test_application_service.py::test_get_tenant_consistency_report_detects_orphaned_links \
  tests/modules/admissions/test_application_service.py::test_get_tenant_consistency_report_detects_applicant_and_application_field_drift \
  tests/modules/admissions/test_application_service.py::test_get_tenant_consistency_report_detects_duplicate_applications \
  tests/modules/admissions/test_router.py

echo "[data-layer-gate] platform plan and quota consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/test_quotas.py::test_plan_quota_consistency_report_detects_missing_keys_and_orphans \
  tests/test_quotas.py::test_platform_quota_consistency_endpoint_returns_detected_issues

echo "[data-layer-gate] workflows runtime consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/modules/workflows/test_workflow_consistency.py

echo "[data-layer-gate] university core graph consistency integrity"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/test_university_core.py::test_university_core_consistency_endpoint_detects_cross_entity_drift

echo "[data-layer-gate] platform persistence and workflow data guarantees"
run_backend_checks pytest -q --no-cov --disable-warnings \
  tests/platform/test_platform_core_uow_fault_injection.py \
  tests/platform/test_platform_context_layer_v1.py \
  tests/platform/test_platform_outbox_events.py \
  tests/platform/test_platform_webhooks_v1.py \
  tests/platform/test_platform_automation_workflow_engine_v1.py \
  tests/platform/test_platform_automation_templates.py \
  tests/platform/test_platform_developer_platform_v1.py \
  tests/platform/test_platform_federation_layer_v1.py

popd >/dev/null

echo "[data-layer-gate] PASS: data layer safety and consistency checks are green"