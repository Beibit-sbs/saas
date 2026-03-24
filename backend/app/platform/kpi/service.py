from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.platform.kpi.repository import KpiRepository

_SHARED_KPI_REPOSITORY = KpiRepository()
_kpi_repository = _SHARED_KPI_REPOSITORY


METRIC_TITLES: dict[str, str] = {
    "total_students": "Total Students",
    "total_enrollments": "Total Enrollments",
    "total_grades_submitted": "Total Grades Submitted",
    "total_active_subscriptions": "Active Subscriptions",
    "total_failed_jobs": "Failed Jobs",
    "total_failed_notifications": "Failed Notifications",
}


EVENT_METRIC_MAP: dict[str, str] = {
    "student.created": "total_students",
    "enrollment.created": "total_enrollments",
    "grade.submitted": "total_grades_submitted",
}


def clear_kpi_state() -> None:
    _kpi_repository.clear_state()


def refresh_tenant_metrics(*, tenant_id: int, uow: Any, snapshot_date: str | None = None) -> list[dict[str, Any]]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    day = snapshot_date or date.today().isoformat()

    analytics_latest = uow.analytics_repository.get_latest_kpi_snapshot(tenant_id=int(tenant_id), conn=conn)
    analytics_counts = dict((analytics_latest or {}).get("event_counts_json", {}))

    metric_values: dict[str, int] = {}
    if conn is None:
        for event_type, metric_key in EVENT_METRIC_MAP.items():
            metric_values[metric_key] = len(
                uow.analytics_repository.list_event_projections(
                    tenant_id=int(tenant_id),
                    event_type=event_type,
                    limit=1_000_000,
                    conn=conn,
                )
            )
    else:
        for event_type, metric_key in EVENT_METRIC_MAP.items():
            metric_values[metric_key] = repo.count_events_by_type(
                tenant_id=int(tenant_id),
                event_type=event_type,
                conn=conn,
            )

    subscription = uow.billing_repository.get_subscription(int(tenant_id), conn=conn)
    metric_values["total_active_subscriptions"] = 1 if subscription and subscription.get("status") == "active" else 0
    if conn is None:
        failed_jobs = uow.job_repository.list_for_tenant(int(tenant_id), status="failed", limit=1_000_000, conn=conn)
        metric_values["total_failed_jobs"] = len(failed_jobs)

        notifications = uow.notification_repository.list_for_tenant(int(tenant_id), limit=1_000_000, conn=conn)
        metric_values["total_failed_notifications"] = sum(
            1 for row in notifications if str(row.get("status", "")).lower() == "failed"
        )
    else:
        metric_values["total_failed_jobs"] = repo.count_failed_jobs(tenant_id=int(tenant_id), conn=conn)
        metric_values["total_failed_notifications"] = repo.count_failed_notifications(tenant_id=int(tenant_id), conn=conn)

    rows: list[dict[str, Any]] = []
    for metric_key, metric_value in metric_values.items():
        rows.append(
            repo.upsert_metric_snapshot(
                tenant_id=int(tenant_id),
                metric_key=metric_key,
                metric_value=int(metric_value),
                snapshot_date=day,
                metadata_json={
                    "title": METRIC_TITLES.get(metric_key, metric_key),
                    "source": "analytics_sink_v1" if metric_key in {
                        "total_students",
                        "total_enrollments",
                        "total_grades_submitted",
                    } else "platform_core",
                    "analytics_today": int(analytics_counts.get(_metric_key_to_event(metric_key), 0)),
                },
                conn=conn,
            )
        )

    rows.sort(key=lambda item: str(item["metric_key"]))
    return rows


def refresh_tenant_dashboard_snapshot(
    *,
    tenant_id: int,
    uow: Any,
    snapshot_date: str | None = None,
) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    day = snapshot_date or date.today().isoformat()

    metrics = refresh_tenant_metrics(tenant_id=int(tenant_id), uow=uow, snapshot_date=day)

    cards: list[dict[str, Any]] = []
    for metric in metrics:
        metric_key = str(metric["metric_key"])
        history = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=7,
            conn=conn,
        )
        cards.append(
            {
                "metric_key": metric_key,
                "title": METRIC_TITLES.get(metric_key, metric_key),
                "value": int(metric["metric_value"]),
                "trend_7d": [
                    {"snapshot_date": str(point["snapshot_date"]), "value": int(point["metric_value"])}
                    for point in history
                ],
                "metadata_json": dict(metric.get("metadata_json") or {}),
            }
        )

    payload = {
        "tenant_id": int(tenant_id),
        "snapshot_date": day,
        "cards": cards,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "kpi_metrics_engine_v1",
    }

    return repo.upsert_dashboard_snapshot(
        tenant_id=int(tenant_id),
        snapshot_date=day,
        snapshot_json=payload,
        conn=conn,
    )


def get_latest_tenant_metrics(*, tenant_id: int, uow: Any) -> list[dict[str, Any]]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    return repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)


def get_rector_dashboard(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)

    latest = repo.get_latest_dashboard_snapshot(tenant_id=int(tenant_id), conn=conn)
    if latest is None:
        latest = refresh_tenant_dashboard_snapshot(tenant_id=int(tenant_id), uow=uow)

    dashboard = dict(latest.get("snapshot_json") or {})
    if not dashboard:
        dashboard = {
            "tenant_id": int(tenant_id),
            "snapshot_date": str(latest["snapshot_date"]),
            "cards": [],
            "generated_at": latest.get("updated_at"),
            "source": "kpi_metrics_engine_v1",
        }
    return dashboard


def refresh_all_tenants(*, uow: Any) -> dict[str, int]:
    conn = getattr(uow, "conn", None)
    tenants = uow.tenant_repository.list_tenant_profiles(conn=conn)

    refreshed = 0
    failed = 0
    for tenant in tenants:
        tenant_id = int(tenant["tenant_id"])
        try:
            refresh_tenant_dashboard_snapshot(tenant_id=tenant_id, uow=uow)
            refreshed += 1
        except Exception:
            failed += 1
    return {"tenants_total": len(tenants), "refreshed": refreshed, "failed": failed}


def _metric_key_to_event(metric_key: str) -> str:
    for event_type, key in EVENT_METRIC_MAP.items():
        if key == metric_key:
            return event_type
    return ""
