"""Pydantic schemas for Reporting Runtime shell."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReportingOverviewSummary(BaseModel):
    reporting_center_name: str = "Reporting Brain Runtime Shell"
    owner_module: str = "reporting_runtime"
    active_reporting_cycles: int = 0
    active_submissions: int = 0
    active_deadlines: int = 0
    source_modules: list[str] = Field(default_factory=list)
    read_only: bool = True


class ProviderReadinessSummary(BaseModel):
    owner_module: str = "regulatory_reporting_integration"
    provider_status_counts: dict[str, int] = Field(default_factory=dict)
    provider_readiness: str = "NON_LIVE_PROFILE_ONLY"
    blocker_count: int = 0
    warning_count: int = 0
    live_integrations_enabled: bool = False
    sync_enabled: bool = False
    submission_execution_enabled: bool = False
    source_modules: list[str] = Field(default_factory=list)
    read_only: bool = True


class ComplianceSummary(BaseModel):
    owner_module: str = "reporting_runtime"
    compliance_score: int = 0
    risk_band: str = "MEDIUM"
    source_modules: list[str] = Field(default_factory=list)
    read_only: bool = True


class DeadlineSummary(BaseModel):
    owner_module: str = "reporting_runtime"
    active_deadlines: int = 0
    overdue_deadlines: int = 0
    upcoming_deadlines: int = 0
    deadline_signals: list[str] = Field(default_factory=list)
    source_modules: list[str] = Field(default_factory=list)
    read_only: bool = True


class ReportingStatusSummary(BaseModel):
    open_items: int = 0
    in_review_items: int = 0
    blocked_items: int = 0
    read_only: bool = True


class ReportingRuntimeShellResponse(BaseModel):
    tenant_id: int
    reporting_center_name: str = "Reporting Brain Runtime Shell"
    active_reporting_cycles: int = 0
    active_submissions: int = 0
    active_deadlines: int = 0
    provider_readiness: ProviderReadinessSummary
    compliance_score: int = 0
    generated_at: datetime
    read_only: bool = True
    auditability_preserved: bool = True
    overview: ReportingOverviewSummary
    compliance: ComplianceSummary
    deadlines: DeadlineSummary
    reporting_status: ReportingStatusSummary
    widgets: list[str] = Field(default_factory=list)
    rbac_roles: list[str] = Field(default_factory=list)
