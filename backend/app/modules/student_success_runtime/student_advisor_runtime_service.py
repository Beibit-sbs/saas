"""Read-only Student Advisor runtime service (A-051.11-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_runtime.student_advisor_runtime_schemas import (
    StudentAdvisorRuntimeResponse,
    StudentAdvisorRuntimeSafety,
    StudentAdvisorRuntimeSection,
)


REQUIRED_LIMITATIONS = [
    "read_only_runtime",
    "aggregator_only_runtime",
    "deterministic_runtime",
    "tenant_scoped_visibility",
    "summary_read_rbac_required",
    "no_persistence",
    "no_writes",
    "no_intervention_execution",
    "no_workflow_execution",
    "no_approvals",
    "no_background_jobs",
    "no_notifications",
    "no_provider_mutations",
    "no_outbound_integrations",
    "no_scheduling_engine",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _count(values: dict[str, int]) -> int:
    return int(sum(values.values()))


def get_student_advisor_runtime(db: Session, tenant_id: int) -> StudentAdvisorRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)

    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    degree_progress = _count(lifecycle["degree_progress_counts"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])
    human_review_required = int(lifecycle["human_review_required_count"])

    advisor_workload_total = interventions + requests + appeals
    advisor_assignments_total = enrollments + degree_progress
    advisor_queue_total = interventions + human_review_required
    advisor_follow_up_total = requests + appeals + interventions
    advisor_risk_coverage_total = degree_progress + human_review_required + enrollments
    advisor_effectiveness_total = interventions + degree_progress + appeals
    advisor_signal_total = (
        advisor_workload_total
        + advisor_assignments_total
        + advisor_queue_total
        + advisor_follow_up_total
        + advisor_risk_coverage_total
        + advisor_effectiveness_total
    )
    advisor_summary_total = advisor_workload_total + advisor_assignments_total

    return StudentAdvisorRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        advisor_summary=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_summary_total,
            source_modules=["student_lifecycle", "advising", "student_services"],
        ),
        advisor_workload_distribution=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_workload_total,
            source_modules=["advising", "interventions", "student_services"],
        ),
        advisor_student_assignments=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_assignments_total,
            source_modules=["student_lifecycle", "advising"],
        ),
        advisor_intervention_queue=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_queue_total,
            source_modules=["interventions", "student_success_analytics"],
        ),
        advisor_follow_up_summary=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_follow_up_total,
            source_modules=["student_services", "advising", "interventions"],
        ),
        advisor_risk_coverage=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_risk_coverage_total,
            source_modules=["academic_operations", "student_lifecycle", "student_services"],
        ),
        advisor_effectiveness_summary=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_effectiveness_total,
            source_modules=["analytics", "advising", "reporting_runtime"],
        ),
        advisor_signal_summary=StudentAdvisorRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_signal_total,
            source_modules=["brain_core", "analytics", "student_lifecycle"],
        ),
        safety=StudentAdvisorRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
