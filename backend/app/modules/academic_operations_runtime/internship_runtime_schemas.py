"""Schemas for Internship runtime (A-052.12-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InternshipRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "INTERNSHIP_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class InternshipRuntimeStatistics(BaseModel):
    participation_rate: float = 0.0
    completion_rate: float = 0.0
    active_rate: float = 0.0
    placement_rate: float = 0.0
    total_internships: int = 0
    active_internships: int = 0
    completed_internships: int = 0
    employer_count: int = 0


class InternshipPlacementDistribution(BaseModel):
    by_employer: dict[str, int] = Field(default_factory=dict)
    by_industry: dict[str, int] = Field(default_factory=dict)
    by_department: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True


class InternshipCompletionSummary(BaseModel):
    completed: int = 0
    active: int = 0
    overdue: int = 0
    read_only: bool = True


class ActiveInternshipRecord(BaseModel):
    internship_identifier: str
    employer: str
    student_count: int = 0
    status: str = "ACTIVE"


class InternshipActiveInternships(BaseModel):
    owner_module: str = "internship"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)
    items: list[ActiveInternshipRecord] = Field(default_factory=list)


class InternshipEmployerEngagement(BaseModel):
    employer_participation_rate: float = 0.0
    repeat_employers: int = 0
    placement_volume: int = 0
    employer_count: int = 0
    read_only: bool = True


class InternshipRiskSummary(BaseModel):
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    read_only: bool = True


class HighRiskInternship(BaseModel):
    internship_identifier: str
    employer: str
    student_count: int = 0
    risk_reason: str


class InternshipHighRiskInternships(BaseModel):
    owner_module: str = "internship"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)
    items: list[HighRiskInternship] = Field(default_factory=list)


class InternshipSignals(BaseModel):
    generated_signals: int = 0
    signal_types: list[str] = Field(default_factory=list)
    indicators: list[str] = Field(default_factory=list)
    read_only: bool = True


class InternshipReadiness(BaseModel):
    readiness_score: int = 0
    readiness_classification: str = "NOT_READY"
    readiness_drivers: list[str] = Field(default_factory=list)
    ready_for_runtime: bool = False


class InternshipRuntimeResponse(BaseModel):
    tenant_id: int
    overview: InternshipRuntimeOverview
    internship_statistics: InternshipRuntimeStatistics
    placement_distribution: InternshipPlacementDistribution
    completion_summary: InternshipCompletionSummary
    active_internships: InternshipActiveInternships
    employer_engagement: InternshipEmployerEngagement
    internship_risk_summary: InternshipRiskSummary
    high_risk_internships: InternshipHighRiskInternships
    internship_signals: InternshipSignals
    internship_readiness: InternshipReadiness
