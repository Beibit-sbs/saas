"""Schemas for Teaching Load runtime (A-052.11-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TeachingLoadRuntimeOverview(BaseModel):
    owner_module: str = "academic_operations_runtime"
    runtime_scope: str = "TEACHING_LOAD_RUNTIME"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True


class TeachingLoadRuntimeStatistics(BaseModel):
    tracked_faculty_total: int = 0
    department_groups_total: int = 0
    high_utilization_total: int = 0
    low_utilization_total: int = 0
    high_risk_assignments_total: int = 0
    teaching_load_signals_total: int = 0
    canonical_bridge_total: int = 0


class TeachingLoadRuntimeSection(BaseModel):
    owner_module: str = "academic_operations"
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class FacultyWorkloadDistribution(BaseModel):
    evenly_distributed_total: int = 0
    overloaded_total: int = 0
    underutilized_total: int = 0
    fairness_alert_total: int = 0
    read_only: bool = True


class WorkloadUtilization(BaseModel):
    average_utilization_pct: float = 0.0
    median_utilization_pct: float = 0.0
    min_utilization_pct: float = 0.0
    max_utilization_pct: float = 0.0
    utilization_std_dev: float = 0.0
    read_only: bool = True


class TeachingLoadRiskSummary(BaseModel):
    risk_score: int = 0
    open_risks: int = 0
    indicators: list[str] = Field(default_factory=list)
    read_only: bool = True


class TeachingLoadSignals(BaseModel):
    generated_signals: int = 0
    signal_types: list[str] = Field(default_factory=list)
    read_only: bool = True


class TeachingLoadReadiness(BaseModel):
    ready_for_runtime: bool = False
    checklist: list[str] = Field(default_factory=list)
    readiness_score: int = 0


class TeachingLoadRuntimeResponse(BaseModel):
    tenant_id: int
    overview: TeachingLoadRuntimeOverview
    teaching_load_statistics: TeachingLoadRuntimeStatistics
    faculty_workload_distribution: FacultyWorkloadDistribution
    workload_utilization: WorkloadUtilization
    overload_risk_summary: TeachingLoadRiskSummary
    underutilization_summary: TeachingLoadRuntimeSection
    faculty_assignment_health: TeachingLoadRuntimeSection
    coverage_risk_summary: TeachingLoadRiskSummary
    high_risk_assignments: TeachingLoadRuntimeSection
    teaching_load_signals: TeachingLoadSignals
    teaching_load_readiness: TeachingLoadReadiness