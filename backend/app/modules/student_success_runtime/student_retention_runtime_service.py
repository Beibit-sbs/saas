"""Read-only Student Retention runtime service (A-051.7-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_runtime.student_retention_runtime_schemas import (
    StudentRetentionRuntimeResponse,
    StudentRetentionRuntimeSafety,
    StudentRetentionRuntimeSection,
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
    "no_outbound_providers",
    "no_external_integrations",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _count(values: dict[str, int]) -> int:
    return int(sum(values.values()))


def get_student_retention_runtime(db: Session, tenant_id: int) -> StudentRetentionRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)

    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    degree_progress = _count(lifecycle["degree_progress_counts"])
    transcripts = _count(lifecycle["transcript_preview_counts"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])

    retention_summary_total = enrollments + degree_progress
    retention_score_distribution_total = degree_progress + transcripts
    retention_risk_distribution_total = degree_progress + int(lifecycle["human_review_required_count"])
    dropout_risk_total = retention_risk_distribution_total + interventions
    persistence_total = enrollments + requests + appeals
    retention_trend_total = degree_progress + enrollments + interventions
    cohort_retention_total = enrollments + transcripts
    retention_signal_total = dropout_risk_total + persistence_total + interventions

    return StudentRetentionRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        retention_summary=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=retention_summary_total,
            source_modules=["student_lifecycle", "student_success_analytics"],
        ),
        retention_score_distribution=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=retention_score_distribution_total,
            source_modules=["student_lifecycle", "academic_operations"],
        ),
        retention_risk_distribution=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=retention_risk_distribution_total,
            source_modules=["student_lifecycle", "student_services"],
        ),
        dropout_risk_summary=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=dropout_risk_total,
            source_modules=["academic_operations", "student_services", "interventions"],
        ),
        persistence_summary=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=persistence_total,
            source_modules=["student_lifecycle", "student_services"],
        ),
        retention_trend_summary=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=retention_trend_total,
            source_modules=["student_lifecycle", "interventions", "reporting_runtime"],
        ),
        cohort_retention_summary=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=cohort_retention_total,
            source_modules=["student_lifecycle"],
        ),
        retention_signal_summary=StudentRetentionRuntimeSection(
            owner_module="student_success_brain",
            records=retention_signal_total,
            source_modules=["academic_operations", "student_services", "finance", "career", "alumni"],
        ),
        safety=StudentRetentionRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
