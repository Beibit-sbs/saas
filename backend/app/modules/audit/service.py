from __future__ import annotations

from app.core.db import get_raw_conn
from app.core.config import is_runtime_schema_bootstrap_enabled

from collections import deque
from contextvars import ContextVar, Token
from datetime import datetime, timezone
import json
import logging
import os
from threading import Lock
from typing import Any
from uuid import uuid4

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

logger = logging.getLogger("app.audit")

_MAX_AUDIT_EVENTS = 1000
_audit_events: deque[dict[str, Any]] = deque(maxlen=_MAX_AUDIT_EVENTS)
_audit_lock = Lock()
_audit_schema_lock = Lock()
_audit_schema_ready = False
_request_tenant_id_var: ContextVar[int | None] = ContextVar("audit_request_tenant_id", default=None)


def _require_tenant_id(value: int | str | None, *, operation: str) -> int:
    if value is None:
        raise RuntimeError(f"tenant_id is required for {operation}")
    try:
        tenant_id = int(value)
    except (TypeError, ValueError):
        raise RuntimeError(f"tenant_id is required for {operation}") from None
    if tenant_id <= 0:
        raise RuntimeError(f"tenant_id is required for {operation}")
    return tenant_id


def set_request_tenant_id(tenant_id: int | None) -> Token[int | None]:
    if tenant_id is None:
        return _request_tenant_id_var.set(None)
    return _request_tenant_id_var.set(_require_tenant_id(tenant_id, operation="set_request_tenant_id"))


def reset_request_tenant_id(token: Token[int | None]) -> None:
    _request_tenant_id_var.reset(token)


def _effective_tenant_id(tenant_id: int | None, metadata: dict[str, Any] | None = None) -> int:
    if tenant_id is not None:
        return _require_tenant_id(tenant_id, operation="audit event")

    if metadata is not None and "tenant_id" in metadata:
        return _require_tenant_id(metadata.get("tenant_id"), operation="audit event")

    request_tenant_id = _request_tenant_id_var.get()
    if request_tenant_id is not None:
        return _require_tenant_id(request_tenant_id, operation="audit event")

    raise RuntimeError("tenant_id is required for audit event")


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _to_iso_or_none(value: str | None) -> str | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    try:
        # Accept both UTC Z and offset datetime inputs.
        datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return raw
    except ValueError:
        return None


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _ensure_table(conn) -> None:
    if not is_runtime_schema_bootstrap_enabled():
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                path TEXT NOT NULL,
                ip TEXT NOT NULL,
                result TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                tenant_id BIGINT NOT NULL REFERENCES app_tenants(id),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
        cur.execute(
            "ALTER TABLE app_audit_events ADD COLUMN IF NOT EXISTS tenant_id BIGINT"
        )
        cur.execute(
            "ALTER TABLE app_audit_events ALTER COLUMN tenant_id DROP DEFAULT"
        )
        cur.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM app_audit_events WHERE tenant_id IS NULL) THEN
                    RAISE EXCEPTION 'audit tenant remediation required: app_audit_events has NULL tenant_id rows';
                END IF;
            END
            $$;
            """
        )
        cur.execute(
            "ALTER TABLE app_audit_events ALTER COLUMN tenant_id SET NOT NULL"
        )
        cur.execute(
            "DO $$ BEGIN "
            "IF NOT EXISTS ("
            "SELECT 1 FROM pg_constraint WHERE conname = 'fk_app_audit_events_tenant_id'"
            ") THEN "
            "ALTER TABLE app_audit_events "
            "ADD CONSTRAINT fk_app_audit_events_tenant_id FOREIGN KEY (tenant_id) REFERENCES app_tenants(id); "
            "END IF; "
            "END $$"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_audit_events_timestamp ON app_audit_events (timestamp DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_audit_events_actor ON app_audit_events (actor)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_audit_events_action ON app_audit_events (action)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_app_audit_events_tenant_created ON app_audit_events (tenant_id, timestamp DESC)"
        )
    conn.commit()


def _append_memory(event: dict[str, Any]) -> None:
    with _audit_lock:
        _audit_events.appendleft(event)


def _ensure_table_once(conn) -> None:
    global _audit_schema_ready
    if _audit_schema_ready:
        return
    with _audit_schema_lock:
        if _audit_schema_ready:
            return
        _ensure_table(conn)
        _audit_schema_ready = True


def _list_memory(
    actor: str | None = None,
    action: str | None = None,
    entity: str | None = None,
    result: str | None = None,
    correlation_id: str | None = None,
    since: str | None = None,
    limit: int = 100,
    tenant_id: int | None = None,
    include_all_tenants: bool = False,
) -> list[dict[str, Any]]:
    actor_filter = (actor or "").strip().lower()
    action_filter = (action or "").strip().lower()
    entity_filter = (entity or "").strip().lower()
    result_filter = (result or "").strip().lower()
    correlation_filter = (correlation_id or "").strip().lower()
    since_filter = _to_iso_or_none(since)
    cap = max(1, min(limit, 500))

    with _audit_lock:
        rows = list(_audit_events)

    if actor_filter:
        rows = [item for item in rows if actor_filter in str(item.get("actor", "")).lower()]
    if action_filter:
        rows = [item for item in rows if action_filter in str(item.get("action", "")).lower()]
    if entity_filter:
        rows = [item for item in rows if entity_filter in str(item.get("entity", "")).lower()]
    if result_filter:
        rows = [item for item in rows if result_filter in str(item.get("result", "")).lower()]
    if correlation_filter:
        rows = [item for item in rows if correlation_filter in str(item.get("correlation_id", "")).lower()]
    if not include_all_tenants:
        effective_tenant_id = _require_tenant_id(tenant_id, operation="list_admin_actions")
        rows = [item for item in rows if _require_tenant_id(item.get("tenant_id"), operation="stored audit row") == effective_tenant_id]
    if since_filter:
        rows = [item for item in rows if str(item.get("timestamp", "")) >= since_filter]

    return rows[:cap]


def _row_to_event(row: tuple[Any, ...]) -> dict[str, Any]:
    metadata = row[8]
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}

    timestamp = row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1])
    return {
        "event_id": row[0],
        "timestamp": timestamp,
        "actor": row[2],
        "action": row[3],
        "entity": row[4],
        "path": row[5],
        "ip": row[6],
        "client_ip": row[6],
        "result": row[7],
        "tenant_id": _require_tenant_id(row[9], operation="stored audit row"),
        "correlation_id": row[10],
        "metadata": metadata,
    }


def _insert_db(event: dict[str, Any]) -> None:
    db_url = _db_url()
    if not db_url or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_table_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_audit_events(
                    event_id, timestamp, actor, action, entity, path, ip, result, tenant_id, correlation_id, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    event["event_id"],
                    _parse_timestamp(event["timestamp"]),
                    event["actor"],
                    event["action"],
                    event["entity"],
                    event["path"],
                    event["ip"],
                    event["result"],
                    _require_tenant_id(event.get("tenant_id"), operation="audit event"),
                    event["correlation_id"],
                    json.dumps(event["metadata"], ensure_ascii=False),
                ),
            )
        conn.commit()


def _list_db(
    actor: str | None = None,
    action: str | None = None,
    entity: str | None = None,
    result: str | None = None,
    correlation_id: str | None = None,
    since: str | None = None,
    limit: int = 100,
    tenant_id: int | None = None,
    include_all_tenants: bool = False,
) -> list[dict[str, Any]]:
    db_url = _db_url()
    if not db_url or psycopg is None:
        raise RuntimeError("database unavailable")

    actor_filter = (actor or "").strip().lower()
    action_filter = (action or "").strip().lower()
    entity_filter = (entity or "").strip().lower()
    result_filter = (result or "").strip().lower()
    correlation_filter = (correlation_id or "").strip().lower()
    since_filter = _to_iso_or_none(since)
    cap = max(1, min(limit, 500))

    where_clauses: list[str] = []
    params: list[Any] = []

    if actor_filter:
        where_clauses.append("LOWER(actor) LIKE %s")
        params.append(f"%{actor_filter}%")
    if action_filter:
        where_clauses.append("LOWER(action) LIKE %s")
        params.append(f"%{action_filter}%")
    if entity_filter:
        where_clauses.append("LOWER(entity) LIKE %s")
        params.append(f"%{entity_filter}%")
    if result_filter:
        where_clauses.append("LOWER(result) LIKE %s")
        params.append(f"%{result_filter}%")
    if correlation_filter:
        where_clauses.append("LOWER(correlation_id) LIKE %s")
        params.append(f"%{correlation_filter}%")
    if not include_all_tenants:
        where_clauses.append("tenant_id = %s")
        params.append(_require_tenant_id(tenant_id, operation="list_admin_actions"))
    if since_filter:
        where_clauses.append("timestamp >= %s")
        params.append(_parse_timestamp(since_filter))

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with get_raw_conn() as conn:
        _ensure_table_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT event_id, timestamp, actor, action, entity, path, ip, result, metadata, tenant_id, correlation_id
                FROM app_audit_events
                {where_sql}
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                [*params, cap],
            )
            rows = cur.fetchall()

    return [_row_to_event(row) for row in rows]


def _clear_db() -> None:
    db_url = _db_url()
    if not db_url or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_table_once(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM app_audit_events")
        conn.commit()


def _merge_rows(*row_sets: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    for rows in row_sets:
        for row in rows:
            event_id = str(row.get("event_id", "")).strip()
            if not event_id or event_id in combined:
                continue
            combined[event_id] = row

    ordered = sorted(combined.values(), key=lambda item: str(item.get("timestamp", "")), reverse=True)
    return ordered[:limit]


def _warn_db_unavailable(operation: str, exc: Exception) -> None:
    logger.warning("audit_db_%s_failed error=%s", operation, exc)


def log_admin_action(
    actor: str,
    action: str,
    path: str,
    client_ip: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    entity: str | None = None,
    result: str = "success",
    tenant_id: int | None = None,
) -> None:
    event_id = str(uuid4())
    normalized_tenant_id = _effective_tenant_id(tenant_id, metadata)
    event = {
        "event_id": event_id,
        "timestamp": _now_iso(),
        "tenant_id": normalized_tenant_id,
        "actor": actor,
        "action": action,
        "entity": entity or "admin",
        "path": path,
        "ip": client_ip,
        "client_ip": client_ip,
        "result": result,
        "correlation_id": correlation_id or event_id,
        "metadata": metadata or {},
    }

    stored_in_db = False
    if _use_database():
        try:
            _insert_db(event)
            stored_in_db = True
        except Exception as exc:  # pragma: no cover - depends on runtime DB state
            _warn_db_unavailable("insert", exc)

    if not stored_in_db:
        _append_memory(event)

    logger.info(
        "admin_action user=%s action=%s entity=%s path=%s ip=%s result=%s correlation_id=%s",
        actor,
        action,
        event["entity"],
        path,
        client_ip,
        event["result"],
        event["correlation_id"],
    )


def list_admin_actions(
    actor: str | None = None,
    action: str | None = None,
    entity: str | None = None,
    result: str | None = None,
    correlation_id: str | None = None,
    since: str | None = None,
    limit: int = 100,
    tenant_id: int | None = None,
    include_all_tenants: bool = False,
) -> list[dict[str, Any]]:
    cap = max(1, min(limit, 500))
    effective_tenant_id = None if include_all_tenants else _effective_tenant_id(tenant_id)
    memory_rows = _list_memory(
        actor=actor,
        action=action,
        entity=entity,
        result=result,
        correlation_id=correlation_id,
        since=since,
        limit=cap,
        tenant_id=effective_tenant_id,
        include_all_tenants=include_all_tenants,
    )

    if not _use_database():
        return memory_rows

    try:
        db_rows = _list_db(
            actor=actor,
            action=action,
            entity=entity,
            result=result,
            correlation_id=correlation_id,
            since=since,
            limit=cap,
            tenant_id=effective_tenant_id,
            include_all_tenants=include_all_tenants,
        )
    except Exception as exc:  # pragma: no cover - depends on runtime DB state
        _warn_db_unavailable("list", exc)
        return memory_rows

    return _merge_rows(db_rows, memory_rows, limit=cap)


def clear_audit_events() -> None:
    if _use_database():
        try:
            _clear_db()
        except Exception as exc:  # pragma: no cover - depends on runtime DB state
            _warn_db_unavailable("clear", exc)

    with _audit_lock:
        _audit_events.clear()
