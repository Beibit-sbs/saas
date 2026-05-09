from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TenantMetricSnapshotReadSchema(BaseModel):
    id: int
    tenant_id: int
    metric_key: str
    metric_value: int
    snapshot_date: str
    metadata_json: dict[str, Any]
    created_at: str
    updated_at: str
    version: int


class TenantDashboardSnapshotReadSchema(BaseModel):
    id: int
    tenant_id: int
    snapshot_date: str
    snapshot_json: dict[str, Any]
    created_at: str
    updated_at: str
    version: int


class RectorTrendPointSchema(BaseModel):
    snapshot_date: str
    value: int


class RectorKpiCardSchema(BaseModel):
    metric_key: str
    title: str
    value: int
    trend_7d: list[RectorTrendPointSchema]
    metadata_json: dict[str, Any]


class RectorKpiEvidenceSourceSchema(BaseModel):
    metric_key: str
    label: str
    value_label: str
    source_domain: str
    interpretation: str
    available: bool
    lineage: dict[str, Any] | None = None


class RectorKpiEvidenceDrilldownSchema(BaseModel):
    drilldown_id: str
    title: str
    domain_id: str
    domain_title: str
    source_metrics: list[str]
    source_domains: list[str]
    evidence_summary: str
    explanation: str
    risk_level: str
    review_required: bool
    data_quality_note: str
    readonly: bool = True
    tenant_scoped: bool = True
    optional: bool = False
    evidence_sources: list[RectorKpiEvidenceSourceSchema]


class RectorDashboardReadSchema(BaseModel):
    tenant_id: int
    snapshot_date: str
    cards: list[RectorKpiCardSchema]
    drilldowns: list[RectorKpiEvidenceDrilldownSchema] = Field(default_factory=list)
    generated_at: str | None = None
    data_as_of: str | None = None
    freshness_status: str | None = None
    served_at: str | None = None
    source: str = "kpi_metrics_engine_v1"


class RectorKpiDrilldownSummarySchema(BaseModel):
    tenant_id: int
    snapshot_date: str
    generated_at: str
    domains: list[RectorKpiEvidenceDrilldownSchema]
    total_domains: int
    review_required_count: int
    unavailable_domains_count: int
    critical_domains_count: int
    high_domains_count: int
    source: str = "kpi_metrics_engine_v1"
    readonly: bool = True
    tenant_scoped: bool = True
    no_policy_enforcement: bool = True
    no_autonomous_decision: bool = True
    no_remediation_action: bool = True
