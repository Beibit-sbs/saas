"""Phase LXXIII — Usage Tracking Router.

Endpoints:
  POST  /api/usage/events           — record a usage event
  GET   /api/usage/events           — list usage events for a tenant
  GET   /api/usage/sum              — sum a metric for a tenant
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.usage.service import (
    get_usage_sum,
    list_usage_events,
    record_usage_event,
)

router = APIRouter(prefix="/api/usage", tags=["usage"])


# ─── schemas ──────────────────────────────────────────────────────────────────


class RecordUsagePayload(BaseModel):
    tenant_id: int = Field(gt=0)
    metric: str = Field(min_length=1)
    value: int = Field(default=1, ge=1)


class UsageEventOut(BaseModel):
    id: int
    tenant_id: int
    metric: str
    value: int
    created_at: str


class UsageEventListOut(BaseModel):
    events: list[UsageEventOut]


class UsageSumOut(BaseModel):
    tenant_id: int
    metric: str
    total: int


# ─── POST /api/usage/events ───────────────────────────────────────────────────


@router.post("/events", response_model=UsageEventOut, status_code=201)
def record_event(payload: RecordUsagePayload) -> UsageEventOut:
    """Record a usage event for a tenant."""
    try:
        row = record_usage_event(
            tenant_id=payload.tenant_id,
            metric=payload.metric,
            value=payload.value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UsageEventOut(**row)


# ─── GET /api/usage/events ────────────────────────────────────────────────────


@router.get("/events", response_model=UsageEventListOut)
def list_events(
    tenant_id: int = Query(gt=0),
    metric: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
) -> UsageEventListOut:
    """List usage events for a tenant, optionally filtered by metric."""
    rows = list_usage_events(
        tenant_id=tenant_id,
        metric=metric,
        limit=limit,
    )
    return UsageEventListOut(events=[UsageEventOut(**r) for r in rows])


# ─── GET /api/usage/sum ───────────────────────────────────────────────────────


@router.get("/sum", response_model=UsageSumOut)
def get_sum(
    tenant_id: int = Query(gt=0),
    metric: str = Query(min_length=1),
    since: Optional[str] = Query(default=None),
) -> UsageSumOut:
    """Return the sum of a metric for a tenant."""
    total = get_usage_sum(tenant_id=tenant_id, metric=metric, since_iso=since)
    return UsageSumOut(tenant_id=tenant_id, metric=metric, total=total)
