from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class OutboxEventRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[int, dict[str, Any]] = {}
        self._counter = 0

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _now_iso(self) -> str:
        return self._now().isoformat()

    def _normalize_datetime(self, value: datetime | None) -> datetime:
        if value is None:
            return self._now()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _row_to_api(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "event_type": str(row[2]),
            "aggregate_type": str(row[3]),
            "aggregate_id": str(row[4]),
            "payload_json": dict(row[5] or {}),
            "status": str(row[6]),
            "retry_count": int(row[7]),
            "available_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
            "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
            "processed_at": row[10].isoformat() if hasattr(row[10], "isoformat") and row[10] is not None else (str(row[10]) if row[10] is not None else None),
            "last_error": row[11],
            "correlation_id": row[12],
            "causation_id": row[13],
        }

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_outbox_events")
            return

        with self._lock:
            self._rows.clear()
            self._counter = 0

    def enqueue(
        self,
        *,
        tenant_id: int,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload_json: dict[str, Any],
        available_at: datetime | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_event_type = event_type.strip().lower()
        normalized_aggregate_type = aggregate_type.strip().lower()
        normalized_aggregate_id = str(aggregate_id).strip()
        normalized_available_at = self._normalize_datetime(available_at)

        if conn is None:
            with transaction() as tx:
                return self.enqueue(
                    tenant_id=normalized_tenant_id,
                    event_type=normalized_event_type,
                    aggregate_type=normalized_aggregate_type,
                    aggregate_id=normalized_aggregate_id,
                    payload_json=payload_json,
                    available_at=normalized_available_at,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_outbox_events (
                        tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                        status, retry_count, available_at, created_at, processed_at,
                        last_error, correlation_id, causation_id
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, 'pending', 0, %s, NOW(), NULL, NULL, %s, %s)
                    RETURNING id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                              status, retry_count, available_at, created_at, processed_at,
                              last_error, correlation_id, causation_id
                    """,
                    (
                        normalized_tenant_id,
                        normalized_event_type,
                        normalized_aggregate_type,
                        normalized_aggregate_id,
                        psycopg.types.json.Jsonb(dict(payload_json)),
                        normalized_available_at,
                        correlation_id,
                        causation_id,
                    ),
                )
                row = cur.fetchone()
            return self._row_to_api(row)

        with self._lock:
            self._counter += 1
            row = {
                "id": self._counter,
                "tenant_id": normalized_tenant_id,
                "event_type": normalized_event_type,
                "aggregate_type": normalized_aggregate_type,
                "aggregate_id": normalized_aggregate_id,
                "payload_json": dict(payload_json),
                "status": "pending",
                "retry_count": 0,
                "available_at": normalized_available_at.isoformat(),
                "created_at": self._now_iso(),
                "processed_at": None,
                "last_error": None,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
            }
            self._rows[self._counter] = row
            return dict(row)

    def get(self, event_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_event_id = int(event_id)
        if conn is None:
            with transaction() as tx:
                return self.get(normalized_event_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                           status, retry_count, available_at, created_at, processed_at,
                           last_error, correlation_id, causation_id
                    FROM app_platform_outbox_events
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (normalized_event_id,),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_event_id)
            return dict(row) if row else None

    def list_for_tenant(self, tenant_id: int, *, limit: int = 100, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_limit = max(1, min(int(limit), 1000))
        if conn is None:
            with transaction() as tx:
                return self.list_for_tenant(normalized_tenant_id, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                           status, retry_count, available_at, created_at, processed_at,
                           last_error, correlation_id, causation_id
                    FROM app_platform_outbox_events
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (normalized_tenant_id, normalized_limit),
                )
                rows = cur.fetchall()
            return [self._row_to_api(row) for row in rows]

        with self._lock:
            rows = [dict(item) for item in self._rows.values() if int(item["tenant_id"]) == normalized_tenant_id]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows[:normalized_limit]

    def fetch_processible(
        self,
        *,
        limit: int = 50,
        max_retry_count: int = 5,
        as_of: datetime | None = None,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit), 1000))
        normalized_max_retry = max(1, int(max_retry_count))
        normalized_as_of = self._normalize_datetime(as_of)

        if conn is None:
            with transaction() as tx:
                return self.fetch_processible(
                    limit=normalized_limit,
                    max_retry_count=normalized_max_retry,
                    as_of=normalized_as_of,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                           status, retry_count, available_at, created_at, processed_at,
                           last_error, correlation_id, causation_id
                    FROM app_platform_outbox_events
                    WHERE status = ANY(%s)
                      AND retry_count < %s
                      AND available_at <= %s
                    ORDER BY available_at ASC, created_at ASC, id ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (["pending", "failed"], normalized_max_retry, normalized_as_of, normalized_limit),
                )
                rows = cur.fetchall()
            return [self._row_to_api(row) for row in rows]

        with self._lock:
            rows = []
            for row in self._rows.values():
                available_at_raw = str(row.get("available_at") or self._now_iso())
                available_at = datetime.fromisoformat(available_at_raw)
                if available_at.tzinfo is None:
                    available_at = available_at.replace(tzinfo=timezone.utc)
                if str(row.get("status")) not in {"pending", "failed"}:
                    continue
                if int(row.get("retry_count", 0)) >= normalized_max_retry:
                    continue
                if available_at > normalized_as_of:
                    continue
                rows.append(dict(row))
        rows.sort(key=lambda item: (str(item["available_at"]), str(item["created_at"]), int(item["id"])))
        return rows[:normalized_limit]

    def count_backlog(self, *, conn: object | None = None) -> int:
        if conn is None:
            with transaction() as tx:
                return self.count_backlog(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM app_platform_outbox_events
                    WHERE status IN ('pending', 'failed', 'processing')
                    """
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(1 for row in self._rows.values() if str(row.get("status")) in {"pending", "failed", "processing"})

    def mark_processing(self, event_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_event_id = int(event_id)
        if conn is None:
            with transaction() as tx:
                return self.mark_processing(normalized_event_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_outbox_events
                    SET status = 'processing',
                        last_error = NULL
                    WHERE id = %s AND status = ANY(%s)
                    RETURNING id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                              status, retry_count, available_at, created_at, processed_at,
                              last_error, correlation_id, causation_id
                    """,
                    (normalized_event_id, ["pending", "failed"]),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_event_id)
            if row is None or str(row.get("status")) not in {"pending", "failed"}:
                return None
            row["status"] = "processing"
            row["last_error"] = None
            return dict(row)

    def mark_processed(self, event_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_event_id = int(event_id)
        if conn is None:
            with transaction() as tx:
                return self.mark_processed(normalized_event_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_outbox_events
                    SET status = 'processed',
                        processed_at = NOW(),
                        last_error = NULL
                    WHERE id = %s AND status = 'processing'
                    RETURNING id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                              status, retry_count, available_at, created_at, processed_at,
                              last_error, correlation_id, causation_id
                    """,
                    (normalized_event_id,),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_event_id)
            if row is None or str(row.get("status")) != "processing":
                return None
            row["status"] = "processed"
            row["processed_at"] = self._now_iso()
            row["last_error"] = None
            return dict(row)

    def mark_failed(
        self,
        event_id: int,
        *,
        error: str,
        next_available_at: datetime,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        normalized_event_id = int(event_id)
        normalized_error = error.strip() or "event handler failed"
        normalized_next_available_at = self._normalize_datetime(next_available_at)
        if conn is None:
            with transaction() as tx:
                return self.mark_failed(
                    normalized_event_id,
                    error=normalized_error,
                    next_available_at=normalized_next_available_at,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_outbox_events
                    SET status = 'failed',
                        retry_count = retry_count + 1,
                        available_at = %s,
                        last_error = %s
                    WHERE id = %s AND status = 'processing'
                    RETURNING id, tenant_id, event_type, aggregate_type, aggregate_id, payload_json,
                              status, retry_count, available_at, created_at, processed_at,
                              last_error, correlation_id, causation_id
                    """,
                    (normalized_next_available_at, normalized_error, normalized_event_id),
                )
                row = cur.fetchone()
            return self._row_to_api(row) if row else None

        with self._lock:
            row = self._rows.get(normalized_event_id)
            if row is None or str(row.get("status")) != "processing":
                return None
            row["status"] = "failed"
            row["retry_count"] = int(row.get("retry_count", 0)) + 1
            row["available_at"] = normalized_next_available_at.isoformat()
            row["last_error"] = normalized_error
            return dict(row)