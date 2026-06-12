"""Schemas for Student Retention runtime (A-051.7-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentRetentionRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentRetentionRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    write_operations_enabled: bool = False
    workflow_execution_enabled: bool = False
    approval_execution_enabled: bool = False
    background_jobs_enabled: bool = False
    outbound_providers_enabled: bool = False
    external_integrations_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentRetentionRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_RETENTION_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    retention_summary: StudentRetentionRuntimeSection
    retention_score_distribution: StudentRetentionRuntimeSection
    retention_risk_distribution: StudentRetentionRuntimeSection
    dropout_risk_summary: StudentRetentionRuntimeSection
    persistence_summary: StudentRetentionRuntimeSection
    retention_trend_summary: StudentRetentionRuntimeSection
    cohort_retention_summary: StudentRetentionRuntimeSection
    retention_signal_summary: StudentRetentionRuntimeSection
    safety: StudentRetentionRuntimeSafety
