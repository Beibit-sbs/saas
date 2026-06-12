"""Read-only Student Attendance Risk runtime service (A-051.9-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_lifecycle import repository as student_lifecycle_repository
from app.modules.student_success_runtime.student_attendance_risk_runtime_schemas import (
    StudentAttendanceRiskRuntimeResponse,
    StudentAttendanceRiskRuntimeSafety,
    StudentAttendanceRiskRuntimeSection,
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


def get_student_attendance_risk_runtime(db: Session, tenant_id: int) -> StudentAttendanceRiskRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)
    lifecycle = student_lifecycle_repository.compute_student_lifecycle_dashboard_summary(db, tenant)

    enrollments = _count(lifecycle["enrollment_counts_by_status"])
    requests = _count(lifecycle["request_counts_by_status"])
    appeals = _count(lifecycle["appeal_counts_by_status"])
    interventions = _count(lifecycle["intervention_counts_by_status"])
    degree_progress = _count(lifecycle["degree_progress_counts"])
    human_review_required = int(lifecycle["human_review_required_count"])

    absence_distribution_total = enrollments + human_review_required
    chronic_absence_total = interventions + requests
    missed_class_total = degree_progress + requests
    attendance_trend_total = enrollments + interventions
    punctuality_total = appeals + human_review_required
    engagement_attendance_total = degree_progress + interventions + appeals
    attendance_signal_total = (
        absence_distribution_total
        + chronic_absence_total
        + missed_class_total
        + attendance_trend_total
        + punctuality_total
        + engagement_attendance_total
    )
    attendance_risk_total = (
        absence_distribution_total
        + chronic_absence_total
        + missed_class_total
        + attendance_trend_total
    )

    return StudentAttendanceRiskRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        attendance_risk_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=attendance_risk_total,
            source_modules=["student_lifecycle", "academic_operations"],
        ),
        absence_distribution=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=absence_distribution_total,
            source_modules=["student_lifecycle", "attendance_tracking"],
        ),
        chronic_absence_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=chronic_absence_total,
            source_modules=["student_services", "interventions"],
        ),
        missed_class_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=missed_class_total,
            source_modules=["academic_operations", "student_lifecycle"],
        ),
        attendance_trend_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=attendance_trend_total,
            source_modules=["student_lifecycle", "reporting_runtime"],
        ),
        punctuality_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=punctuality_total,
            source_modules=["academic_operations", "student_services"],
        ),
        engagement_attendance_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=engagement_attendance_total,
            source_modules=["student_lifecycle", "interventions", "advising"],
        ),
        attendance_signal_summary=StudentAttendanceRiskRuntimeSection(
            owner_module="student_success_brain",
            records=attendance_signal_total,
            source_modules=["brain_core", "analytics", "student_lifecycle"],
        ),
        safety=StudentAttendanceRiskRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
