"""Schemas for Assessment runtime (A-052.10-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "ASSESSMENT_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class AssessmentRuntimeStatistics(BaseModel):
    exams_total: int = 0
    completed_exams_total: int = 0
    gradebook_entries_total: int = 0
    grading_distribution_total: int = 0
    schedule_alignment_total: int = 0
    assessment_signals_total: int = 0
    canonical_bridge_total: int = 0


class AssessmentSection(BaseModel):
    owner_module: str = "academic_operations"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class AssessmentGradingDistribution(BaseModel):
    excellent_band: int = 0
    good_band: int = 0
    warning_band: int = 0
    critical_band: int = 0
    read_only: bool = True


class AssessmentRiskSummary(BaseModel):
    risk_score: int = 0
    open_risks: int = 0
    indicators: list[str] = Field(default_factory=list)
    read_only: bool = True


class AssessmentSignals(BaseModel):
    generated_signals: int = 0
    signal_types: list[str] = Field(default_factory=list)
    read_only: bool = True


class AssessmentReadiness(BaseModel):
    ready_for_runtime: bool = False
    checklist: list[str] = Field(default_factory=list)
    readiness_score: int = 0


class AssessmentRuntimeResponse(BaseModel):
    tenant_id: int
    overview: AssessmentRuntimeOverview
    assessment_statistics: AssessmentRuntimeStatistics
    exam_governance_summary: AssessmentSection
    gradebook_readiness: AssessmentSection
    grading_distribution: AssessmentGradingDistribution
    assessment_schedule_alignment: AssessmentSection
    assessment_risk_summary: AssessmentRiskSummary
    high_risk_assessments: AssessmentSection
    assessment_signals: AssessmentSignals
    assessment_readiness: AssessmentReadiness
