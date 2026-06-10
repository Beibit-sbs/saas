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
    "ministry_deadline_risk",
    "protocol_non_execution",
    "decision_stagnation",
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
