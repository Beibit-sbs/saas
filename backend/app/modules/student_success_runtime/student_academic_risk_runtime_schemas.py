"""Schemas for Student Academic Risk runtime (A-051.8-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentAcademicRiskRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentAcademicRiskRuntimeSafety(BaseModel):
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


class StudentAcademicRiskRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_ACADEMIC_RISK_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    academic_risk_summary: StudentAcademicRiskRuntimeSection
    gpa_risk_distribution: StudentAcademicRiskRuntimeSection
    failed_course_risk_summary: StudentAcademicRiskRuntimeSection
    low_performance_summary: StudentAcademicRiskRuntimeSection
    probation_summary: StudentAcademicRiskRuntimeSection
    progression_risk_summary: StudentAcademicRiskRuntimeSection
    academic_alert_summary: StudentAcademicRiskRuntimeSection
    academic_signal_summary: StudentAcademicRiskRuntimeSection
    safety: StudentAcademicRiskRuntimeSafety
