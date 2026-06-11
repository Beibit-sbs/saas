"""Schemas for Student Success runtime shell (A-051.5-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentSuccessRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentSuccessRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    workflow_execution_enabled: bool = False
    provider_mutation_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentSuccessRuntimeShellResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_shell: str = "STUDENT_SUCCESS_RUNTIME_SHELL"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    student_success_overview: StudentSuccessRuntimeSection
    lifecycle_summary: StudentSuccessRuntimeSection
    retention_summary: StudentSuccessRuntimeSection
    risk_summary: StudentSuccessRuntimeSection
    intervention_summary: StudentSuccessRuntimeSection
    advisor_summary: StudentSuccessRuntimeSection
    signal_summary: StudentSuccessRuntimeSection
    dashboard_summary: StudentSuccessRuntimeSection
    safety: StudentSuccessRuntimeSafety
