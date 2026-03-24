from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class KpiRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._metric_counter = 0
        self._dashboard_counter = 0
        self._metric_rows: dict[tuple[int, str, str], dict[str, Any]] = {}
        self._dashboard_rows: dict[tuple[int, str], dict[str, Any]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def clear_state(self) -> None:
        with self._lock:
            self._metric_counter = 0
            self._dashboard_counter = 0
            self._metric_rows.clear()
            self._dashboard_rows.clear()

    def upsert_metric_snapshot(
        self,
        *,
        tenant_id: int,
        metric_key: str,
        metric_value: int,
        snapshot_date: str,
        metadata_json: dict[str, Any] | None = None,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_key = str(metric_key).strip().lower()
        normalized_metadata = dict(metadata_json or {})

        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.upsert_metric_snapshot(
                        tenant_id=tenant_id,
                        metric_key=normalized_key,
                        metric_value=metric_value,
                        snapshot_date=snapshot_date,
                        metadata_json=normalized_metadata,
                        conn=tx,
                    )
            with self._lock:
                key = (int(tenant_id), normalized_key, str(snapshot_date))
                current = self._metric_rows.get(key)
                now_iso = self._now_iso()
                if current is None:
                    self._metric_counter += 1
                    current = {
                        "id": self._metric_counter,
                        "tenant_id": int(tenant_id),
                        "metric_key": normalized_key,
                        "metric_value": int(metric_value),
                        "snapshot_date": str(snapshot_date),
                        "metadata_json": normalized_metadata,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                        "version": 1,
                    }
                    self._metric_rows[key] = current
                else:
                    current["metric_value"] = int(metric_value)
                    current["metadata_json"] = normalized_metadata
                    current["updated_at"] = now_iso
                    current["version"] = int(current["version"]) + 1
                return dict(current)

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.upsert_metric_snapshot(
                tenant_id=tenant_id,
                metric_key=normalized_key,
                metric_value=metric_value,
                snapshot_date=snapshot_date,
                metadata_json=normalized_metadata,
                conn=None,
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_platform_tenant_metric_snapshots
                    (tenant_id, metric_key, metric_value, snapshot_date, metadata_json, version)
                VALUES (%s, %s, %s, %s::date, %s::jsonb, 1)
                ON CONFLICT (tenant_id, metric_key, snapshot_date) DO UPDATE
                    SET metric_value = EXCLUDED.metric_value,
                        metadata_json = EXCLUDED.metadata_json,
                        updated_at = NOW(),
                        version = app_platform_tenant_metric_snapshots.version + 1
                RETURNING id, tenant_id, metric_key, metric_value, snapshot_date, metadata_json, created_at, updated_at, version
                """,
                (
                    int(tenant_id),
                    normalized_key,
                    int(metric_value),
                    str(snapshot_date),
                    psycopg.types.json.Jsonb(normalized_metadata),
                ),
            )
            row_db = cur.fetchone()
        return _metric_row_to_dict(row_db)

    def list_latest_metrics(
        self,
        *,
        tenant_id: int,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.list_latest_metrics(tenant_id=tenant_id, conn=tx)
            with self._lock:
                rows = [row for row in self._metric_rows.values() if int(row["tenant_id"]) == int(tenant_id)]
            if not rows:
                return []
            latest_date = max(str(item["snapshot_date"]) for item in rows)
            filtered = [dict(item) for item in rows if str(item["snapshot_date"]) == latest_date]
            filtered.sort(key=lambda item: str(item["metric_key"]))
            return filtered

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.list_latest_metrics(tenant_id=tenant_id, conn=None)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT MAX(snapshot_date)
                FROM app_platform_tenant_metric_snapshots
                WHERE tenant_id = %s
                """,
                (int(tenant_id),),
            )
            latest_date = cur.fetchone()[0]
            if latest_date is None:
                return []
            cur.execute(
                """
                SELECT id, tenant_id, metric_key, metric_value, snapshot_date, metadata_json, created_at, updated_at, version
                FROM app_platform_tenant_metric_snapshots
                WHERE tenant_id = %s AND snapshot_date = %s::date
                ORDER BY metric_key ASC
                """,
                (int(tenant_id), latest_date.isoformat() if hasattr(latest_date, "isoformat") else str(latest_date)),
            )
            db_rows = cur.fetchall()
        return [_metric_row_to_dict(row) for row in db_rows]

    def list_metric_history(
        self,
        *,
        tenant_id: int,
        metric_key: str,
        days: int = 7,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_days = max(1, min(int(days), 30))
        normalized_key = str(metric_key).strip().lower()

        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.list_metric_history(
                        tenant_id=tenant_id,
                        metric_key=normalized_key,
                        days=normalized_days,
                        conn=tx,
                    )
            with self._lock:
                rows = [
                    dict(item)
                    for item in self._metric_rows.values()
                    if int(item["tenant_id"]) == int(tenant_id)
                    and str(item["metric_key"]) == normalized_key
                ]
            rows.sort(key=lambda item: str(item["snapshot_date"]))
            return rows[-normalized_days:]

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.list_metric_history(
                tenant_id=tenant_id,
                metric_key=normalized_key,
                days=normalized_days,
                conn=None,
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, metric_key, metric_value, snapshot_date, metadata_json, created_at, updated_at, version
                FROM app_platform_tenant_metric_snapshots
                WHERE tenant_id = %s
                  AND metric_key = %s
                ORDER BY snapshot_date DESC
                LIMIT %s
                """,
                (int(tenant_id), normalized_key, normalized_days),
            )
            db_rows = cur.fetchall()
        rows = [_metric_row_to_dict(row) for row in db_rows]
        rows.reverse()
        return rows

    def upsert_dashboard_snapshot(
        self,
        *,
        tenant_id: int,
        snapshot_date: str,
        snapshot_json: dict[str, Any],
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_snapshot = dict(snapshot_json)

        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.upsert_dashboard_snapshot(
                        tenant_id=tenant_id,
                        snapshot_date=snapshot_date,
                        snapshot_json=normalized_snapshot,
                        conn=tx,
                    )
            with self._lock:
                key = (int(tenant_id), str(snapshot_date))
                current = self._dashboard_rows.get(key)
                now_iso = self._now_iso()
                if current is None:
                    self._dashboard_counter += 1
                    current = {
                        "id": self._dashboard_counter,
                        "tenant_id": int(tenant_id),
                        "snapshot_date": str(snapshot_date),
                        "snapshot_json": normalized_snapshot,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                        "version": 1,
                    }
                    self._dashboard_rows[key] = current
                else:
                    current["snapshot_json"] = normalized_snapshot
                    current["updated_at"] = now_iso
                    current["version"] = int(current["version"]) + 1
                return dict(current)

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.upsert_dashboard_snapshot(
                tenant_id=tenant_id,
                snapshot_date=snapshot_date,
                snapshot_json=normalized_snapshot,
                conn=None,
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_platform_tenant_dashboard_snapshots
                    (tenant_id, snapshot_date, snapshot_json, version)
                VALUES (%s, %s::date, %s::jsonb, 1)
                ON CONFLICT (tenant_id, snapshot_date) DO UPDATE
                    SET snapshot_json = EXCLUDED.snapshot_json,
                        updated_at = NOW(),
                        version = app_platform_tenant_dashboard_snapshots.version + 1
                RETURNING id, tenant_id, snapshot_date, snapshot_json, created_at, updated_at, version
                """,
                (
                    int(tenant_id),
                    str(snapshot_date),
                    psycopg.types.json.Jsonb(normalized_snapshot),
                ),
            )
            row_db = cur.fetchone()
        return _dashboard_row_to_dict(row_db)

    def get_latest_dashboard_snapshot(self, *, tenant_id: int, conn: object | None = None) -> dict[str, Any] | None:
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.get_latest_dashboard_snapshot(tenant_id=tenant_id, conn=tx)
            with self._lock:
                rows = [dict(item) for item in self._dashboard_rows.values() if int(item["tenant_id"]) == int(tenant_id)]
            if not rows:
                return None
            return max(rows, key=lambda item: str(item["snapshot_date"]))

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.get_latest_dashboard_snapshot(tenant_id=tenant_id, conn=None)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, snapshot_date, snapshot_json, created_at, updated_at, version
                FROM app_platform_tenant_dashboard_snapshots
                WHERE tenant_id = %s
                ORDER BY snapshot_date DESC
                LIMIT 1
                """,
                (int(tenant_id),),
            )
            row_db = cur.fetchone()
        if row_db is None:
            return None
        return _dashboard_row_to_dict(row_db)

    def count_events_by_type(
        self,
        *,
        tenant_id: int,
        event_type: str,
        conn: object | None = None,
    ) -> int:
        normalized_event_type = str(event_type).strip().lower()
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.count_events_by_type(tenant_id=tenant_id, event_type=normalized_event_type, conn=tx)
            from app.platform.analytics.repository import AnalyticsRepository  # noqa: PLC0415

            analytics_repo = AnalyticsRepository()
            rows = analytics_repo.list_event_projections(
                tenant_id=int(tenant_id),
                event_type=normalized_event_type,
                limit=1_000_000,
                conn=None,
            )
            return len(rows)

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.count_events_by_type(tenant_id=tenant_id, event_type=normalized_event_type, conn=None)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM app_platform_analytics_events
                WHERE tenant_id = %s
                  AND event_type = %s
                """,
                (int(tenant_id), normalized_event_type),
            )
            count = cur.fetchone()[0]
        return int(count)

    def count_failed_jobs(self, *, tenant_id: int, conn: object | None = None) -> int:
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.count_failed_jobs(tenant_id=tenant_id, conn=tx)
            from app.platform.repository.job_repository import JobRepository  # noqa: PLC0415

            rows = JobRepository().list_for_tenant(int(tenant_id), status="failed", limit=5000, conn=None)
            return len(rows)

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.count_failed_jobs(tenant_id=tenant_id, conn=None)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM app_platform_jobs
                WHERE tenant_id = %s
                  AND status = 'failed'
                """,
                (int(tenant_id),),
            )
            count = cur.fetchone()[0]
        return int(count)

    def count_failed_notifications(self, *, tenant_id: int, conn: object | None = None) -> int:
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.count_failed_notifications(tenant_id=tenant_id, conn=tx)
            from app.platform.repository.notification_repository import NotificationRepository  # noqa: PLC0415

            rows = NotificationRepository().list_for_tenant(int(tenant_id), limit=5000, conn=None)
            return sum(1 for row in rows if str(row.get("status", "")).lower() == "failed")

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.count_failed_notifications(tenant_id=tenant_id, conn=None)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM app_platform_notifications
                WHERE tenant_id = %s
                  AND status = 'failed'
                """,
                (int(tenant_id),),
            )
            count = cur.fetchone()[0]
        return int(count)


def _metric_row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "tenant_id": int(row[1]),
        "metric_key": str(row[2]),
        "metric_value": int(row[3]),
        "snapshot_date": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
        "metadata_json": dict(row[5]) if row[5] is not None else {},
        "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
        "updated_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
        "version": int(row[8]),
    }


def _dashboard_row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "tenant_id": int(row[1]),
        "snapshot_date": row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
        "snapshot_json": dict(row[3]) if row[3] is not None else {},
        "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
        "updated_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
        "version": int(row[6]),
    }
