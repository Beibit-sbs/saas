from __future__ import annotations
from app.core.db import get_raw_conn
from app.core.config import is_runtime_schema_bootstrap_enabled

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from threading import Lock

_usage_table_ready = False
_usage_table_lock = Lock()
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


@dataclass
class UsageState:
    rows: list[dict[str, Any]] = field(default_factory=list)
    counter: int = 0


_state_lock = Lock()
_state = UsageState()


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_table(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_usage_events (
                id BIGSERIAL PRIMARY KEY,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id),
                metric TEXT NOT NULL,
                value BIGINT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_usage_events_tenant_metric_created ON app_usage_events (tenant_id, metric, created_at DESC)"
        )
    conn.commit()



def _ensure_table_once(conn) -> None:
    global _usage_table_ready
    if _usage_table_ready:
        return
    with _usage_table_lock:
        if _usage_table_ready:
            return
        _ensure_table(conn)
        _usage_table_ready = True


def record_usage_event(tenant_id: int, metric: str, value: int = 1) -> dict[str, object]:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    normalized_metric = str(metric or "").strip().lower()
    if not normalized_metric:
        raise ValueError("metric is required")

    normalized_value = int(value)

    if _use_database():
        try:
            assert _db_url() and psycopg is not None
            with get_raw_conn() as conn:
                _ensure_table_once(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO app_usage_events (tenant_id, metric, value)
                        VALUES (%s, %s, %s)
                        RETURNING id, tenant_id, metric, value, created_at
                        """,
                        (normalized_tenant_id, normalized_metric, normalized_value),
                    )
                    row = cur.fetchone()
                conn.commit()
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "metric": str(row[2]),
                "value": int(row[3]),
                "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
            }
        except Exception:
            pass

    with _state_lock:
        _state.counter += 1
        row = {
            "id": _state.counter,
            "tenant_id": normalized_tenant_id,
            "metric": normalized_metric,
            "value": normalized_value,
            "created_at": _now_iso(),
        }
        _state.rows.append(row)
        return dict(row)


def list_usage_events(
    tenant_id: int,
    metric: str | None = None,
    limit: int = 200,
) -> list[dict[str, object]]:
    normalized_tenant_id = int(tenant_id)
    normalized_limit = max(1, min(int(limit), 1000))
    normalized_metric = str(metric or "").strip().lower() if metric else None

    if _use_database():
        try:
            assert _db_url() and psycopg is not None
            with get_raw_conn() as conn:
                _ensure_table_once(conn)
                with conn.cursor() as cur:
                    if normalized_metric:
                        cur.execute(
                            """
                            SELECT id, tenant_id, metric, value, created_at
                            FROM app_usage_events
                            WHERE tenant_id = %s AND metric = %s
                            ORDER BY created_at DESC
                            LIMIT %s
                            """,
                            (normalized_tenant_id, normalized_metric, normalized_limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT id, tenant_id, metric, value, created_at
                            FROM app_usage_events
                            WHERE tenant_id = %s
                            ORDER BY created_at DESC
                            LIMIT %s
                            """,
                            (normalized_tenant_id, normalized_limit),
                        )
                    rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "tenant_id": int(row[1]),
                    "metric": str(row[2]),
                    "value": int(row[3]),
                    "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                }
                for row in rows
            ]
        except Exception:
            pass

    with _state_lock:
        rows = [
            dict(item)
            for item in _state.rows
            if int(item["tenant_id"]) == normalized_tenant_id
            and (normalized_metric is None or str(item["metric"]) == normalized_metric)
        ]
    rows.sort(key=lambda item: str(item["created_at"]), reverse=True)
    return rows[:normalized_limit]


def get_usage_sum(
    tenant_id: int,
    metric: str,
    since_iso: str | None = None,
) -> int:
    normalized_metric = str(metric or "").strip().lower()
    if not normalized_metric:
        return 0

    rows = list_usage_events(tenant_id=tenant_id, metric=normalized_metric, limit=10000)
    if since_iso:
        rows = [item for item in rows if str(item.get("created_at", "")) >= since_iso]
    return int(sum(int(item.get("value", 0)) for item in rows))


def clear_usage_state() -> None:
    with _state_lock:
        _state.rows.clear()
        _state.counter = 0

    if _use_database():
        try:
            assert _db_url() and psycopg is not None
            with get_raw_conn() as conn:
                _ensure_table_once(conn)
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM app_usage_events")
                conn.commit()
        except Exception:
            pass
