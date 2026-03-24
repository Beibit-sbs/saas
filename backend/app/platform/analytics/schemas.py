from __future__ import annotations

from pydantic import BaseModel


class AnalyticsEventProjectionRead(BaseModel):
    id: int
    tenant_id: int
    outbox_event_id: int
    event_type: str
    aggregate_type: str
    aggregate_id: str
    created_at: str


class AnalyticsEventProjectionListSchema(BaseModel):
    tenant_id: int
    total: int
    items: list[AnalyticsEventProjectionRead]


class TenantKpiSnapshotRead(BaseModel):
    id: int
    tenant_id: int
    snapshot_date: str
    event_counts_json: dict[str, int]
    total_events: int
    version: int
    updated_at: str
