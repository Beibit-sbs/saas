"""Schemas for Academic Registry runtime (A-052.6-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AcademicRegistryRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "ACADEMIC_REGISTRY_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class AcademicRegistryRuntimeStatistics(BaseModel):
    academic_periods_total: int = 0
    academic_groups_total: int = 0
    curriculum_registry_total: int = 0
    course_catalog_linkage_total: int = 0
    student_registry_linkage_total: int = 0
    canonical_bridge_total: int = 0


class AcademicRegistryRuntimeSection(BaseModel):
    owner_module: str = "academic_operations"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class AcademicRegistryIntegrationStatus(BaseModel):
    provider: str
    status: str
    integration_mode: str = "READINESS_ONLY"
    ready: bool = False
    evidence_count: int = 0
    read_only: bool = True


class AcademicRegistryHealth(BaseModel):
    healthy: bool = True
    consistency_score: int = 0
    issues: list[str] = Field(default_factory=list)


class AcademicRegistryReadiness(BaseModel):
    ready_for_runtime: bool = False
    checklist: list[str] = Field(default_factory=list)
    readiness_score: int = 0


class AcademicRegistryRuntimeResponse(BaseModel):
    tenant_id: int
    overview: AcademicRegistryRuntimeOverview
    registry_statistics: AcademicRegistryRuntimeStatistics
    academic_periods: AcademicRegistryRuntimeSection
    academic_groups: AcademicRegistryRuntimeSection
    curriculum_linkage: AcademicRegistryRuntimeSection
    catalog_linkage: AcademicRegistryRuntimeSection
    sis_status: AcademicRegistryIntegrationStatus
    lms_status: AcademicRegistryIntegrationStatus
    health: AcademicRegistryHealth
    readiness: AcademicRegistryReadiness
