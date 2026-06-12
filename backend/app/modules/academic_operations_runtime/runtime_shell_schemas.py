"""Schemas for Academic Operations runtime shell (A-052.5-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AcademicOperationsRuntimeShellSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class AcademicOperationsRuntimeShellSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    tenant_aware: bool = True
    summary_read_required: bool = True
    workflow_execution_enabled: bool = False
    approval_execution_enabled: bool = False
    background_jobs_enabled: bool = False
    provider_mutation_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class AcademicOperationsRuntimeShellResponse(BaseModel):
    tenant_id: int
    owner_module: str = "academic_operations"
    runtime_shell: str = "ACADEMIC_OPERATIONS_RUNTIME_SHELL"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    runtime_shell_summary: AcademicOperationsRuntimeShellSection
    runtime_shell_domain: AcademicOperationsRuntimeShellSection
    runtime_shell_runtime: AcademicOperationsRuntimeShellSection
    runtime_shell_integration: AcademicOperationsRuntimeShellSection
    runtime_shell_readiness: AcademicOperationsRuntimeShellSection
    safety: AcademicOperationsRuntimeShellSafety
