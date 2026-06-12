"""Read-only Student Intervention runtime service (A-051.10-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_runtime.student_intervention_runtime_schemas import (
    StudentInterventionRuntimeResponse,
    StudentInterventionRuntimeSafety,
    StudentInterventionRuntimeSection,
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
    "no_notifications",
    "no_provider_mutations",
    "no_outbound_integrations",
    "no_intervention_execution",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _count(values: dict[str, int]) -> int:
    return int(sum(values.values()))


def get_student_intervention_runtime(db: Session, tenant_id: int) -> StudentInterventionRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)

    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    degree_progress = _count(lifecycle["degree_progress_counts"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])
    transcripts = _count(lifecycle["transcript_preview_counts"])
    human_review_required = int(lifecycle["human_review_required_count"])

    intervention_priority_total = human_review_required + interventions + requests
    intervention_recommendation_total = degree_progress + transcripts + requests
    advisor_interventions_total = interventions + requests + appeals
    dean_interventions_total = human_review_required + appeals + degree_progress
    support_programs_total = enrollments + requests + appeals
    intervention_effectiveness_total = interventions + degree_progress + enrollments
    intervention_signal_total = (
        intervention_priority_total
        + intervention_recommendation_total
        + advisor_interventions_total
        + dean_interventions_total
        + support_programs_total
        + intervention_effectiveness_total
    )
    intervention_summary_total = intervention_priority_total + intervention_recommendation_total

    return StudentInterventionRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        intervention_summary=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_summary_total,
            source_modules=["student_lifecycle", "student_services"],
        ),
        intervention_priority_groups=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_priority_total,
            source_modules=["student_lifecycle", "student_success_analytics"],
        ),
        intervention_recommendations=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_recommendation_total,
            source_modules=["academic_operations", "student_lifecycle", "student_services"],
        ),
        advisor_interventions=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_interventions_total,
            source_modules=["advising", "student_services", "interventions"],
        ),
        dean_interventions=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=dean_interventions_total,
            source_modules=["academic_operations", "student_services", "advising"],
        ),
        support_programs=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=support_programs_total,
            source_modules=["student_services", "career_services", "financial_aid"],
        ),
        intervention_effectiveness_signals=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_effectiveness_total,
            source_modules=["analytics", "student_services", "reporting_runtime"],
        ),
        intervention_signal_summary=StudentInterventionRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_signal_total,
            source_modules=["brain_core", "analytics", "student_lifecycle"],
        ),
        safety=StudentInterventionRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
