"""Schemas for Student Attendance Risk runtime (A-051.9-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentAttendanceRiskRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentAttendanceRiskRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    write_operations_enabled: bool = False
    workflow_execution_enabled: bool = False
    approval_execution_enabled: bool = False
    background_jobs_enabled: bool = False
    provider_mutation_enabled: bool = False
    outbound_integrations_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentAttendanceRiskRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_ATTENDANCE_RISK_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    attendance_risk_summary: StudentAttendanceRiskRuntimeSection
    absence_distribution: StudentAttendanceRiskRuntimeSection
    chronic_absence_summary: StudentAttendanceRiskRuntimeSection
    missed_class_summary: StudentAttendanceRiskRuntimeSection
    attendance_trend_summary: StudentAttendanceRiskRuntimeSection
    punctuality_summary: StudentAttendanceRiskRuntimeSection
    engagement_attendance_summary: StudentAttendanceRiskRuntimeSection
    attendance_signal_summary: StudentAttendanceRiskRuntimeSection
    safety: StudentAttendanceRiskRuntimeSafety
