"""Read-only Timetable runtime service (A-052.8-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.timetable_runtime_schemas import (
    TimetableCapacityIndicators,
    TimetableInstructorAllocation,
    TimetableRoomUtilization,
    TimetableRuntimeHealth,
    TimetableRuntimeOverview,
    TimetableRuntimeReadiness,
    TimetableRuntimeResponse,
    TimetableRuntimeSection,
    TimetableRuntimeStatistics,
    TimetableScheduleConflicts,
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


def get_timetable_runtime(db: Session, tenant_id: int) -> TimetableRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)
    course_registration_total = len(repository.list_course_registration_metadata(db, tenant))

    terms_total = _sum_status_counts(dashboard_summary["summer_semester_terms"])
    groups_total = _sum_status_counts(dashboard_summary["academic_groups"])
    cohorts_total = _sum_status_counts(dashboard_summary["cohorts"])
    advisor_total = _sum_status_counts(dashboard_summary["advisor_tutor_assignments"])
    retake_total = _sum_status_counts(dashboard_summary["retake_plans"])

    course_sections_total = course_registration_total + groups_total
    schedules_total = course_sections_total + terms_total
    calendar_periods_total = terms_total
    rooms_total = max(1, _bridge_count(bridge_summary, "room", "classroom", "allocation"))
    instructors_total = max(advisor_total, _bridge_count(bridge_summary, "instructor", "faculty", "teaching_load"))
    students_total = max(cohorts_total, course_registration_total)
    conflicts_total = retake_total + _bridge_count(bridge_summary, "conflict", "schedule_conflict")

    utilization_rate = min(100, int((schedules_total * 100) / max(1, rooms_total * 10)))
    overloaded_rooms = max(0, schedules_total - (rooms_total * 8))
    underutilized_rooms = max(0, rooms_total - max(1, schedules_total // 4))

    unassigned_sections = max(0, course_sections_total - instructors_total)
    assigned_instructors = max(0, instructors_total - unassigned_sections)

    conflict_rate = min(100, int((conflicts_total * 100) / max(1, course_sections_total)))
    critical_conflicts = min(conflicts_total, max(0, conflicts_total // 2))

    capacity_alerts_total = max(0, _bridge_count(bridge_summary, "capacity") + overloaded_rooms)
    over_capacity_sections = min(course_sections_total, capacity_alerts_total)
    under_capacity_sections = max(0, underutilized_rooms)

    consistency_score = max(
        0,
        min(
            100,
            100
            - min(60, conflict_rate)
            - min(20, unassigned_sections)
            - min(20, over_capacity_sections),
        ),
    )

    health_issues: list[str] = []
    if conflict_rate > 0:
        health_issues.append("schedule_conflicts_detected")
    if unassigned_sections > 0:
        health_issues.append("unassigned_instructor_slots")
    if over_capacity_sections > 0:
        health_issues.append("capacity_pressure_detected")

    readiness_score = max(0, min(100, consistency_score + min(20, calendar_periods_total) - len(health_issues) * 5))

    return TimetableRuntimeResponse(
        tenant_id=tenant,
        overview=TimetableRuntimeOverview(generated_at=_now()),
        timetable_statistics=TimetableRuntimeStatistics(
            course_sections_total=course_sections_total,
            schedules_total=schedules_total,
            calendar_periods_total=calendar_periods_total,
            rooms_total=rooms_total,
            instructors_total=instructors_total,
            students_total=students_total,
            conflicts_total=conflicts_total,
            capacity_alerts_total=capacity_alerts_total,
            canonical_bridge_total=sum(int(v) for v in bridge_summary.values()),
        ),
        academic_calendar_summary=TimetableRuntimeSection(
            owner_module="academic_calendar",
            records=calendar_periods_total,
            source_modules=["academic_calendar", "scheduling"],
        ),
        room_utilization=TimetableRoomUtilization(
            records=rooms_total,
            utilization_rate=utilization_rate,
            underutilized_rooms=underutilized_rooms,
            overloaded_rooms=overloaded_rooms,
        ),
        instructor_allocation=TimetableInstructorAllocation(
            records=instructors_total,
            assigned_instructors=assigned_instructors,
            unassigned_sections=unassigned_sections,
        ),
        student_schedule_summary=TimetableRuntimeSection(
            owner_module="timetable_management",
            records=students_total,
            source_modules=["scheduling", "student_lifecycle"],
        ),
        schedule_conflicts=TimetableScheduleConflicts(
            records=conflicts_total,
            conflict_rate=conflict_rate,
            critical_conflicts=critical_conflicts,
        ),
        capacity_indicators=TimetableCapacityIndicators(
            records=capacity_alerts_total,
            over_capacity_sections=over_capacity_sections,
            under_capacity_sections=under_capacity_sections,
        ),
        timetable_health=TimetableRuntimeHealth(
            healthy=len(health_issues) == 0,
            consistency_score=consistency_score,
            issues=health_issues,
        ),
        timetable_readiness=TimetableRuntimeReadiness(
            ready_for_runtime=len(health_issues) == 0,
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