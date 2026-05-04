from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.platform.developer.auth import require_developer_scope
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import ANALYTICS_EVENT_READ, ANALYTICS_KPI_READ
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork

from .schemas import (
    PlatformEventItemSchema,
    PlatformEventListSchema,
    PlatformEventSummarySchema,
    TenantAnalyticsKpiInsightListReadSchema,
    TenantAnalyticsKpiListReadSchema,
    TenantAnalyticsKpiRefreshHistoryReadSchema,
    TenantAnalyticsKpiRefreshReadSchema,
    TenantAnalyticsKpiRecommendationListReadSchema,
    TenantAnalyticsKpiTrendListReadSchema,
)
from app.modules.usage.service import get_usage_brain_context


router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics-kpi"],
    # A-009 Phase 2.1: Add permission_dependency guard (HIGH severity fix for 64 unguarded endpoints)
    dependencies=[Depends(permission_dependency("analytics.data.read"))],
)


async def _resolve_kpi_read_access(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_admin_user: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
    x_app_key: Annotated[str | None, Header(alias="X-App-Key")] = None,
    x_app_secret: Annotated[str | None, Header(alias="X-App-Secret")] = None,
) -> dict[str, int | Literal["internal_user", "external_client"]]:
    has_developer_headers = bool(x_app_key or x_app_secret)
    if has_developer_headers:
        if x_tenant_id is not None:
            raise HTTPException(status_code=400, detail="manual tenant override is forbidden for developer API")
        auth = require_developer_scope("analytics.read")(
            x_app_key=x_app_key,
            x_app_secret=x_app_secret,
            x_tenant_id=None,
        )
        return {"tenant_id": int(auth["tenant_id"]), "access_mode": "external_client"}

    # Internal path remains token/session based and tenant-scoped via existing dependencies.
    tenant = await get_current_tenant(
        request=request,
        authorization=authorization,
        x_tenant_id=x_tenant_id,
    )
    await get_actor(
        request=request,
        authorization=authorization,
        x_admin_user=x_admin_user,
    )

    return {"tenant_id": int((tenant or {}).get("id") or 0), "access_mode": "internal_user"}


@router.get("/kpis", response_model=TenantAnalyticsKpiListReadSchema)
def get_tenant_analytics_kpis(
    request: Request,
    access: Annotated[dict[str, int | Literal["internal_user", "external_client"]], Depends(_resolve_kpi_read_access)],
) -> TenantAnalyticsKpiListReadSchema:
    tenant_id = int(access.get("tenant_id") or 0)
    with UnitOfWork() as uow:
        payload = kpi_service.get_tenant_product_kpis(tenant_id=tenant_id, uow=uow)
        payload = kpi_service.attach_kpi_response_envelope(
            payload,
            request_id=getattr(request.state, "request_id", None),
        )
        event_ingestion_service.record_event(tenant_id, ANALYTICS_EVENT_READ, {"endpoint": "kpis"}, uow=uow)
    return TenantAnalyticsKpiListReadSchema.model_validate(payload)


@router.post("/kpis/refresh", response_model=TenantAnalyticsKpiRefreshReadSchema)
def refresh_tenant_analytics_kpis(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    _write_perm: Annotated[None, Depends(permission_dependency("analytics.data.write"))] = None,
) -> TenantAnalyticsKpiRefreshReadSchema:
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        payload = kpi_service.execute_tenant_product_kpi_refresh(tenant_id=tenant_id, uow=uow)
    return TenantAnalyticsKpiRefreshReadSchema.model_validate(payload)


@router.get("/kpis/refresh-history", response_model=TenantAnalyticsKpiRefreshHistoryReadSchema)
def get_tenant_analytics_kpi_refresh_history(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    limit: Annotated[int, Query(description="Bounded refresh history length", ge=1, le=50)] = 10,
) -> TenantAnalyticsKpiRefreshHistoryReadSchema:
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        payload = kpi_service.get_tenant_product_kpi_refresh_history(tenant_id=tenant_id, uow=uow, limit=limit)
    return TenantAnalyticsKpiRefreshHistoryReadSchema.model_validate(payload)


@router.get("/kpis/trends", response_model=TenantAnalyticsKpiTrendListReadSchema)
def get_tenant_analytics_kpi_trends(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    window_days: Annotated[int, Query(description="Bounded trend window in days", ge=1)] = 30,
) -> TenantAnalyticsKpiTrendListReadSchema:
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        payload = kpi_service.get_tenant_product_kpi_trends(
            tenant_id=tenant_id,
            uow=uow,
            window_days=window_days,
        )
        event_ingestion_service.record_event(tenant_id, ANALYTICS_KPI_READ, {"endpoint": "kpis/trends", "window_days": window_days}, uow=uow)
    return TenantAnalyticsKpiTrendListReadSchema.model_validate(payload)


@router.get("/kpis/insights", response_model=TenantAnalyticsKpiInsightListReadSchema)
def get_tenant_analytics_kpi_insights(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    window_days: Annotated[int, Query(description="Bounded insight window in days", ge=1)] = 30,
) -> TenantAnalyticsKpiInsightListReadSchema:
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        payload = kpi_service.get_tenant_product_kpi_insights(
            tenant_id=tenant_id,
            uow=uow,
            window_days=window_days,
        )
        event_ingestion_service.record_event(tenant_id, ANALYTICS_KPI_READ, {"endpoint": "kpis/insights", "window_days": window_days}, uow=uow)
    return TenantAnalyticsKpiInsightListReadSchema.model_validate(payload)


@router.get("/kpis/recommendations", response_model=TenantAnalyticsKpiRecommendationListReadSchema)
def get_tenant_analytics_kpi_recommendations(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    window_days: Annotated[int, Query(description="Bounded recommendation window in days", ge=1)] = 30,
) -> TenantAnalyticsKpiRecommendationListReadSchema:
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        payload = kpi_service.get_tenant_product_kpi_recommendations(
            tenant_id=tenant_id,
            uow=uow,
            window_days=window_days,
        )
        event_ingestion_service.record_event(tenant_id, ANALYTICS_KPI_READ, {"endpoint": "kpis/recommendations", "window_days": window_days}, uow=uow)
    return TenantAnalyticsKpiRecommendationListReadSchema.model_validate(payload)


# ---------------------------------------------------------------------------
# Event projection / read layer v1
# ---------------------------------------------------------------------------

_EVENT_LIMIT_MAX = 200
_EVENT_LIMIT_DEFAULT = 50


@router.get("/events", response_model=PlatformEventListSchema)
def get_tenant_recent_events(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
    event_type: Annotated[str | None, Query(description="Filter by event type")] = None,
    limit: Annotated[int, Query(description="Max events to return", ge=1, le=_EVENT_LIMIT_MAX)] = _EVENT_LIMIT_DEFAULT,
) -> PlatformEventListSchema:
    """Return recent platform events for the current tenant.

    Tenant-scoped — callers only see their own events.
    Ordered newest-first. No cross-tenant access.
    """
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        raw = event_ingestion_service.list_events_for_tenant(
            tenant_id, event_type=event_type, limit=limit, uow=uow
        )
    items = [
        PlatformEventItemSchema(
            id=int(e["id"]),
            event_type=str(e["event_type"]),
            created_at=str(e["created_at"]),
            payload=dict(e["payload_json"]),
        )
        for e in raw
    ]
    return PlatformEventListSchema(tenant_id=tenant_id, items=items, count=len(items))


@router.get("/events/summary", response_model=PlatformEventSummarySchema)
def get_tenant_event_summary(
    _actor: Annotated[str, Depends(get_actor)],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> PlatformEventSummarySchema:
    """Return a projection of event counts grouped by event_type for the current tenant.

    Simple rule-based aggregation — no ETL or materialized views.
    Tenant-scoped — no cross-tenant leakage.
    """
    tenant_id = int(tenant.get("id") or 0)
    with UnitOfWork() as uow:
        counts = event_ingestion_service.summary_for_tenant(tenant_id, uow=uow)
    return PlatformEventSummarySchema(
        tenant_id=tenant_id,
        counts_by_type=counts,
        total=sum(counts.values()),
    )


@router.get("/brain-context", response_model=dict, tags=["analytics-kpi", "brain-core"])
def get_analytics_brain_context(
    access: Annotated[dict[str, int | Literal["internal_user", "external_client"]], Depends(_resolve_kpi_read_access)],
) -> dict:
    """Return usage context snapshot for Brain Core enrichment.

    Tenant-scoped — no cross-tenant data leakage.
    """
    tenant_id = int(access.get("tenant_id") or 0)
    return get_usage_brain_context(tenant_id=tenant_id)
