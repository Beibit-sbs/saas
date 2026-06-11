"""Read-only runtime shell service for Student Success (A-051.5-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_analytics.service import get_student_success_analytics_foundation_contract
from app.modules.student_success_runtime.runtime_shell_schemas import (
    StudentSuccessRuntimeSafety,
    StudentSuccessRuntimeSection,
    StudentSuccessRuntimeShellResponse,
)


REQUIRED_LIMITATIONS = [
    "read_only_runtime",
    "aggregator_only_runtime",
    "tenant_scoped_visibility",
    "summary_read_rbac_required",
    "no_workflow_execution",
    "no_provider_mutation",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _count(values: dict[str, int]) -> int:
    return int(sum(values.values()))


def get_runtime_shell(db: Session, tenant_id: int) -> StudentSuccessRuntimeShellResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)
    analytics_contract = get_student_success_analytics_foundation_contract(tenant)

    applicants = _count(lifecycle["applicant_counts_by_status"])
    students = _count(lifecycle["student_counts_by_status"])
    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    transcripts = _count(lifecycle["transcript_preview_counts"])
    degree_progress = _count(lifecycle["degree_progress_counts"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])

    lifecycle_total = applicants + students + enrollments + transcripts + degree_progress + requests + appeals
    risk_total = degree_progress + interventions + int(lifecycle["human_review_required_count"])
    advisor_total = requests + appeals + interventions
    signal_total = risk_total + int(bool(analytics_contract.get("service_contract_ready")))
    dashboard_total = lifecycle_total + interventions + signal_total

    return StudentSuccessRuntimeShellResponse(
        tenant_id=tenant,
        generated_at=_now(),
        student_success_overview=StudentSuccessRuntimeSection(
            owner_module="student_success_brain",
            records=students,
            source_modules=["student_lifecycle"],
        ),
        lifecycle_summary=StudentSuccessRuntimeSection(
            owner_module="student_lifecycle",
            records=lifecycle_total,
            source_modules=["student_lifecycle"],
        ),
        retention_summary=StudentSuccessRuntimeSection(
            owner_module="student_success_brain",
            records=degree_progress + enrollments,
            source_modules=["student_lifecycle", "student_success_analytics"],
        ),
        risk_summary=StudentSuccessRuntimeSection(
            owner_module="student_success_brain",
            records=risk_total,
            source_modules=["academic_operations", "student_lifecycle", "student_services"],
        ),
        intervention_summary=StudentSuccessRuntimeSection(
            owner_module="student_services",
            records=interventions,
            source_modules=["interventions", "student_lifecycle"],
        ),
        advisor_summary=StudentSuccessRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_total,
            source_modules=["student_services", "interventions"],
        ),
        signal_summary=StudentSuccessRuntimeSection(
            owner_module="student_success_brain",
            records=signal_total,
            source_modules=[
                "academic_operations",
                "student_services",
                "finance",
                "career",
                "alumni",
                "student_success_analytics",
            ],
        ),
        dashboard_summary=StudentSuccessRuntimeSection(
            owner_module="student_success_brain",
            records=dashboard_total,
            source_modules=["student_success_brain", "student_lifecycle", "reporting_runtime"],
        ),
        safety=StudentSuccessRuntimeSafety(
            limitations=list(REQUIRED_LIMITATIONS),
        ),
    )
