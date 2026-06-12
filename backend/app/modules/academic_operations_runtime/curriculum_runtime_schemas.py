"""Schemas for Curriculum runtime (A-052.7-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CurriculumRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "CURRICULUM_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class CurriculumRuntimeStatistics(BaseModel):
    program_structures_total: int = 0
    curriculum_versions_total: int = 0
    curriculum_health_score: int = 0
    course_catalog_linkage_total: int = 0
    prerequisite_chains_total: int = 0
    learning_outcomes_total: int = 0
    academic_plans_total: int = 0
    canonical_bridge_total: int = 0


class CurriculumRuntimeSection(BaseModel):
    owner_module: str = "academic_operations"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class CurriculumRuntimeHealth(BaseModel):
    healthy: bool = True
    consistency_score: int = 0
    issues: list[str] = Field(default_factory=list)


class CurriculumRuntimeRisks(BaseModel):
    risk_score: int = 0
    open_risks: int = 0
    indicators: list[str] = Field(default_factory=list)


class CurriculumRuntimeReadiness(BaseModel):
    ready_for_runtime: bool = False
    checklist: list[str] = Field(default_factory=list)
    readiness_score: int = 0


class CurriculumRuntimeResponse(BaseModel):
    tenant_id: int
    overview: CurriculumRuntimeOverview
    curriculum_statistics: CurriculumRuntimeStatistics
    program_structures: CurriculumRuntimeSection
    curriculum_versions: CurriculumRuntimeSection
    curriculum_health: CurriculumRuntimeHealth
    course_catalog_linkage: CurriculumRuntimeSection
    prerequisite_chains: CurriculumRuntimeSection
    learning_outcomes_summary: CurriculumRuntimeSection
    curriculum_risks: CurriculumRuntimeRisks
    curriculum_readiness: CurriculumRuntimeReadiness