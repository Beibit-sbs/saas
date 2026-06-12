"""Schemas for Student Advisor runtime (A-051.11-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentAdvisorRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentAdvisorRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    write_operations_enabled: bool = False
    intervention_execution_enabled: bool = False
    workflow_execution_enabled: bool = False
    approval_execution_enabled: bool = False
    background_jobs_enabled: bool = False
    notification_execution_enabled: bool = False
    provider_mutation_enabled: bool = False
    outbound_integrations_enabled: bool = False
    scheduling_engine_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentAdvisorRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_ADVISOR_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    advisor_summary: StudentAdvisorRuntimeSection
    advisor_workload_distribution: StudentAdvisorRuntimeSection
    advisor_student_assignments: StudentAdvisorRuntimeSection
    advisor_intervention_queue: StudentAdvisorRuntimeSection
    advisor_follow_up_summary: StudentAdvisorRuntimeSection
    advisor_risk_coverage: StudentAdvisorRuntimeSection
    advisor_effectiveness_summary: StudentAdvisorRuntimeSection
    advisor_signal_summary: StudentAdvisorRuntimeSection
    safety: StudentAdvisorRuntimeSafety
