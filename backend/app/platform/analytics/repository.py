from __future__ import annotations

from datetime import date, datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class AnalyticsRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._event_counter = 0
        self._kpi_counter = 0
        self._events: dict[int, dict[str, Any]] = {}
        # key: outbox_event_id → event row id  (for idempotency)
        self._event_by_outbox_id: dict[int, int] = {}
        self._kpis: dict[tuple[int, str], dict[str, Any]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def clear_state(self) -> None:
        with self._lock:
            self._event_counter = 0
            self._kpi_counter = 0
            self._events.clear()
            self._event_by_outbox_id.clear()
            self._kpis.clear()

    # ------------------------------------------------------------------
    # Event projections
    # ------------------------------------------------------------------

    def append_event_projection(
        self,
        *,
        tenant_id: int,
        outbox_event_id: int,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        """Insert projection row, silently skipping duplicates (idempotent)."""
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.append_event_projection(
                        tenant_id=tenant_id,
                        outbox_event_id=outbox_event_id,
                        event_type=event_type,
                        aggregate_type=aggregate_type,
                        aggregate_id=aggregate_id,
                        conn=tx,
                    )
            # in-memory fallback
            with self._lock:
                if outbox_event_id in self._event_by_outbox_id:
                    return None
                self._event_counter += 1
                row: dict[str, Any] = {
                    "id": self._event_counter,
                    "tenant_id": tenant_id,
                    "outbox_event_id": outbox_event_id,
                    "event_type": event_type,
                    "aggregate_type": aggregate_type,
                    "aggregate_id": aggregate_id,
                    "created_at": self._now_iso(),
                }
                self._events[self._event_counter] = row
                self._event_by_outbox_id[outbox_event_id] = self._event_counter
                return row

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.append_event_projection(
                tenant_id=tenant_id,
                outbox_event_id=outbox_event_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                conn=None,
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_platform_analytics_events
                    (tenant_id, outbox_event_id, event_type, aggregate_type, aggregate_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (outbox_event_id) DO NOTHING
                RETURNING
                    id, tenant_id, outbox_event_id, event_type,
                    aggregate_type, aggregate_id,
                    created_at
                """,
                (tenant_id, outbox_event_id, event_type, aggregate_type, aggregate_id),
            )
            row_db = cur.fetchone()
        if row_db is None:
            return None
        return {
            "id": int(row_db[0]),
            "tenant_id": int(row_db[1]),
            "outbox_event_id": int(row_db[2]),
            "event_type": str(row_db[3]),
            "aggregate_type": str(row_db[4]),
            "aggregate_id": str(row_db[5]),
            "created_at": row_db[6].isoformat() if hasattr(row_db[6], "isoformat") else str(row_db[6]),
        }

    def list_event_projections(
        self,
        *,
        tenant_id: int,
        event_type: str | None = None,
        limit: int = 100,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.list_event_projections(
                        tenant_id=tenant_id,
                        event_type=event_type,
                        limit=limit,
                        conn=tx,
                    )
            with self._lock:
                rows = [
                    r for r in self._events.values()
                    if r["tenant_id"] == tenant_id
                    and (event_type is None or r["event_type"] == event_type)
                ]
                rows.sort(key=lambda r: r["id"], reverse=True)
                return rows[:limit]

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.list_event_projections(
                tenant_id=tenant_id,
                event_type=event_type,
                limit=limit,
                conn=None,
            )

        if event_type is not None:
            sql = (
                "SELECT id, tenant_id, outbox_event_id, event_type, aggregate_type, aggregate_id, created_at "
                "FROM app_platform_analytics_events "
                "WHERE tenant_id = %s AND event_type = %s "
                "ORDER BY id DESC LIMIT %s"
            )
            params: tuple[Any, ...] = (tenant_id, event_type, limit)
        else:
            sql = (
                "SELECT id, tenant_id, outbox_event_id, event_type, aggregate_type, aggregate_id, created_at "
                "FROM app_platform_analytics_events "
                "WHERE tenant_id = %s "
                "ORDER BY id DESC LIMIT %s"
            )
            params = (tenant_id, limit)

        with conn.cursor() as cur:
            cur.execute(sql, params)
            db_rows = cur.fetchall()
        return [
            {
                "id": int(r[0]),
                "tenant_id": int(r[1]),
                "outbox_event_id": int(r[2]),
                "event_type": str(r[3]),
                "aggregate_type": str(r[4]),
                "aggregate_id": str(r[5]),
                "created_at": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
            }
            for r in db_rows
        ]

    # ------------------------------------------------------------------
    # KPI snapshots
    # ------------------------------------------------------------------

    def increment_kpi_snapshot(
        self,
        *,
        tenant_id: int,
        snapshot_date: str,
        event_type: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        """Atomically increment the counter for one event_type in today's KPI row."""
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.increment_kpi_snapshot(
                        tenant_id=tenant_id,
                        snapshot_date=snapshot_date,
                        event_type=event_type,
                        conn=tx,
                    )
            with self._lock:
                key = (tenant_id, snapshot_date)
                if key not in self._kpis:
                    self._kpi_counter += 1
                    self._kpis[key] = {
                        "id": self._kpi_counter,
                        "tenant_id": tenant_id,
                        "snapshot_date": snapshot_date,
                        "event_counts_json": {},
                        "total_events": 0,
                        "version": 1,
                        "updated_at": self._now_iso(),
                    }
                snap = self._kpis[key]
                counts: dict[str, int] = snap["event_counts_json"]
                counts[event_type] = counts.get(event_type, 0) + 1
                snap["total_events"] = snap["total_events"] + 1
                snap["version"] = snap["version"] + 1
                snap["updated_at"] = self._now_iso()
                return dict(snap)

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.increment_kpi_snapshot(
                tenant_id=tenant_id,
                snapshot_date=snapshot_date,
                event_type=event_type,
                conn=None,
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_platform_tenant_kpi_snapshots
                    (tenant_id, snapshot_date, event_counts_json, total_events, version)
                VALUES (%s, %s::date, %s::jsonb, 1, 1)
                ON CONFLICT (tenant_id, snapshot_date) DO UPDATE
                    SET event_counts_json = (
                            app_platform_tenant_kpi_snapshots.event_counts_json ||
                            jsonb_build_object(
                                %s,
                                COALESCE((app_platform_tenant_kpi_snapshots.event_counts_json->>%s)::bigint, 0) + 1
                            )
                        ),
                        total_events = app_platform_tenant_kpi_snapshots.total_events + 1,
                        version      = app_platform_tenant_kpi_snapshots.version + 1,
                        updated_at   = NOW()
                RETURNING id, tenant_id, snapshot_date, event_counts_json, total_events, version, updated_at
                """,
                (
                    tenant_id,
                    snapshot_date,
                    f'{{"{event_type}": 1}}',
                    event_type,
                    event_type,
                ),
            )
            row_db = cur.fetchone()
        return _kpi_row_to_dict(row_db)

    def get_latest_kpi_snapshot(
        self,
        *,
        tenant_id: int,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.get_latest_kpi_snapshot(tenant_id=tenant_id, conn=tx)
            with self._lock:
                snaps = [v for k, v in self._kpis.items() if k[0] == tenant_id]
                if not snaps:
                    return None
                return dict(max(snaps, key=lambda s: s["snapshot_date"]))

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.get_latest_kpi_snapshot(tenant_id=tenant_id, conn=None)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, snapshot_date, event_counts_json, total_events, version, updated_at
                FROM app_platform_tenant_kpi_snapshots
                WHERE tenant_id = %s
                ORDER BY snapshot_date DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            row_db = cur.fetchone()
        if row_db is None:
            return None
        return _kpi_row_to_dict(row_db)

    def recompute_kpi_snapshot(
        self,
        *,
        tenant_id: int,
        snapshot_date: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        """Full recount from projections table for a given date."""
        if conn is None:
            if db_available():
                with transaction() as tx:
                    return self.recompute_kpi_snapshot(
                        tenant_id=tenant_id,
                        snapshot_date=snapshot_date,
                        conn=tx,
                    )
            with self._lock:
                date_prefix = snapshot_date[:10]
                counts: dict[str, int] = {}
                for r in self._events.values():
                    if r["tenant_id"] == tenant_id and r["created_at"][:10] == date_prefix:
                        counts[r["event_type"]] = counts.get(r["event_type"], 0) + 1
                total = sum(counts.values())
                key = (tenant_id, snapshot_date)
                if key in self._kpis:
                    snap = self._kpis[key]
                    snap["event_counts_json"] = counts
                    snap["total_events"] = total
                    snap["version"] = snap["version"] + 1
                    snap["updated_at"] = self._now_iso()
                else:
                    self._kpi_counter += 1
                    snap = {
                        "id": self._kpi_counter,
                        "tenant_id": tenant_id,
                        "snapshot_date": snapshot_date,
                        "event_counts_json": counts,
                        "total_events": total,
                        "version": 1,
                        "updated_at": self._now_iso(),
                    }
                    self._kpis[key] = snap
                return dict(snap)

        from app.platform.repository.db import _MEMORY_TX  # noqa: PLC0415

        if conn is _MEMORY_TX:
            return self.recompute_kpi_snapshot(
                tenant_id=tenant_id,
                snapshot_date=snapshot_date,
                conn=None,
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_type, COUNT(*) AS cnt
                FROM app_platform_analytics_events
                WHERE tenant_id = %s
                  AND DATE(created_at) = %s::date
                GROUP BY event_type
                """,
                (tenant_id, snapshot_date),
            )
            count_rows = cur.fetchall()

        counts_recomputed: dict[str, int] = {str(r[0]): int(r[1]) for r in count_rows}
        total_recomputed = sum(counts_recomputed.values())

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_platform_tenant_kpi_snapshots
                    (tenant_id, snapshot_date, event_counts_json, total_events, version)
                VALUES (%s, %s::date, %s::jsonb, %s, 1)
                ON CONFLICT (tenant_id, snapshot_date) DO UPDATE
                    SET event_counts_json = EXCLUDED.event_counts_json,
                        total_events      = EXCLUDED.total_events,
                        version           = app_platform_tenant_kpi_snapshots.version + 1,
                        updated_at        = NOW()
                RETURNING id, tenant_id, snapshot_date, event_counts_json, total_events, version, updated_at
                """,
                (tenant_id, snapshot_date, psycopg.types.json.Jsonb(counts_recomputed), total_recomputed),
            )
            row_db = cur.fetchone()
        return _kpi_row_to_dict(row_db)


def _kpi_row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "tenant_id": int(row[1]),
        "snapshot_date": row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
        "event_counts_json": dict(row[3]) if row[3] is not None else {},
        "total_events": int(row[4]),
        "version": int(row[5]),
        "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
    }
