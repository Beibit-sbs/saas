from __future__ import annotations

from typing import Any

from pydantic import BaseModel


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


class RectorDashboardReadSchema(BaseModel):
    tenant_id: int
    snapshot_date: str
    cards: list[RectorKpiCardSchema]
    generated_at: str | None = None
    data_as_of: str | None = None
    freshness_status: str | None = None
    served_at: str | None = None
    source: str = "kpi_metrics_engine_v1"
