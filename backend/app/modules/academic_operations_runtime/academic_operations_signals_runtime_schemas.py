"""Schemas for Academic Operations Signals runtime (A-052.13-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AcademicOperationsSignalsRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "ACADEMIC_OPERATIONS_SIGNALS_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class AcademicOperationsSignalSummary(BaseModel):
    total_signals: int = 0
    high_priority_total: int = 0
    medium_priority_total: int = 0
    low_priority_total: int = 0
    read_only: bool = True


class AcademicOperationsSignalDistribution(BaseModel):
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_domain: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True


class AcademicOperationsSignalItem(BaseModel):
    signal_id: str
    signal_name: str
    severity: str
    score: int
    status: str
    summary: str
    source_modules: list[str] = Field(default_factory=list)
    read_only: bool = True


class AcademicOperationsSignalSection(BaseModel):
    owner_module: str = "academic_operations_runtime"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)
    items: list[AcademicOperationsSignalItem] = Field(default_factory=list)


class AcademicOperationsHealthScore(BaseModel):
    composite_score: int = 0
    classification: str = "CRITICAL"
    contributing_factors: list[str] = Field(default_factory=list)
    read_only: bool = True


class AcademicOperationsRecommendedAction(BaseModel):
    action_id: str
    title: str
    priority: str
    rationale: str
    source_signal_ids: list[str] = Field(default_factory=list)


class AcademicOperationsSignalsRuntimeResponse(BaseModel):
    tenant_id: int
    overview: AcademicOperationsSignalsRuntimeOverview
    signal_summary: AcademicOperationsSignalSummary
    signal_distribution: AcademicOperationsSignalDistribution
    high_priority_signals: AcademicOperationsSignalSection
    medium_priority_signals: AcademicOperationsSignalSection
    low_priority_signals: AcademicOperationsSignalSection
    curriculum_signals: AcademicOperationsSignalSection
    timetable_signals: AcademicOperationsSignalSection
    attendance_signals: AcademicOperationsSignalSection
    assessment_signals: AcademicOperationsSignalSection
    teaching_load_signals: AcademicOperationsSignalSection
    internship_signals: AcademicOperationsSignalSection
    health_score: AcademicOperationsHealthScore
    recommended_actions: list[AcademicOperationsRecommendedAction] = Field(default_factory=list)
