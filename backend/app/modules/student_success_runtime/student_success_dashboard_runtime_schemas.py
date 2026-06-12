"""Schemas for Student Success Dashboard runtime (A-051.13-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentSuccessDashboardRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentSuccessDashboardRuntimeSafety(BaseModel):
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
    persistence_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentSuccessDashboardRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_SUCCESS_DASHBOARD_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    executive_summary: StudentSuccessDashboardRuntimeSection
    student_population: StudentSuccessDashboardRuntimeSection
    retention_overview: StudentSuccessDashboardRuntimeSection
    academic_risk_overview: StudentSuccessDashboardRuntimeSection
    attendance_risk_overview: StudentSuccessDashboardRuntimeSection
    intervention_overview: StudentSuccessDashboardRuntimeSection
    advisor_overview: StudentSuccessDashboardRuntimeSection
    success_signals: StudentSuccessDashboardRuntimeSection
    priority_actions: StudentSuccessDashboardRuntimeSection
    dashboard_kpis: StudentSuccessDashboardRuntimeSection
    safety: StudentSuccessDashboardRuntimeSafety
