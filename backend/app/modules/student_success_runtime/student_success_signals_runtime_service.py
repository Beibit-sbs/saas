"""Read-only Student Success Signals runtime service (A-051.12-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.student_success_runtime.student_academic_risk_runtime_service import get_student_academic_risk_runtime
from app.modules.student_success_runtime.student_advisor_runtime_service import get_student_advisor_runtime
from app.modules.student_success_runtime.student_attendance_risk_runtime_service import get_student_attendance_risk_runtime
from app.modules.student_success_runtime.student_intervention_runtime_service import get_student_intervention_runtime
from app.modules.student_success_runtime.student_registry_runtime_service import get_student_registry_runtime
from app.modules.student_success_runtime.student_retention_runtime_service import get_student_retention_runtime
from app.modules.student_success_runtime.student_success_runtime_shell_service import get_runtime_shell
from app.modules.student_success_runtime.student_success_signals_runtime_schemas import (
    StudentSuccessSignalsRuntimeResponse,
    StudentSuccessSignalsRuntimeSafety,
    StudentSuccessSignalsRuntimeSection,
)


REQUIRED_LIMITATIONS = [
    "read_only_runtime",
    "aggregator_only_runtime",
    "deterministic_runtime",
    "tenant_scoped_visibility",
    "summary_read_rbac_required",
    "no_persistence",
    "no_writes",
    "no_workflow_execution",
    "no_approvals",
    "no_background_jobs",
    "no_notifications",
    "no_provider_mutations",
    "no_outbound_integrations",
    "no_scheduling_engine",
    "no_signal_execution_engine",
]


def _now() -> datetime:
    return datetime.now(UTC)


def get_student_success_signals_runtime(db: Session, tenant_id: int) -> StudentSuccessSignalsRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)

    runtime_shell = get_runtime_shell(db, tenant)
    student_registry = get_student_registry_runtime(db, tenant)
    retention = get_student_retention_runtime(db, tenant)
    academic = get_student_academic_risk_runtime(db, tenant)
    attendance = get_student_attendance_risk_runtime(db, tenant)
    intervention = get_student_intervention_runtime(db, tenant)
    advisor = get_student_advisor_runtime(db, tenant)

    retention_signals_total = int(retention.retention_signal_summary.records)
    academic_signals_total = int(academic.academic_signal_summary.records)
    attendance_signals_total = int(attendance.attendance_signal_summary.records)
    intervention_signals_total = int(intervention.intervention_signal_summary.records)
    advisor_signals_total = int(advisor.advisor_signal_summary.records)

    early_warning_total = (
        int(retention.dropout_risk_summary.records)
        + int(academic.academic_alert_summary.records)
        + int(attendance.chronic_absence_summary.records)
        + int(intervention.intervention_priority_groups.records)
        + int(advisor.advisor_intervention_queue.records)
    )

    success_indicator_total = (
        int(runtime_shell.dashboard_summary.records)
        + int(student_registry.lifecycle_status_summary.records)
        + int(retention.persistence_summary.records)
        + int(academic.progression_risk_summary.records)
        + int(attendance.engagement_attendance_summary.records)
        + int(intervention.intervention_effectiveness_signals.records)
        + int(advisor.advisor_effectiveness_summary.records)
    )

    signal_trend_total = (
        int(retention.retention_trend_summary.records)
        + int(attendance.attendance_trend_summary.records)
        + int(academic.academic_signal_summary.records)
        + int(advisor.advisor_signal_summary.records)
    )

    signal_scorecard_total = (
        retention_signals_total
        + academic_signals_total
        + attendance_signals_total
        + intervention_signals_total
        + advisor_signals_total
        + early_warning_total
        + success_indicator_total
        + signal_trend_total
    )

    success_signal_summary_total = (
        retention_signals_total
        + academic_signals_total
        + attendance_signals_total
        + intervention_signals_total
        + advisor_signals_total
    )

    return StudentSuccessSignalsRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        success_signal_summary=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=success_signal_summary_total,
            source_modules=["student_success_runtime", "student_success_analytics", "brain_core"],
        ),
        retention_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=retention_signals_total,
            source_modules=["student_retention_runtime", "student_success_analytics"],
        ),
        academic_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=academic_signals_total,
            source_modules=["student_academic_risk_runtime", "academic_operations"],
        ),
        attendance_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=attendance_signals_total,
            source_modules=["student_attendance_risk_runtime", "attendance_tracking"],
        ),
        intervention_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_signals_total,
            source_modules=["student_intervention_runtime", "interventions"],
        ),
        advisor_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_signals_total,
            source_modules=["student_advisor_runtime", "advising"],
        ),
        early_warning_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=early_warning_total,
            source_modules=[
                "student_retention_runtime",
                "student_academic_risk_runtime",
                "student_attendance_risk_runtime",
                "student_intervention_runtime",
                "student_advisor_runtime",
            ],
        ),
        success_indicator_signals=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=success_indicator_total,
            source_modules=[
                "student_success_runtime_shell",
                "student_registry_runtime",
                "student_retention_runtime",
                "student_academic_risk_runtime",
                "student_attendance_risk_runtime",
                "student_intervention_runtime",
                "student_advisor_runtime",
            ],
        ),
        signal_trend_summary=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=signal_trend_total,
            source_modules=[
                "student_retention_runtime",
                "student_attendance_risk_runtime",
                "student_academic_risk_runtime",
                "student_advisor_runtime",
                "reporting_runtime",
            ],
        ),
        signal_scorecard=StudentSuccessSignalsRuntimeSection(
            owner_module="student_success_brain",
            records=signal_scorecard_total,
            source_modules=["student_success_runtime", "student_success_analytics", "reporting_runtime"],
        ),
        safety=StudentSuccessSignalsRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
