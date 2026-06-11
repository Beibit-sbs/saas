"""Schemas for Quality / Accreditation improvement plan runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ImprovementMilestoneDTO(BaseModel):
    milestone_id: str
    milestone_title: str
    due_date: datetime
    completion_percentage: int = 0
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class ImprovementKpiTargetDTO(BaseModel):
    kpi_target_id: str
    kpi_name: str
    baseline_value: float
    target_value: float
    current_value: float
    unit: str
    read_only: bool = True
    aggregator_only: bool = True


class ImprovementInitiativeDTO(BaseModel):
    initiative_id: str
    initiative_title: str
    strategic_theme: str
    owner_unit: str
    status: str
    completion_percentage: int = 0
    milestones: list[ImprovementMilestoneDTO] = Field(default_factory=list)
    kpi_targets: list[ImprovementKpiTargetDTO] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True


class ImprovementRoadmapDTO(BaseModel):
    roadmap_id: str
    roadmap_title: str
    accreditation_cycle: str
    phase: str
    initiatives_total: int = 0
    initiatives_completed: int = 0
    completion_percentage: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class ImprovementForecastDTO(BaseModel):
    forecast_id: str
    forecast_type: str
    confidence_level: str
    projected_completion_date: datetime
    readiness_forecast_score: int = 0
    risk_level: str = "UNKNOWN"
    read_only: bool = True
    aggregator_only: bool = True


class ImprovementPlanRuntimeDTO(BaseModel):
    plan_id: str
    plan_title: str
    accreditation_standard: str
    owner_unit: str
    progress_tracking_status: str
    completion_percentage: int = 0
    initiatives: list[ImprovementInitiativeDTO] = Field(default_factory=list)
    roadmaps: list[ImprovementRoadmapDTO] = Field(default_factory=list)
    forecasts: list[ImprovementForecastDTO] = Field(default_factory=list)
    last_updated: datetime
    read_only: bool = True
    aggregator_only: bool = True


class ImprovementPlanRuntimeResponseDTO(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "IMPROVEMENT_PLAN_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    improvement_plans: list[ImprovementPlanRuntimeDTO] = Field(default_factory=list)
