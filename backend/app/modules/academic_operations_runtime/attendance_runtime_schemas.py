"""Schemas for Attendance runtime (A-052.9-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AttendanceRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "ATTENDANCE_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class AttendanceRuntimeStatistics(BaseModel):
    tracked_students_total: int = 0
    tracked_courses_total: int = 0
    average_attendance_rate: int = 0
    at_risk_students_total: int = 0
    intervention_candidates_total: int = 0
    trend_windows_total: int = 0
    canonical_bridge_total: int = 0


class AttendanceDistribution(BaseModel):
    excellent_band: int = 0
    good_band: int = 0
    warning_band: int = 0
    critical_band: int = 0
    read_only: bool = True


class AttendanceTrends(BaseModel):
    improving_count: int = 0
    stable_count: int = 0
    declining_count: int = 0
    trend_score: int = 0
    read_only: bool = True


class AttendanceRiskSummary(BaseModel):
    risk_score: int = 0
    open_risks: int = 0
    primary_risks: list[str] = Field(default_factory=list)
    read_only: bool = True


class AttendanceSection(BaseModel):
    owner_module: str = "attendance"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class AttendanceSignals(BaseModel):
    generated_signals: int = 0
    signal_types: list[str] = Field(default_factory=list)
    read_only: bool = True


class AttendanceReadiness(BaseModel):
    ready_for_runtime: bool = False
    checklist: list[str] = Field(default_factory=list)
    readiness_score: int = 0


class AttendanceRuntimeResponse(BaseModel):
    tenant_id: int
    overview: AttendanceRuntimeOverview
    attendance_statistics: AttendanceRuntimeStatistics
    attendance_distribution: AttendanceDistribution
    attendance_trends: AttendanceTrends
    attendance_risk_summary: AttendanceRiskSummary
    high_risk_population: AttendanceSection
    course_attendance_health: AttendanceSection
    attendance_intervention_candidates: AttendanceSection
    attendance_signals: AttendanceSignals
    attendance_readiness: AttendanceReadiness
