"""Schemas for Quality / Accreditation corrective action runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CorrectiveActionItem(BaseModel):
    action_id: str
    action_title: str
    accreditation_standard: str
    finding_reference: str
    owner_unit: str
    due_date: datetime
    completion_percentage: int = 0
    status: str
    readiness_score: int = 0
    risk_level: str = "UNKNOWN"
    overdue_flag: bool = False
    last_updated: datetime
    read_only: bool = True
    aggregator_only: bool = True


class CorrectiveActionSummary(BaseModel):
    total_actions: int = 0
    completed_actions: int = 0
    in_progress_actions: int = 0
    overdue_actions: int = 0
    average_completion_percentage: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class CorrectiveActionReadinessSummary(BaseModel):
    readiness_band: str
    action_count: int = 0
    average_readiness_score: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class CorrectiveActionRiskSummary(BaseModel):
    risk_level: str
    action_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class CorrectiveActionOverdueSummary(BaseModel):
    overdue_state: str
    action_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class CorrectiveActionRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "CORRECTIVE_ACTION_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    corrective_actions: list[CorrectiveActionItem] = Field(default_factory=list)
    action_summary: CorrectiveActionSummary
    readiness_summary: list[CorrectiveActionReadinessSummary] = Field(default_factory=list)
    risk_summary: list[CorrectiveActionRiskSummary] = Field(default_factory=list)
    overdue_summary: list[CorrectiveActionOverdueSummary] = Field(default_factory=list)
