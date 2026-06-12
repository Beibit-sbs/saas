"""Schemas for Student Success Signals runtime (A-051.12-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentSuccessSignalsRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentSuccessSignalsRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    write_operations_enabled: bool = False
    workflow_execution_enabled: bool = False
    approval_execution_enabled: bool = False
    background_jobs_enabled: bool = False
    notification_execution_enabled: bool = False
    provider_mutation_enabled: bool = False
    outbound_integrations_enabled: bool = False
    scheduling_engine_enabled: bool = False
    signal_execution_engine_enabled: bool = False
    persistence_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentSuccessSignalsRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_SUCCESS_SIGNALS_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    success_signal_summary: StudentSuccessSignalsRuntimeSection
    retention_signals: StudentSuccessSignalsRuntimeSection
    academic_signals: StudentSuccessSignalsRuntimeSection
    attendance_signals: StudentSuccessSignalsRuntimeSection
    intervention_signals: StudentSuccessSignalsRuntimeSection
    advisor_signals: StudentSuccessSignalsRuntimeSection
    early_warning_signals: StudentSuccessSignalsRuntimeSection
    success_indicator_signals: StudentSuccessSignalsRuntimeSection
    signal_trend_summary: StudentSuccessSignalsRuntimeSection
    signal_scorecard: StudentSuccessSignalsRuntimeSection
    safety: StudentSuccessSignalsRuntimeSafety
