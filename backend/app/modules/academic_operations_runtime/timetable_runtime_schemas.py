"""Schemas for Timetable runtime (A-052.8-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TimetableRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "TIMETABLE_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class TimetableRuntimeStatistics(BaseModel):
    course_sections_total: int = 0
    schedules_total: int = 0
    calendar_periods_total: int = 0
    rooms_total: int = 0
    instructors_total: int = 0
    students_total: int = 0
    conflicts_total: int = 0
    capacity_alerts_total: int = 0
    canonical_bridge_total: int = 0


class TimetableRuntimeSection(BaseModel):
    owner_module: str = "scheduling"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class TimetableRoomUtilization(BaseModel):
    records: int = 0
    utilization_rate: int = 0
    underutilized_rooms: int = 0
    overloaded_rooms: int = 0
    read_only: bool = True


class TimetableInstructorAllocation(BaseModel):
    records: int = 0
    assigned_instructors: int = 0
    unassigned_sections: int = 0
    read_only: bool = True


class TimetableScheduleConflicts(BaseModel):
    records: int = 0
    conflict_rate: int = 0
    critical_conflicts: int = 0
    read_only: bool = True


class TimetableCapacityIndicators(BaseModel):
    records: int = 0
    over_capacity_sections: int = 0
    under_capacity_sections: int = 0
    read_only: bool = True


class TimetableRuntimeHealth(BaseModel):
    healthy: bool = True
    consistency_score: int = 0
    issues: list[str] = Field(default_factory=list)


class TimetableRuntimeReadiness(BaseModel):
    ready_for_runtime: bool = False
    checklist: list[str] = Field(default_factory=list)
    readiness_score: int = 0


class TimetableRuntimeResponse(BaseModel):
    tenant_id: int
    overview: TimetableRuntimeOverview
    timetable_statistics: TimetableRuntimeStatistics
    academic_calendar_summary: TimetableRuntimeSection
    room_utilization: TimetableRoomUtilization
    instructor_allocation: TimetableInstructorAllocation
    student_schedule_summary: TimetableRuntimeSection
    schedule_conflicts: TimetableScheduleConflicts
    capacity_indicators: TimetableCapacityIndicators
    timetable_health: TimetableRuntimeHealth
    timetable_readiness: TimetableRuntimeReadiness