"""Schemas for Quality / Accreditation self-assessment runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SelfAssessmentStandard(BaseModel):
    standard_id: str
    standard_name: str
    accreditation_framework: str
    readiness_score: int = 0
    completion_percentage: int = 0
    evidence_coverage: int = 0
    gap_count: int = 0
    risk_level: str = "UNKNOWN"
    owner_unit: str
    last_updated: datetime
    read_only: bool = True
    aggregator_only: bool = True


class SelfAssessmentScorecard(BaseModel):
    standards_total: int = 0
    ready_standards: int = 0
    average_readiness_score: float = 0.0
    average_completion_percentage: float = 0.0
    average_evidence_coverage: float = 0.0
    high_risk_standards: int = 0
    gap_total: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class SelfAssessmentReadinessSummary(BaseModel):
    readiness_band: str
    standard_count: int = 0
    average_readiness_score: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class SelfAssessmentCoverageSummary(BaseModel):
    coverage_scope: str
    standard_count: int = 0
    average_evidence_coverage: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class SelfAssessmentRiskSummary(BaseModel):
    risk_level: str
    standard_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class SelfAssessmentRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "SELF_ASSESSMENT_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    standards: list[SelfAssessmentStandard] = Field(default_factory=list)
    scorecard: SelfAssessmentScorecard
    readiness_summary: list[SelfAssessmentReadinessSummary] = Field(default_factory=list)
    coverage_summary: list[SelfAssessmentCoverageSummary] = Field(default_factory=list)
    risk_summary: list[SelfAssessmentRiskSummary] = Field(default_factory=list)
