from __future__ import annotations

from datetime import date
from datetime import datetime, timezone
from typing import Any

from app.platform.analytics.repository import AnalyticsRepository
from app.platform.events.schemas import OutboxEventRead

# Circular-import guard: UnitOfWork is only imported inside functions
_SHARED_ANALYTICS_REPOSITORY = AnalyticsRepository()

_analytics_repository = _SHARED_ANALYTICS_REPOSITORY


def clear_analytics_state() -> None:
    _analytics_repository.clear_state()


def record_event_projection(event: OutboxEventRead, *, uow: "Any") -> dict[str, Any] | None:
    """Append an event projection row and bump today's KPI snapshot."""
    repo: AnalyticsRepository = uow.analytics_repository
    conn = getattr(uow, "conn", None)

    projection = repo.append_event_projection(
        tenant_id=event.tenant_id,
        outbox_event_id=event.id,
        event_type=event.event_type,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        conn=conn,
    )
    # Always increment KPI, even if projection was a duplicate — no, only when
    # projection was actually inserted (non-None means new row).
    if projection is not None:
        today = datetime.now(timezone.utc).date().isoformat()
        repo.increment_kpi_snapshot(
            tenant_id=event.tenant_id,
            snapshot_date=today,
            event_type=event.event_type,
            conn=conn,
        )
    return projection


def refresh_tenant_kpis(*, tenant_id: int, uow: "Any") -> dict[str, Any]:
    """Recompute KPI snapshot for today from the projections table."""
    repo: AnalyticsRepository = uow.analytics_repository
    conn = getattr(uow, "conn", None)
    today = datetime.now(timezone.utc).date().isoformat()
    return repo.recompute_kpi_snapshot(
        tenant_id=tenant_id,
        snapshot_date=today,
        conn=conn,
    )


def list_event_projections(
    *,
    tenant_id: int,
    event_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    cursor_id_lt: int | None = None,
    ordering: str = "created_at_desc",
    limit: int = 100,
    uow: "Any",
) -> list[dict[str, Any]]:
    repo: AnalyticsRepository = uow.analytics_repository
    conn = getattr(uow, "conn", None)
    return repo.list_event_projections(
        tenant_id=tenant_id,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
        cursor_id_lt=cursor_id_lt,
        ordering=ordering,
        limit=limit,
        conn=conn,
    )


def get_latest_tenant_kpis(*, tenant_id: int, uow: "Any") -> dict[str, Any] | None:
    repo: AnalyticsRepository = uow.analytics_repository
    conn = getattr(uow, "conn", None)
    return repo.get_latest_kpi_snapshot(tenant_id=tenant_id, conn=conn)
