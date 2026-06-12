"""Read-only Student Registry runtime service (A-051.6-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_runtime.student_registry_runtime_schemas import (
    StudentRegistryRuntimeResponse,
    StudentRegistryRuntimeSafety,
    StudentRegistryRuntimeSection,
)


REQUIRED_LIMITATIONS = [
    "read_only_runtime",
    "aggregator_only_runtime",
    "tenant_scoped_visibility",
    "summary_read_rbac_required",
    "no_writes",
    "no_workflow_execution",
    "no_approvals",
    "no_background_jobs",
    "no_provider_mutations",
    "no_outbound_calls",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _count(values: dict[str, int]) -> int:
    return int(sum(values.values()))


def get_student_registry_runtime(db: Session, tenant_id: int) -> StudentRegistryRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)

    applicants = _count(lifecycle["applicant_counts_by_status"])
    students = _count(lifecycle["student_counts_by_status"])
    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    transcripts = _count(lifecycle["transcript_preview_counts"])
    degree_progress = _count(lifecycle["degree_progress_counts"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])

    lifecycle_total = applicants + students + enrollments + transcripts + degree_progress + requests + appeals
    student_registry_total = applicants + students
    academic_standing_total = degree_progress + transcripts
    retention_link_total = degree_progress + enrollments
    advisor_link_total = requests + appeals + interventions
    risk_link_total = degree_progress + interventions + int(lifecycle["human_review_required_count"])

    return StudentRegistryRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        student_registry_summary=StudentRegistryRuntimeSection(
            owner_module="student_lifecycle",
            records=student_registry_total,
            source_modules=["student_lifecycle"],
        ),
        enrollment_summary=StudentRegistryRuntimeSection(
            owner_module="student_lifecycle",
            records=enrollments,
            source_modules=["student_lifecycle"],
        ),
        academic_standing_summary=StudentRegistryRuntimeSection(
            owner_module="student_success_brain",
            records=academic_standing_total,
            source_modules=["academic_operations", "student_lifecycle"],
        ),
        retention_link_summary=StudentRegistryRuntimeSection(
            owner_module="student_success_brain",
            records=retention_link_total,
            source_modules=["student_lifecycle", "student_success_analytics"],
        ),
        advisor_link_summary=StudentRegistryRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_link_total,
            source_modules=["student_services", "interventions"],
        ),
        risk_link_summary=StudentRegistryRuntimeSection(
            owner_module="student_success_brain",
            records=risk_link_total,
            source_modules=["academic_operations", "student_services", "student_lifecycle"],
        ),
        lifecycle_status_summary=StudentRegistryRuntimeSection(
            owner_module="student_lifecycle",
            records=lifecycle_total,
            source_modules=["student_lifecycle"],
        ),
        safety=StudentRegistryRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
