"""Repository for the platform_events table.

Records lightweight platform events (reads, usage) for data platform purposes.
Separate from the outbox_events table which handles domain events for processing.
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class PlatformEventRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[int, dict[str, Any]] = {}
        self._counter = 0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM platform_events")
            return

        with self._lock:
            self._rows.clear()
            self._counter = 0

    def record(
        self,
        *,
        tenant_id: int,
        event_type: str,
        payload_json: dict[str, Any] | None = None,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_event_type = str(event_type).strip().lower()
        normalized_payload = dict(payload_json or {})

        if conn is None:
            with transaction() as tx:
                return self.record(
                    tenant_id=normalized_tenant_id,
                    event_type=normalized_event_type,
                    payload_json=normalized_payload,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO platform_events (tenant_id, event_type, payload_json, created_at)
                    VALUES (%s, %s, %s::jsonb, NOW())
                    RETURNING id, tenant_id, event_type, payload_json, created_at
                    """,
                    (
                        normalized_tenant_id,
                        normalized_event_type,
                        psycopg.types.json.Jsonb(normalized_payload),
                    ),
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "event_type": str(row[2]),
                "payload_json": dict(row[3] or {}),
                "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
            }

        with self._lock:
            self._counter += 1
            entry: dict[str, Any] = {
                "id": self._counter,
                "tenant_id": normalized_tenant_id,
                "event_type": normalized_event_type,
                "payload_json": normalized_payload,
                "created_at": self._now_iso(),
            }
            self._rows[self._counter] = entry
            return dict(entry)

    def list_for_tenant(
        self,
        tenant_id: int,
        *,
        event_type: str | None = None,
        limit: int = 100,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_limit = max(1, min(int(limit), 1000))
        normalized_type = str(event_type).strip().lower() if event_type else None

        if conn is None:
            with transaction() as tx:
                return self.list_for_tenant(
                    normalized_tenant_id,
                    event_type=normalized_type,
                    limit=normalized_limit,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            if normalized_type:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, tenant_id, event_type, payload_json, created_at
                        FROM platform_events
                        WHERE tenant_id = %s AND event_type = %s
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_type, normalized_limit),
                    )
                    rows = cur.fetchall()
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, tenant_id, event_type, payload_json, created_at
                        FROM platform_events
                        WHERE tenant_id = %s
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_limit),
                    )
                    rows = cur.fetchall()
            return [
                {
                    "id": int(r[0]),
                    "tenant_id": int(r[1]),
                    "event_type": str(r[2]),
                    "payload_json": dict(r[3] or {}),
                    "created_at": r[4].isoformat() if hasattr(r[4], "isoformat") else str(r[4]),
                }
                for r in rows
            ]

        with self._lock:
            rows = [
                dict(item)
                for item in self._rows.values()
                if int(item["tenant_id"]) == normalized_tenant_id
                and (normalized_type is None or str(item["event_type"]) == normalized_type)
            ]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows[:normalized_limit]

    def count_by_type_for_tenant(
        self,
        tenant_id: int,
        *,
        conn: object | None = None,
    ) -> dict[str, int]:
        """Return per-event-type counts for a tenant. Used in projection summary."""
        normalized_tenant_id = int(tenant_id)

        if conn is None:
            with transaction() as tx:
                return self.count_by_type_for_tenant(normalized_tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_type, COUNT(*) AS cnt
                    FROM platform_events
                    WHERE tenant_id = %s
                    GROUP BY event_type
                    """,
                    (normalized_tenant_id,),
                )
                rows = cur.fetchall()
            return {str(r[0]): int(r[1]) for r in rows}

        with self._lock:
            counts: dict[str, int] = {}
            for item in self._rows.values():
                if int(item["tenant_id"]) == normalized_tenant_id:
                    etype = str(item["event_type"])
                    counts[etype] = counts.get(etype, 0) + 1
        return counts
