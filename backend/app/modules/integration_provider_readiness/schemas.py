"""Pydantic schemas for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GovernanceMutationRequest(BaseModel):
    status: str = "draft"
    payload: dict[str, Any] = Field(default_factory=dict)
    reason_code: str | None = None
    note: str | None = None


class GovernanceRecordRead(BaseModel):
    id: int
    tenant_id: int
    provider_id: str
    record_type: str
    status: str
    payload: dict[str, Any]
    readiness_only: bool
    provider_connected: bool
    live_provider_calls: bool
    credentials_stored: bool
    external_submission: bool
    sync_execution: bool
    fake_health_metrics: bool
    fake_readiness_metrics: bool


class GovernanceListRead(BaseModel):
    items: list[GovernanceRecordRead]
    total: int


class DashboardContractRead(BaseModel):
    dashboard_name: str
    required_permission: str
    tenant_scope: str
    readiness_only: bool
    fake_metrics: bool
    provider_connected: bool
    live_provider_calls: bool
    external_submission: bool
    data: dict[str, Any]


class DashboardContractListRead(BaseModel):
    items: list[DashboardContractRead]
    total: int


class HealthSummaryRead(BaseModel):
    tenant_id: int
    total_providers: int
    readiness_only: bool
    fake_metrics: bool
    provider_connected: bool
    live_provider_calls: bool
    external_submission: bool
    data: dict[str, Any]
