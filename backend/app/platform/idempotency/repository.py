from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class IdempotencyRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._memory: dict[tuple[int, str, str], dict[str, Any]] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _now_iso(self) -> str:
        return self._now().isoformat()

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM platform_idempotency_keys")
            return

        with self._lock:
            self._memory.clear()

    def get(self, tenant_id: int, key: str, operation: str, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_tenant_id = int(tenant_id)
        normalized_key = key.strip()
        normalized_operation = operation.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.get(normalized_tenant_id, normalized_key, normalized_operation, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT tenant_id, key, operation, request_hash, status, response_snapshot, created_at, expires_at
                    FROM platform_idempotency_keys
                    WHERE tenant_id = %s AND key = %s AND operation = %s
                    LIMIT 1
                    """,
                    (normalized_tenant_id, normalized_key, normalized_operation),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return {
                "tenant_id": int(row[0]),
                "key": str(row[1]),
                "operation": str(row[2]),
                "request_hash": str(row[3]),
                "status": str(row[4]),
                "response_snapshot": dict(row[5] or {}),
                "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
                "expires_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
            }

        with self._lock:
            row = self._memory.get((normalized_tenant_id, normalized_key, normalized_operation))
            return dict(row) if row else None

    def create_pending(
        self,
        tenant_id: int,
        key: str,
        operation: str,
        request_hash: str,
        *,
        ttl_seconds: int = 24 * 60 * 60,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_key = key.strip()
        normalized_operation = operation.strip().lower()
        normalized_hash = request_hash.strip()

        if conn is None:
            with transaction() as tx:
                return self.create_pending(
                    normalized_tenant_id,
                    normalized_key,
                    normalized_operation,
                    normalized_hash,
                    ttl_seconds=ttl_seconds,
                    conn=tx,
                )

        expires_at = self._now() + timedelta(seconds=max(60, int(ttl_seconds)))

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO platform_idempotency_keys (tenant_id, key, operation, request_hash, status, response_snapshot, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, 'pending', '{}'::jsonb, NOW(), %s)
                    ON CONFLICT (tenant_id, key, operation) DO NOTHING
                    """,
                    (normalized_tenant_id, normalized_key, normalized_operation, normalized_hash, expires_at),
                )
            row = self.get(normalized_tenant_id, normalized_key, normalized_operation, conn=conn)
            if row is None:
                raise RuntimeError("failed to create idempotency key")
            return row

        with self._lock:
            record_key = (normalized_tenant_id, normalized_key, normalized_operation)
            row = self._memory.get(record_key)
            if row is None:
                row = {
                    "tenant_id": normalized_tenant_id,
                    "key": normalized_key,
                    "operation": normalized_operation,
                    "request_hash": normalized_hash,
                    "status": "pending",
                    "response_snapshot": {},
                    "created_at": self._now_iso(),
                    "expires_at": expires_at.isoformat(),
                }
                self._memory[record_key] = row
            return dict(row)

    def complete(
        self,
        tenant_id: int,
        key: str,
        operation: str,
        response_snapshot: dict[str, Any],
        *,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_key = key.strip()
        normalized_operation = operation.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.complete(normalized_tenant_id, normalized_key, normalized_operation, response_snapshot, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE platform_idempotency_keys
                    SET status = 'completed', response_snapshot = %s::jsonb
                    WHERE tenant_id = %s AND key = %s AND operation = %s
                    """,
                    (psycopg.types.json.Jsonb(dict(response_snapshot)), normalized_tenant_id, normalized_key, normalized_operation),
                )
            row = self.get(normalized_tenant_id, normalized_key, normalized_operation, conn=conn)
            if row is None:
                raise RuntimeError("idempotency key missing during completion")
            return row

        with self._lock:
            record_key = (normalized_tenant_id, normalized_key, normalized_operation)
            row = self._memory.get(record_key)
            if row is None:
                raise RuntimeError("idempotency key missing during completion")
            row["status"] = "completed"
            row["response_snapshot"] = dict(response_snapshot)
            return dict(row)

    def fail(
        self,
        tenant_id: int,
        key: str,
        operation: str,
        response_snapshot: dict[str, Any],
        *,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_key = key.strip()
        normalized_operation = operation.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.fail(normalized_tenant_id, normalized_key, normalized_operation, response_snapshot, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE platform_idempotency_keys
                    SET status = 'failed', response_snapshot = %s::jsonb
                    WHERE tenant_id = %s AND key = %s AND operation = %s
                    """,
                    (psycopg.types.json.Jsonb(dict(response_snapshot)), normalized_tenant_id, normalized_key, normalized_operation),
                )
            row = self.get(normalized_tenant_id, normalized_key, normalized_operation, conn=conn)
            if row is None:
                raise RuntimeError("idempotency key missing during failure")
            return row

        with self._lock:
            record_key = (normalized_tenant_id, normalized_key, normalized_operation)
            row = self._memory.get(record_key)
            if row is None:
                raise RuntimeError("idempotency key missing during failure")
            row["status"] = "failed"
            row["response_snapshot"] = dict(response_snapshot)
            return dict(row)
