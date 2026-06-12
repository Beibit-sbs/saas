"""Read-only Student Success Dashboard runtime service (A-051.13-E1)."""

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
from app.modules.student_success_runtime.student_success_dashboard_runtime_schemas import (
    StudentSuccessDashboardRuntimeResponse,
    StudentSuccessDashboardRuntimeSafety,
    StudentSuccessDashboardRuntimeSection,
)
from app.modules.student_success_runtime.student_success_runtime_shell_service import get_runtime_shell
from app.modules.student_success_runtime.student_success_signals_runtime_service import get_student_success_signals_runtime


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
]


def _now() -> datetime:
    return datetime.now(UTC)


def get_student_success_dashboard_runtime(db: Session, tenant_id: int) -> StudentSuccessDashboardRuntimeResponse:
    tenant = validate_tenant_id_provided(tenant_id)

    runtime_shell = get_runtime_shell(db, tenant)
    registry = get_student_registry_runtime(db, tenant)
    retention = get_student_retention_runtime(db, tenant)
    academic = get_student_academic_risk_runtime(db, tenant)
    attendance = get_student_attendance_risk_runtime(db, tenant)
    intervention = get_student_intervention_runtime(db, tenant)
    advisor = get_student_advisor_runtime(db, tenant)
    signals = get_student_success_signals_runtime(db, tenant)

    executive_summary_total = (
        int(runtime_shell.student_success_overview.records)
        + int(runtime_shell.dashboard_summary.records)
        + int(signals.success_signal_summary.records)
    )
    student_population_total = (
        int(registry.student_registry_summary.records)
        + int(registry.enrollment_summary.records)
        + int(registry.lifecycle_status_summary.records)
    )
    retention_overview_total = (
        int(retention.retention_summary.records)
        + int(retention.dropout_risk_summary.records)
        + int(retention.retention_signal_summary.records)
    )
    academic_risk_overview_total = (
        int(academic.academic_risk_summary.records)
        + int(academic.academic_alert_summary.records)
        + int(academic.academic_signal_summary.records)
    )
    attendance_risk_overview_total = (
        int(attendance.attendance_risk_summary.records)
        + int(attendance.chronic_absence_summary.records)
        + int(attendance.attendance_signal_summary.records)
    )
    intervention_overview_total = (
        int(intervention.intervention_summary.records)
        + int(intervention.intervention_priority_groups.records)
        + int(intervention.intervention_signal_summary.records)
    )
    advisor_overview_total = (
        int(advisor.advisor_summary.records)
        + int(advisor.advisor_intervention_queue.records)
        + int(advisor.advisor_signal_summary.records)
    )
    success_signals_total = int(signals.success_signal_summary.records)
    priority_actions_total = (
        int(signals.early_warning_signals.records)
        + int(intervention.intervention_priority_groups.records)
        + int(advisor.advisor_intervention_queue.records)
    )
    dashboard_kpis_total = (
        executive_summary_total
        + retention_overview_total
        + academic_risk_overview_total
        + attendance_risk_overview_total
        + intervention_overview_total
        + advisor_overview_total
        + success_signals_total
    )

    return StudentSuccessDashboardRuntimeResponse(
        tenant_id=tenant,
        generated_at=_now(),
        executive_summary=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=executive_summary_total,
            source_modules=["student_success_runtime_shell", "student_success_signals_runtime", "reporting_runtime"],
        ),
        student_population=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=student_population_total,
            source_modules=["student_registry_runtime", "student_lifecycle"],
        ),
        retention_overview=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=retention_overview_total,
            source_modules=["student_retention_runtime", "student_success_analytics"],
        ),
        academic_risk_overview=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=academic_risk_overview_total,
            source_modules=["student_academic_risk_runtime", "academic_operations"],
        ),
        attendance_risk_overview=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=attendance_risk_overview_total,
            source_modules=["student_attendance_risk_runtime", "attendance_tracking"],
        ),
        intervention_overview=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=intervention_overview_total,
            source_modules=["student_intervention_runtime", "interventions"],
        ),
        advisor_overview=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=advisor_overview_total,
            source_modules=["student_advisor_runtime", "advising"],
        ),
        success_signals=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=success_signals_total,
            source_modules=["student_success_signals_runtime", "student_success_analytics"],
        ),
        priority_actions=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=priority_actions_total,
            source_modules=["student_success_signals_runtime", "student_intervention_runtime", "student_advisor_runtime"],
        ),
        dashboard_kpis=StudentSuccessDashboardRuntimeSection(
            owner_module="student_success_brain",
            records=dashboard_kpis_total,
            source_modules=["student_success_runtime_shell", "student_success_signals_runtime", "reporting_runtime"],
        ),
        safety=StudentSuccessDashboardRuntimeSafety(limitations=list(REQUIRED_LIMITATIONS)),
    )
