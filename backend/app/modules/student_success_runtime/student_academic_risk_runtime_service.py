"""Read-only Student Academic Risk runtime service (A-051.8-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_runtime.student_academic_risk_runtime_schemas import (
    StudentAcademicRiskRuntimeResponse,
    StudentAcademicRiskRuntimeSafety,
    StudentAcademicRiskRuntimeSection,
)


REQUIRED_LIMITATIONS = [
    "read_only_runtime",
    "aggregator_only_runtime",
    "deterministic_runtime",
    "tenant_scoped_visibility",
    "summary_read_rbac_required",
    "no_writes",
    "no_workflow_execution",
    "no_approvals",
    "no_background_jobs",
    "no_provider_mutations",
    "no_outbound_integrations",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _count(values: dict[str, int]) -> int:
    return int(sum(values.values()))


def get_student_academic_risk_runtime(db: Session, tenant_id: int) -> StudentAcademicRiskRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)

    degree_progress = _count(lifecycle["degree_progress_counts"])
    transcripts = _count(lifecycle["transcript_preview_counts"])
    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])
    human_review_required = int(lifecycle["human_review_required_count"])

    gpa_risk_total = transcripts + human_review_required
    failed_course_risk_total = degree_progress + requests
    low_performance_total = degree_progress + transcripts
    probation_total = appeals + human_review_required
    progression_risk_total = degree_progress + enrollments
    academic_alert_total = interventions + human_review_required + requests
    academic_signal_total = (
        gpa_risk_total
        + failed_course_risk_total
        + low_performance_total
        + probation_total
        + progression_risk_total
        + academic_alert_total
    )
    academic_risk_total = (
        gpa_risk_total
        + failed_course_risk_total
        + low_performance_total
        + probation_total
    )

    return StudentAcademicRiskRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        academic_risk_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=academic_risk_total,
            source_modules=["student_lifecycle", "academic_operations"],
        ),
        gpa_risk_distribution=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=gpa_risk_total,
            source_modules=["student_lifecycle", "academic_operations"],
        ),
        failed_course_risk_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=failed_course_risk_total,
            source_modules=["student_lifecycle", "degree_progress"],
        ),
        low_performance_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=low_performance_total,
            source_modules=["academic_operations", "student_lifecycle"],
        ),
        probation_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=probation_total,
            source_modules=["student_services", "student_lifecycle"],
        ),
        progression_risk_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=progression_risk_total,
            source_modules=["degree_progress", "student_lifecycle"],
        ),
        academic_alert_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=academic_alert_total,
            source_modules=["interventions", "student_services", "advising"],
        ),
        academic_signal_summary=StudentAcademicRiskRuntimeSection(
            owner_module="student_success_brain",
            records=academic_signal_total,
            source_modules=["brain_core", "analytics", "student_lifecycle"],
        ),
        safety=StudentAcademicRiskRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
