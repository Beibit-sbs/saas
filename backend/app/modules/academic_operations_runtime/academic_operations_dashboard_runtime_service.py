"""Read-only Academic Operations Dashboard runtime service (A-052.14-E1)."""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean

from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.academic_operations_dashboard_runtime_schemas import (
    AcademicOperationsDashboardHealthScore,
    AcademicOperationsDashboardKpiSummary,
    AcademicOperationsDashboardPriorityItem,
    AcademicOperationsDashboardRecommendedAction,
    AcademicOperationsDashboardRuntimeOverview,
    AcademicOperationsDashboardRuntimeResponse,
    AcademicOperationsDashboardSummarySection,
)
from app.modules.academic_operations_runtime.academic_operations_runtime_shell_service import get_runtime_shell
from app.modules.academic_operations_runtime.academic_operations_signals_runtime_service import (
    get_academic_operations_signals_runtime,
)
from app.modules.academic_operations_runtime.academic_registry_runtime_service import get_academic_registry_runtime
from app.modules.academic_operations_runtime.assessment_runtime_service import get_assessment_runtime
from app.modules.academic_operations_runtime.attendance_runtime_service import get_attendance_runtime
from app.modules.academic_operations_runtime.curriculum_runtime_service import get_curriculum_runtime
from app.modules.academic_operations_runtime.internship_runtime_service import get_internship_runtime
from app.modules.academic_operations_runtime.teaching_load_runtime_service import get_teaching_load_runtime
from app.modules.academic_operations_runtime.timetable_runtime_service import get_timetable_runtime


def _now() -> datetime:
    return datetime.now(UTC)


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _classification(score: int) -> str:
    if score >= 75:
        return "HEALTHY"
    if score >= 50:
        return "WATCH"
    return "CRITICAL"


def _summary_section(records: int, source_modules: list[str]) -> AcademicOperationsDashboardSummarySection:
    return AcademicOperationsDashboardSummarySection(records=records, source_modules=source_modules)


def get_academic_operations_dashboard_runtime(db: Session, tenant_id: int) -> AcademicOperationsDashboardRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    runtime_shell = get_runtime_shell(db, tenant)
    registry = get_academic_registry_runtime(db, tenant)
    curriculum = get_curriculum_runtime(db, tenant)
    timetable = get_timetable_runtime(db, tenant)
    attendance = get_attendance_runtime(db, tenant)
    assessment = get_assessment_runtime(db, tenant)
    teaching_load = get_teaching_load_runtime(db, tenant)
    internship = get_internship_runtime(db, tenant)
    signals = get_academic_operations_signals_runtime(db, tenant)

    registry_records = (
        registry.registry_statistics.academic_periods_total
        + registry.registry_statistics.academic_groups_total
        + registry.registry_statistics.curriculum_registry_total
        + registry.registry_statistics.student_registry_linkage_total
    )
    curriculum_records = (
        curriculum.curriculum_statistics.program_structures_total
        + curriculum.curriculum_statistics.curriculum_versions_total
        + curriculum.curriculum_statistics.learning_outcomes_total
        + curriculum.curriculum_statistics.prerequisite_chains_total
    )
    timetable_records = (
        timetable.timetable_statistics.course_sections_total
        + timetable.timetable_statistics.schedules_total
        + timetable.timetable_statistics.conflicts_total
    )
    attendance_records = (
        attendance.attendance_statistics.tracked_students_total
        + attendance.attendance_statistics.at_risk_students_total
        + attendance.attendance_statistics.intervention_candidates_total
    )
    assessment_records = (
        assessment.assessment_statistics.exams_total
        + assessment.assessment_statistics.completed_exams_total
        + assessment.assessment_statistics.assessment_signals_total
    )
    teaching_load_records = (
        teaching_load.teaching_load_statistics.tracked_faculty_total
        + teaching_load.teaching_load_statistics.high_risk_assignments_total
        + teaching_load.faculty_workload_distribution.fairness_alert_total
    )
    internship_records = (
        internship.internship_statistics.total_internships
        + internship.internship_statistics.active_internships
        + internship.internship_risk_summary.high_risk_count
    )
    signals_records = (
        signals.signal_summary.total_signals
        + signals.signal_summary.high_priority_total
        + len(signals.recommended_actions)
    )

    aggregated_records_total = (
        runtime_shell.runtime_shell_runtime.records
        + registry_records
        + curriculum_records
        + timetable_records
        + attendance_records
        + assessment_records
        + teaching_load_records
        + internship_records
        + signals_records
    )

    priority_source = signals.high_priority_signals.items or signals.medium_priority_signals.items
    high_priority_items = [
        AcademicOperationsDashboardPriorityItem(
            item_id=item.signal_id,
            title=item.signal_name,
            priority=item.severity,
            status=item.status,
            score=item.score,
            domain="signals",
            source_signal_ids=[item.signal_id],
        )
        for item in priority_source[:10]
    ]

    recommended_actions = [
        AcademicOperationsDashboardRecommendedAction(
            action_id=action.action_id,
            title=action.title,
            priority=action.priority,
            rationale=action.rationale,
            source_signal_ids=list(action.source_signal_ids),
        )
        for action in signals.recommended_actions
    ]

    domain_health_scores = [
        registry.health.consistency_score,
        curriculum.curriculum_health.consistency_score,
        timetable.timetable_health.consistency_score,
        100 - attendance.attendance_risk_summary.risk_score,
        100 - assessment.assessment_risk_summary.risk_score,
        100 - max(teaching_load.overload_risk_summary.risk_score, teaching_load.coverage_risk_summary.risk_score),
        internship.internship_readiness.readiness_score,
        signals.health_score.composite_score,
    ]
    composite_score = _clamp_score(mean(domain_health_scores))

    return AcademicOperationsDashboardRuntimeResponse(
        tenant_id=tenant,
        overview=AcademicOperationsDashboardRuntimeOverview(generated_at=_now()),
        kpi_summary=AcademicOperationsDashboardKpiSummary(
            runtime_slice_count=9,
            aggregated_records_total=aggregated_records_total,
            high_priority_total=signals.signal_summary.high_priority_total,
            recommended_actions_total=len(recommended_actions),
        ),
        registry_summary=_summary_section(
            registry_records,
            ["academic_operations_runtime_shell", "academic_registry_runtime"],
        ),
        curriculum_summary=_summary_section(
            curriculum_records,
            ["curriculum_runtime", "course_catalog_management", "prerequisite_management"],
        ),
        timetable_summary=_summary_section(
            timetable_records,
            ["timetable_runtime", "scheduling"],
        ),
        attendance_summary=_summary_section(
            attendance_records,
            ["attendance_runtime", "attendance"],
        ),
        assessment_summary=_summary_section(
            assessment_records,
            ["assessment_runtime", "grades", "exam_governance"],
        ),
        teaching_load_summary=_summary_section(
            teaching_load_records,
            ["teaching_load_runtime", "faculty", "teaching_load_contracts"],
        ),
        internship_summary=_summary_section(
            internship_records,
            ["internship_runtime", "internship"],
        ),
        signals_summary=_summary_section(
            signals_records,
            ["academic_operations_signals_runtime", "brain_core"],
        ),
        high_priority_items=high_priority_items,
        recommended_actions=recommended_actions,
        academic_operations_health_score=AcademicOperationsDashboardHealthScore(
            composite_score=composite_score,
            classification=_classification(composite_score),
            contributing_factors=[
                f"registry_consistency={registry.health.consistency_score}",
                f"curriculum_consistency={curriculum.curriculum_health.consistency_score}",
                f"timetable_consistency={timetable.timetable_health.consistency_score}",
                f"attendance_risk={attendance.attendance_risk_summary.risk_score}",
                f"assessment_risk={assessment.assessment_risk_summary.risk_score}",
                f"teaching_load_risk={max(teaching_load.overload_risk_summary.risk_score, teaching_load.coverage_risk_summary.risk_score)}",
                f"internship_readiness={internship.internship_readiness.readiness_score}",
                f"signals_health={signals.health_score.composite_score}",
            ],
        ),
    )
