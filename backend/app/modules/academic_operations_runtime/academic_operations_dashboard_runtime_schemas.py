"""Schemas for Academic Operations Dashboard runtime (A-052.14-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AcademicOperationsDashboardRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "ACADEMIC_OPERATIONS_DASHBOARD_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class AcademicOperationsDashboardKpiSummary(BaseModel):
    runtime_slice_count: int = 0
    aggregated_records_total: int = 0
    high_priority_total: int = 0
    recommended_actions_total: int = 0
    read_only: bool = True


class AcademicOperationsDashboardSummarySection(BaseModel):
    owner_module: str = "academic_operations_runtime"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class AcademicOperationsDashboardPriorityItem(BaseModel):
    item_id: str
    title: str
    priority: str
    status: str
    score: int
    domain: str
    source_signal_ids: list[str] = Field(default_factory=list)
    read_only: bool = True


class AcademicOperationsDashboardRecommendedAction(BaseModel):
    action_id: str
    title: str
    priority: str
    rationale: str
    source_signal_ids: list[str] = Field(default_factory=list)


class AcademicOperationsDashboardHealthScore(BaseModel):
    composite_score: int = 0
    classification: str = "CRITICAL"
    contributing_factors: list[str] = Field(default_factory=list)
    read_only: bool = True


class AcademicOperationsDashboardRuntimeResponse(BaseModel):
    tenant_id: int
    overview: AcademicOperationsDashboardRuntimeOverview
    kpi_summary: AcademicOperationsDashboardKpiSummary
    registry_summary: AcademicOperationsDashboardSummarySection
    curriculum_summary: AcademicOperationsDashboardSummarySection
    timetable_summary: AcademicOperationsDashboardSummarySection
    attendance_summary: AcademicOperationsDashboardSummarySection
    assessment_summary: AcademicOperationsDashboardSummarySection
    teaching_load_summary: AcademicOperationsDashboardSummarySection
    internship_summary: AcademicOperationsDashboardSummarySection
    signals_summary: AcademicOperationsDashboardSummarySection
    high_priority_items: list[AcademicOperationsDashboardPriorityItem] = Field(default_factory=list)
    recommended_actions: list[AcademicOperationsDashboardRecommendedAction] = Field(default_factory=list)
    academic_operations_health_score: AcademicOperationsDashboardHealthScore
