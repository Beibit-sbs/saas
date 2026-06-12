"""Schemas for Student Registry runtime (A-051.6-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentRegistryRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class StudentRegistryRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    write_operations_enabled: bool = False
    workflow_execution_enabled: bool = False
    approval_execution_enabled: bool = False
    background_jobs_enabled: bool = False
    provider_mutation_enabled: bool = False
    outbound_calls_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class StudentRegistryRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "student_success_brain"
    runtime_surface: str = "STUDENT_REGISTRY_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    student_registry_summary: StudentRegistryRuntimeSection
    enrollment_summary: StudentRegistryRuntimeSection
    academic_standing_summary: StudentRegistryRuntimeSection
    retention_link_summary: StudentRegistryRuntimeSection
    advisor_link_summary: StudentRegistryRuntimeSection
    risk_link_summary: StudentRegistryRuntimeSection
    lifecycle_status_summary: StudentRegistryRuntimeSection
    safety: StudentRegistryRuntimeSafety
