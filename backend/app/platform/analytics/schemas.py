from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyticsEventProjectionRead(BaseModel):
    id: int
    tenant_id: int
    outbox_event_id: int
    event_type: str
    aggregate_type: str
    aggregate_id: str
    created_at: str


class AnalyticsEventProjectionAppliedFiltersSchema(BaseModel):
    event_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None


class AnalyticsEventProjectionListSchema(BaseModel):
    tenant_id: int
    total: int
    limit: int = 50
    ordering: str = "created_at_desc"
    next_cursor: str | None = None
    data_as_of: str | None = None
    freshness_status: str = "empty"
    served_at: str | None = None
    applied_filters: AnalyticsEventProjectionAppliedFiltersSchema = Field(
        default_factory=AnalyticsEventProjectionAppliedFiltersSchema
    )
    items: list[AnalyticsEventProjectionRead]


class TenantKpiSnapshotRead(BaseModel):
    id: int
    tenant_id: int
    snapshot_date: str
    event_counts_json: dict[str, int]
    total_events: int
    version: int
    updated_at: str
    data_as_of: str | None = None
    freshness_status: str = "stale"
    served_at: str | None = None
