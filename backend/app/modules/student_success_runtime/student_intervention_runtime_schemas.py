"""Schemas for Student Intervention runtime (A-051.10-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentInterventionRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentInterventionRuntimeSafety(BaseModel):
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
    intervention_execution_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentInterventionRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_INTERVENTION_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    intervention_summary: StudentInterventionRuntimeSection
    intervention_priority_groups: StudentInterventionRuntimeSection
    intervention_recommendations: StudentInterventionRuntimeSection
    advisor_interventions: StudentInterventionRuntimeSection
    dean_interventions: StudentInterventionRuntimeSection
    support_programs: StudentInterventionRuntimeSection
    intervention_effectiveness_signals: StudentInterventionRuntimeSection
    intervention_signal_summary: StudentInterventionRuntimeSection
    safety: StudentInterventionRuntimeSafety
