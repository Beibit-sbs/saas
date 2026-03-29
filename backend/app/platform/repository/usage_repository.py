from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class UsageRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._memory: dict[tuple[int, str, str], dict[str, Any]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def initialize(
        self,
        tenant_id: int,
        metric: str,
        *,
        period_key: str = "current",
        conn: object | None = None,
    ) -> dict[str, Any]:
        return self.increment(tenant_id, metric, 0, period_key=period_key, conn=conn)

    def increment(
        self,
        tenant_id: int,
        metric: str,
        value: int,
        *,
        period_key: str = "current",
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_metric = str(metric or "").strip().lower()
        normalized_value = int(value)
        normalized_period_key = str(period_key or "current").strip().lower() or "current"

        if normalized_tenant_id <= 0:
            raise ValueError("tenant_id must be positive")
        if not normalized_metric:
            raise ValueError("metric is required")

        if conn is None:
            with transaction() as tx:
                return self.increment(
                    normalized_tenant_id,
                    normalized_metric,
                    normalized_value,
                    period_key=normalized_period_key,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, value
                    FROM app_platform_usage_counters
                    WHERE tenant_id = %s AND metric = %s AND period_key = %s
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (normalized_tenant_id, normalized_metric, normalized_period_key),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        INSERT INTO app_platform_usage_counters (tenant_id, metric, period_key, value, updated_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        RETURNING value, updated_at
                        """,
                        (normalized_tenant_id, normalized_metric, normalized_period_key, normalized_value),
                    )
                    inserted = cur.fetchone()
                    next_value = int(inserted[0])
                    updated_at = inserted[1]
                else:
                    next_value = int(row[1]) + normalized_value
                    cur.execute(
                        """
                        UPDATE app_platform_usage_counters
                        SET value = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING updated_at
                        """,
                        (next_value, int(row[0])),
                    )
                    updated_at = cur.fetchone()[0]

            return {
                "tenant_id": normalized_tenant_id,
                "metric": normalized_metric,
                "period_key": normalized_period_key,
                "value": next_value,
                "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
            }

        with self._lock:
            key = (normalized_tenant_id, normalized_metric, normalized_period_key)
            current = self._memory.get(
                key,
                {
                    "tenant_id": normalized_tenant_id,
                    "metric": normalized_metric,
                    "period_key": normalized_period_key,
                    "value": 0,
                    "updated_at": self._now_iso(),
                },
            )
            current["value"] = int(current["value"]) + normalized_value
            current["updated_at"] = self._now_iso()
            self._memory[key] = current
            return dict(current)

    def list_for_tenant_period(
        self,
        tenant_id: int,
        *,
        period_key: str,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_period_key = str(period_key or "").strip().lower() or "current"

        if conn is None:
            with transaction() as tx:
                return self.list_for_tenant_period(normalized_tenant_id, period_key=normalized_period_key, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tenant_id, metric, period_key, value, updated_at
                    FROM app_platform_usage_counters
                    WHERE tenant_id = %s AND period_key = %s
                    ORDER BY metric ASC
                    """,
                    (normalized_tenant_id, normalized_period_key),
                )
                rows = cur.fetchall()
            return [
                {
                    "tenant_id": int(row[0]),
                    "metric": str(row[1]),
                    "period_key": str(row[2]),
                    "value": int(row[3]),
                    "updated_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [
                dict(item)
                for item in self._memory.values()
                if int(item.get("tenant_id", 0)) == normalized_tenant_id and str(item.get("period_key", "")) == normalized_period_key
            ]
        rows.sort(key=lambda item: str(item.get("metric", "")))
        return rows
