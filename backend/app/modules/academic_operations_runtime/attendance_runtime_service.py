"""Read-only Attendance runtime service (A-052.9-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.attendance_runtime_schemas import (
    AttendanceDistribution,
    AttendanceReadiness,
    AttendanceRiskSummary,
    AttendanceRuntimeOverview,
    AttendanceRuntimeResponse,
    AttendanceRuntimeStatistics,
    AttendanceSection,
    AttendanceSignals,
    AttendanceTrends,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _sum_status_counts(payload: dict[str, int]) -> int:
    return sum(int(v) for v in payload.values())


def _bridge_count(bridge_summary: dict[str, int], *tokens: str) -> int:
    lowered = tuple(token.lower() for token in tokens)
    total = 0
    for key, value in bridge_summary.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in lowered):
            total += int(value)
    return total


def get_attendance_runtime(db: Session, tenant_id: int) -> AttendanceRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)
    course_registration_total = len(repository.list_course_registration_metadata(db, tenant))

    cohorts_total = _sum_status_counts(dashboard_summary["cohorts"])
    groups_total = _sum_status_counts(dashboard_summary["academic_groups"])
    gradebook_total = _sum_status_counts(dashboard_summary["gradebook_metadata"])
    advisor_total = _sum_status_counts(dashboard_summary["advisor_tutor_assignments"])
    retake_total = _sum_status_counts(dashboard_summary["retake_plans"])

    tracked_students_total = max(cohorts_total, course_registration_total)
    tracked_courses_total = max(gradebook_total, groups_total)

    excellent_band = min(tracked_students_total, max(0, tracked_students_total // 3))
    good_band = min(tracked_students_total - excellent_band, max(0, tracked_students_total // 3))
    warning_band = min(
        tracked_students_total - excellent_band - good_band,
        max(0, tracked_students_total // 5 + retake_total),
    )
    critical_band = max(0, tracked_students_total - excellent_band - good_band - warning_band)

    at_risk_students_total = warning_band + critical_band
    intervention_candidates_total = max(0, critical_band + min(warning_band, advisor_total))

    improving_count = max(0, good_band // 2)
    stable_count = max(0, excellent_band + (good_band - improving_count))
    declining_count = max(0, at_risk_students_total)

    average_attendance_rate = max(0, min(100, 100 - (declining_count * 100 // max(1, tracked_students_total))))
    trend_score = max(0, min(100, 60 + improving_count - declining_count))

    attendance_bridge_count = _bridge_count(bridge_summary, "attendance")
    signal_count = max(attendance_bridge_count, declining_count + retake_total)
    signal_types: list[str] = []
    if warning_band > 0:
        signal_types.append("warning_attendance_drop")
    if critical_band > 0:
        signal_types.append("critical_attendance_risk")
    if improving_count > 0:
        signal_types.append("attendance_recovery")

    primary_risks: list[str] = []
    if critical_band > 0:
        primary_risks.append("critical_absence_population")
    if declining_count > improving_count:
        primary_risks.append("declining_attendance_trend")
    if intervention_candidates_total > 0:
        primary_risks.append("intervention_backlog")

    risk_score = max(0, min(100, critical_band * 12 + warning_band * 5 + max(0, declining_count - improving_count) * 4))
    open_risks = len(primary_risks)

    readiness_score = max(0, min(100, 100 - risk_score + min(20, attendance_bridge_count)))

    return AttendanceRuntimeResponse(
        tenant_id=tenant,
        overview=AttendanceRuntimeOverview(generated_at=_now()),
        attendance_statistics=AttendanceRuntimeStatistics(
            tracked_students_total=tracked_students_total,
            tracked_courses_total=tracked_courses_total,
            average_attendance_rate=average_attendance_rate,
            at_risk_students_total=at_risk_students_total,
            intervention_candidates_total=intervention_candidates_total,
            trend_windows_total=3,
            canonical_bridge_total=sum(int(v) for v in bridge_summary.values()),
        ),
        attendance_distribution=AttendanceDistribution(
            excellent_band=excellent_band,
            good_band=good_band,
            warning_band=warning_band,
            critical_band=critical_band,
        ),
        attendance_trends=AttendanceTrends(
            improving_count=improving_count,
            stable_count=stable_count,
            declining_count=declining_count,
            trend_score=trend_score,
        ),
        attendance_risk_summary=AttendanceRiskSummary(
            risk_score=risk_score,
            open_risks=open_risks,
            primary_risks=primary_risks,
        ),
        high_risk_population=AttendanceSection(
            records=at_risk_students_total,
            source_modules=["attendance", "attendance_tracking", "scheduling"],
        ),
        course_attendance_health=AttendanceSection(
            records=tracked_courses_total,
            source_modules=["attendance", "scheduling", "academic_operations"],
        ),
        attendance_intervention_candidates=AttendanceSection(
            records=intervention_candidates_total,
            source_modules=["attendance_tracking", "academic_operations"],
        ),
        attendance_signals=AttendanceSignals(
            generated_signals=signal_count,
            signal_types=signal_types,
        ),
        attendance_readiness=AttendanceReadiness(
            ready_for_runtime=open_risks == 0,
            checklist=[
                "read_only_runtime",
                "aggregator_only_runtime",
                "tenant_scoped_visibility",
                "summary_read_rbac_required",
                "no_mutation_operations",
            ],
            readiness_score=readiness_score,
        ),
    )
