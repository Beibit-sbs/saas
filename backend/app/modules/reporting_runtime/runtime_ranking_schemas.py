"""Pydantic schemas for Ranking Reporting runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _RankingReportingBase(BaseModel):
    id: str
    ranking_system: str
    indicator_name: str
    indicator_score: int
    benchmark_score: int
    trend_direction: str
    readiness_level: str
    risk_level: str
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class RankingReportingSummary(_RankingReportingBase):
    pass


class RankingIndicatorSummary(_RankingReportingBase):
    indicator_weight: int


class RankingReadinessSummary(_RankingReportingBase):
    readiness_score: int


class RankingBenchmarkSummary(_RankingReportingBase):
    benchmark_gap: int


class RankingTrendSummary(_RankingReportingBase):
    trend_delta: int


class RankingRiskSummary(_RankingReportingBase):
    signal_name: str
    signal_owner_module: str = "brain_core"


class RankingReportingResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    reports: list[RankingReportingSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class RankingIndicatorResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    indicators: list[RankingIndicatorSummary] = Field(default_factory=list)


class RankingReadinessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    readiness: list[RankingReadinessSummary] = Field(default_factory=list)


class RankingBenchmarkResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    benchmarks: list[RankingBenchmarkSummary] = Field(default_factory=list)


class RankingTrendResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    trends: list[RankingTrendSummary] = Field(default_factory=list)


class RankingRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[RankingRiskSummary] = Field(default_factory=list)
