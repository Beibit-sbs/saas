"""Pydantic schemas for Executive Governance runtime shell."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ExecutiveSignalFamily = Literal[
    "overdue_assignment",
    "execution_delay",
    "resolution_risk",
    "kpi_drift",
    "escalation_risk",
    "strategic_goal_slippage",
    "executive_workload",
    "workload_imbalance",
    "ministry_deadline_risk",
    "protocol_non_execution",
    "decision_stagnation",
    "assignment_stagnation",
    "roadmap_delay",
    "initiative_stagnation",
    "kpi_deviation",
    "target_miss_risk",
    "performance_decline",
    "strategic_misalignment",
    "unit_underperformance",
    "executive_performance_drop",
    "execution_gap",
    "strategic_risk",
    "transformation_delay",
    "accreditation_risk",
]


class ExecutiveGovernanceSignalSummary(BaseModel):
    signal_family: ExecutiveSignalFamily
    owner_module: str = "brain_core"
    source_module: str
    read_only: bool = True
    observed_items: int = 0
    notes: str


class ExecutiveGovernanceRuntimeOverview(BaseModel):
    tenant_id: int
    owner_module: str = "executive_control_tower"
    runtime_boundary: str = "UNIFIED_READ_ONLY_RUNTIME_SHELL"
    navigation_entry: str = "/console/executive-governance"
    canonical_modules: list[str] = Field(default_factory=list)
    read_only_runtime: bool = True
    provider_integrations_enabled: bool = False
    external_calls_enabled: bool = False
    executive_assignments: int = 0
    executive_decisions: int = 0
    executive_protocols: int = 0
    executive_meetings: int = 0
    overdue_items: int = 0
    escalated_items: int = 0
    strategic_items: int = 0
    executive_signals: int = 0
    generated_at: datetime


class ExecutiveGovernanceRuntimeSummary(BaseModel):
    tenant_id: int
    read_only: bool = True
    owner_modules: list[str] = Field(default_factory=list)
    executive_assignments: int = 0
    executive_decisions: int = 0
    executive_protocols: int = 0
    executive_meetings: int = 0
    overdue_items: int = 0
    escalated_items: int = 0
    strategic_items: int = 0
    executive_signals: int = 0
    generated_at: datetime


class ExecutiveGovernanceDashboardSummary(BaseModel):
    tenant_id: int
    dashboard_owner_module: str = "executive_control_tower"
    dashboard_view: str = "executive_control_tower"
    widgets: list[str] = Field(default_factory=list)
    executive_assignments: int = 0
    executive_decisions: int = 0
    executive_protocols: int = 0
    executive_meetings: int = 0
    overdue_items: int = 0
    escalated_items: int = 0
    strategic_items: int = 0
    executive_signals: int = 0
    signal_summaries: list[ExecutiveGovernanceSignalSummary] = Field(default_factory=list)
    rbac_roles: list[str] = Field(default_factory=list)
    read_only: bool = True
    auditability_preserved: bool = True
    generated_at: datetime


DecisionExecutionStatus = Literal[
    "NOT_STARTED",
    "IN_PROGRESS",
    "AT_RISK",
    "ESCALATED",
    "OVERDUE",
    "COMPLETED",
    "CLOSED",
]


class ExecutiveDecisionRegistryEntry(BaseModel):
    decision_id: str
    decision_type: str
    decision_source: str
    decision_title: str
    decision_status: str
    decision_date: datetime
    execution_status: DecisionExecutionStatus
    execution_progress: int
    assigned_units: list[str] = Field(default_factory=list)
    overdue_flag: bool = False
    escalation_flag: bool = False


class ExecutiveDecisionRegistrySummary(BaseModel):
    tenant_id: int
    entries: list[ExecutiveDecisionRegistryEntry] = Field(default_factory=list)
    total_decisions: int = 0
    decision_sources: dict[str, int] = Field(default_factory=dict)
    execution_status_counts: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True
    aggregator_only: bool = True
    owner_modules: list[str] = Field(default_factory=list)
    generated_at: datetime


class ExecutiveDecisionExecutionSummary(BaseModel):
    tenant_id: int
    total_decisions: int = 0
    execution_status_counts: dict[str, int] = Field(default_factory=dict)
    overdue_items: int = 0
    escalated_items: int = 0
    signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveAssignmentEntry(BaseModel):
    assignment_id: str
    assignment_title: str
    assignment_source: str
    assignment_type: str
    assigned_unit: str
    assigned_person: str
    created_at: datetime
    due_date: datetime
    completion_percent: int = 0
    execution_status: DecisionExecutionStatus
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    overdue_flag: bool = False
    escalation_flag: bool = False


class ExecutiveAssignmentSummary(BaseModel):
    tenant_id: int
    entries: list[ExecutiveAssignmentEntry] = Field(default_factory=list)
    total_assignments: int = 0
    active_assignments: int = 0
    completed_assignments: int = 0
    overdue_assignments: int = 0
    escalated_assignments: int = 0
    execution_performance: int = 0
    execution_trend: str = "STABLE"
    read_only: bool = True
    aggregator_only: bool = True
    owner_modules: list[str] = Field(default_factory=list)
    generated_at: datetime


class ExecutiveExecutionMetrics(BaseModel):
    tenant_id: int
    total_assignments: int = 0
    execution_status_counts: dict[str, int] = Field(default_factory=dict)
    overdue_assignments: int = 0
    escalated_assignments: int = 0
    execution_performance: int = 0
    execution_trend: str = "STABLE"
    escalation_inventory: dict[str, int] = Field(default_factory=dict)
    escalation_summary: dict[str, int] = Field(default_factory=dict)
    escalation_trends: list[str] = Field(default_factory=list)
    high_risk_assignments: list[ExecutiveAssignmentEntry] = Field(default_factory=list)
    signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveControlTowerSummary(BaseModel):
    tenant_id: int
    dashboard_owner_module: str = "executive_control_tower"
    dashboard_view: str = "rector_dashboard"
    total_decisions: int = 0
    total_protocols: int = 0
    total_assignments: int = 0
    active_assignments: int = 0
    completed_assignments: int = 0
    overdue_assignments: int = 0
    escalated_assignments: int = 0
    execution_rate: int = 0
    risk_score: int = 0
    kpi_score: int = 0
    executive_workload: int = 0
    strategic_initiatives: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True
    aggregator_only: bool = True
    auditability_preserved: bool = True
    generated_at: datetime


class ExecutivePerformanceMetrics(BaseModel):
    tenant_id: int
    total_decisions: int = 0
    total_protocols: int = 0
    total_assignments: int = 0
    active_assignments: int = 0
    completed_assignments: int = 0
    overdue_assignments: int = 0
    escalated_assignments: int = 0
    execution_rate: int = 0
    completion_rate: int = 0
    escalation_rate: int = 0
    workload_distribution: dict[str, int] = Field(default_factory=dict)
    unit_performance: dict[str, int] = Field(default_factory=dict)
    strategic_initiative_status: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveRiskOverview(BaseModel):
    tenant_id: int
    risk_score: int = 0
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    high_risk_assignments: list[ExecutiveAssignmentEntry] = Field(default_factory=list)
    high_risk_units: dict[str, int] = Field(default_factory=dict)
    high_risk_initiatives: dict[str, int] = Field(default_factory=dict)
    escalation_hotspots: dict[str, int] = Field(default_factory=dict)
    overdue_hotspots: dict[str, int] = Field(default_factory=dict)
    signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveKpiOverview(BaseModel):
    tenant_id: int
    kpi_score: int = 0
    kpi_distribution: dict[str, int] = Field(default_factory=dict)
    execution_rate: int = 0
    completion_rate: int = 0
    escalation_rate: int = 0
    unit_performance: dict[str, int] = Field(default_factory=dict)
    strategic_initiative_status: dict[str, int] = Field(default_factory=dict)
    signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


KpiTrendDirection = Literal["UP", "DOWN", "STABLE"]
KpiRiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
KpiStatus = Literal["ON_TRACK", "AT_RISK", "MISSED", "EXCEEDED"]


class ExecutiveKpiEntry(BaseModel):
    kpi_id: str
    kpi_code: str
    kpi_name: str
    kpi_owner: str
    kpi_category: str
    target_value: float
    current_value: float
    achievement_percent: int = 0
    status: KpiStatus = "ON_TRACK"
    risk_level: KpiRiskLevel = "LOW"
    trend_direction: KpiTrendDirection = "STABLE"
    linked_initiatives: list[str] = Field(default_factory=list)


class ExecutiveKpiSummary(BaseModel):
    tenant_id: int
    entries: list[ExecutiveKpiEntry] = Field(default_factory=list)
    total_kpis: int = 0
    completion_rate: int = 0
    achievement_rate: int = 0
    deviation_rate: int = 0
    risk_rate: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)
    owner_modules: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutivePerformanceScore(BaseModel):
    kpi_id: str
    kpi_code: str
    score: int = 0
    trend_direction: KpiTrendDirection = "STABLE"
    deviation_percent: int = 0
    risk_level: KpiRiskLevel = "LOW"


class PerformanceGovernanceSummary(BaseModel):
    tenant_id: int
    university_performance_score: int = 0
    executive_performance_score: int = 0
    unit_performance_score: int = 0
    strategic_performance_score: int = 0
    kpi_completion_rate: int = 0
    kpi_risk_rate: int = 0
    performance_trend: str = "STABLE"
    kpi_achievement_rate: int = 0
    kpi_deviation_rate: int = 0
    unit_kpi_performance: dict[str, int] = Field(default_factory=dict)
    strategic_kpi_alignment: dict[str, int] = Field(default_factory=dict)
    trend_analysis: dict[str, int] = Field(default_factory=dict)
    signal_families: list[ExecutiveSignalFamily] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveKpiRiskCenter(BaseModel):
    tenant_id: int
    high_risk_kpis: list[ExecutiveKpiEntry] = Field(default_factory=list)
    missed_kpis: list[ExecutiveKpiEntry] = Field(default_factory=list)
    kpi_deviation_hotspots: dict[str, int] = Field(default_factory=dict)
    low_performance_units: dict[str, int] = Field(default_factory=dict)
    strategic_kpi_gaps: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveKpiTrendSummary(BaseModel):
    tenant_id: int
    trend_direction_counts: dict[str, int] = Field(default_factory=dict)
    performance_scores: list[ExecutivePerformanceScore] = Field(default_factory=list)
    trend_analysis: dict[str, int] = Field(default_factory=dict)
    signal_families: list[ExecutiveSignalFamily] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


RiskTrendDirection = Literal["UP", "DOWN", "STABLE"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
RiskStatus = Literal["OPEN", "MONITORING", "MITIGATING", "ESCALATED", "CLOSED"]


class ExecutiveRiskEntry(BaseModel):
    risk_id: str
    risk_category: str
    risk_source: str
    risk_title: str
    risk_description: str
    risk_owner: str
    risk_level: RiskLevel = "LOW"
    probability: int = 0
    impact: int = 0
    risk_score: int = 0
    status: RiskStatus = "OPEN"
    trend_direction: RiskTrendDirection = "STABLE"
    escalation_flag: bool = False


class ExecutiveRiskSummary(BaseModel):
    tenant_id: int
    entries: list[ExecutiveRiskEntry] = Field(default_factory=list)
    total_risks: int = 0
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    risk_category_breakdown: dict[str, int] = Field(default_factory=dict)
    risk_ownership_visibility: dict[str, int] = Field(default_factory=dict)
    risk_trend_analysis: dict[str, int] = Field(default_factory=dict)
    risk_hotspots: dict[str, int] = Field(default_factory=dict)
    executive_risk_score: int = 0
    owner_modules: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveRiskHeatmap(BaseModel):
    tenant_id: int
    heatmap: dict[str, dict[str, int]] = Field(default_factory=dict)
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    risk_hotspots: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveRiskCenter(BaseModel):
    tenant_id: int
    high_risk_items: list[ExecutiveRiskEntry] = Field(default_factory=list)
    critical_risks: list[ExecutiveRiskEntry] = Field(default_factory=list)
    escalating_risks: list[ExecutiveRiskEntry] = Field(default_factory=list)
    overdue_risks: list[ExecutiveRiskEntry] = Field(default_factory=list)
    risk_hotspots: dict[str, int] = Field(default_factory=dict)
    signal_families: list[ExecutiveSignalFamily] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveRiskScore(BaseModel):
    tenant_id: int
    executive_risk_score: int = 0
    risk_band: Literal["LOW", "GUARDED", "ELEVATED", "SEVERE"] = "LOW"
    high_risk_items: int = 0
    critical_risks: int = 0
    escalating_risks: int = 0
    overdue_risks: int = 0
    trend_direction: RiskTrendDirection = "STABLE"
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class RectorDashboardRuntimeSummary(BaseModel):
    tenant_id: int
    rector_overview: ExecutiveControlTowerSummary
    university_execution_status: ExecutivePerformanceMetrics
    strategic_initiatives: dict[str, int] = Field(default_factory=dict)
    executive_risks: ExecutiveRiskOverview
    kpi_performance: ExecutiveKpiOverview
    escalation_summary: dict[str, int] = Field(default_factory=dict)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class StrategicInitiativeEntry(BaseModel):
    initiative_id: str
    initiative_code: str
    initiative_title: str
    initiative_owner: str
    initiative_status: str
    start_date: datetime
    target_date: datetime
    completion_percent: int = 0
    linked_kpi_count: int = 0
    linked_assignment_count: int = 0
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    escalation_flag: bool = False


class StrategicInitiativeSummary(BaseModel):
    tenant_id: int
    initiatives: list[StrategicInitiativeEntry] = Field(default_factory=list)
    total_initiatives: int = 0
    active_initiatives: int = 0
    completed_initiatives: int = 0
    at_risk_initiatives: int = 0
    delayed_initiatives: int = 0
    initiative_kpi_coverage: int = 0
    kpi_completion_alignment: int = 0
    kpi_deviation_visibility: dict[str, int] = Field(default_factory=dict)
    kpi_ownership_visibility: dict[str, int] = Field(default_factory=dict)
    roadmap_visibility: dict[str, int] = Field(default_factory=dict)
    strategic_signal_families: list[str] = Field(default_factory=list)
    rbac_roles: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class StrategicInitiativeMetrics(BaseModel):
    tenant_id: int
    delayed_initiatives: list[StrategicInitiativeEntry] = Field(default_factory=list)
    high_risk_initiatives: list[StrategicInitiativeEntry] = Field(default_factory=list)
    kpi_deviation_hotspots: dict[str, int] = Field(default_factory=dict)
    strategic_bottlenecks: dict[str, int] = Field(default_factory=dict)
    execution_blockers: dict[str, int] = Field(default_factory=dict)
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    strategic_signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class DevelopmentProgramSummary(BaseModel):
    tenant_id: int
    program_name: str
    program_year: int
    initiative_count: int = 0
    active_initiatives: int = 0
    completed_initiatives: int = 0
    at_risk_initiatives: int = 0
    delayed_initiatives: int = 0
    overall_progress: int = 0
    strategic_signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    aggregator_only: bool = True
    generated_at: datetime


class ExecutiveMeetingEntry(BaseModel):
    meeting_id: str
    meeting_type: str
    meeting_title: str
    meeting_date: datetime
    meeting_status: str
    chairperson: str
    participants_count: int = 0
    protocol_count: int = 0
    decision_count: int = 0
    execution_status: DecisionExecutionStatus


class ExecutiveMeetingSummary(BaseModel):
    tenant_id: int
    entries: list[ExecutiveMeetingEntry] = Field(default_factory=list)
    total_meetings: int = 0
    meeting_status_counts: dict[str, int] = Field(default_factory=dict)
    total_protocols: int = 0
    total_decisions: int = 0
    read_only: bool = True
    generated_at: datetime


class ExecutiveProtocolEntry(BaseModel):
    protocol_id: str
    protocol_number: str
    protocol_title: str
    protocol_date: datetime
    protocol_status: str
    decision_count: int = 0
    assignment_count: int = 0
    execution_progress: int = 0
    overdue_items: int = 0
    escalated_items: int = 0


class ExecutiveProtocolSummary(BaseModel):
    tenant_id: int
    entries: list[ExecutiveProtocolEntry] = Field(default_factory=list)
    total_protocols: int = 0
    protocol_status_counts: dict[str, int] = Field(default_factory=dict)
    total_decisions: int = 0
    total_assignments: int = 0
    average_execution_progress: int = 0
    overdue_items: int = 0
    escalated_items: int = 0
    read_only: bool = True
    generated_at: datetime


class ExecutiveProtocolExecutionSummary(BaseModel):
    tenant_id: int
    total_protocols: int = 0
    average_execution_progress: int = 0
    overdue_items: int = 0
    escalated_items: int = 0
    completion_status: dict[str, int] = Field(default_factory=dict)
    linkage_inventory: dict[str, int] = Field(default_factory=dict)
    signal_families: list[str] = Field(default_factory=list)
    read_only: bool = True
    generated_at: datetime
