from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class NotificationRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: list[dict[str, Any]] = []
        self._counter = 0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def dispatch(
        self,
        *,
        tenant_id: int,
        channel: str,
        target: str,
        payload: dict[str, Any],
        subject: str | None,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_channel = channel.strip().lower()
        normalized_target = target.strip()
        normalized_subject = subject.strip() if isinstance(subject, str) and subject.strip() else None
        if normalized_channel not in {"email", "in_app", "webhook"}:
            raise ValueError("unsupported notification channel")
        if not normalized_target:
            raise ValueError("notification target is required")

        if conn is None:
            with transaction() as tx:
                return self.dispatch(
                    tenant_id=normalized_tenant_id,
                    channel=normalized_channel,
                    target=normalized_target,
                    payload=payload,
                    subject=normalized_subject,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_notifications (tenant_id, channel, target, subject, payload_json, status, retry_count, last_error, created_at)
                    VALUES (%s, %s, %s, %s, %s::jsonb, 'queued', 0, NULL, NOW())
                    RETURNING id, tenant_id, channel, target, subject, payload_json, status, retry_count, last_error, created_at
                    """,
                    (normalized_tenant_id, normalized_channel, normalized_target, normalized_subject, psycopg.types.json.Jsonb(dict(payload))),
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "channel": str(row[2]),
                "target": str(row[3]),
                "subject": row[4],
                "payload": dict(row[5] or {}),
                "status": str(row[6]),
                "retry_count": int(row[7]),
                "last_error": row[8],
                "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
            }

        with self._lock:
            self._counter += 1
            row = {
                "id": self._counter,
                "tenant_id": normalized_tenant_id,
                "channel": normalized_channel,
                "target": normalized_target,
                "subject": normalized_subject,
                "payload": dict(payload),
                "status": "queued",
                "retry_count": 0,
                "last_error": None,
                "created_at": self._now_iso(),
            }
            self._rows.append(row)
            return dict(row)

    def list_for_tenant(self, tenant_id: int, *, limit: int = 100, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_limit = max(1, min(int(limit), 500))

        if conn is None:
            with transaction() as tx:
                return self.list_for_tenant(normalized_tenant_id, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, channel, target, subject, payload_json, status, retry_count, last_error, created_at
                    FROM app_platform_notifications
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
                    "channel": str(row[2]),
                    "target": str(row[3]),
                    "subject": row[4],
                    "payload": dict(row[5] or {}),
                    "status": str(row[6]),
                    "retry_count": int(row[7]),
                    "last_error": row[8],
                    "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [dict(item) for item in self._rows if int(item["tenant_id"]) == normalized_tenant_id]
        rows.sort(key=lambda item: str(item["created_at"]), reverse=True)
        return rows[:normalized_limit]

    def get(self, notification_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_notification_id = int(notification_id)
        if conn is None:
            with transaction() as tx:
                return self.get(normalized_notification_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, channel, target, subject, payload_json, status, retry_count, last_error, created_at
                    FROM app_platform_notifications
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (normalized_notification_id,),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "channel": str(row[2]),
                "target": str(row[3]),
                "subject": row[4],
                "payload": dict(row[5] or {}),
                "status": str(row[6]),
                "retry_count": int(row[7]),
                "last_error": row[8],
                "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
            }

        with self._lock:
            for item in self._rows:
                if int(item["id"]) == normalized_notification_id:
                    return dict(item)
        return None

    def list_by_status(self, status: str, *, limit: int = 100, conn: object | None = None) -> list[dict[str, Any]]:
        normalized_status = status.strip().lower()
        normalized_limit = max(1, min(int(limit), 500))
        if conn is None:
            with transaction() as tx:
                return self.list_by_status(normalized_status, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, channel, target, subject, payload_json, status, retry_count, last_error, created_at
                    FROM app_platform_notifications
                    WHERE status = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (normalized_status, normalized_limit),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "tenant_id": int(row[1]),
                    "channel": str(row[2]),
                    "target": str(row[3]),
                    "subject": row[4],
                    "payload": dict(row[5] or {}),
                    "status": str(row[6]),
                    "retry_count": int(row[7]),
                    "last_error": row[8],
                    "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [dict(item) for item in self._rows if str(item["status"]).lower() == normalized_status]
        rows.sort(key=lambda item: str(item["created_at"]))
        return rows[:normalized_limit]

    def mark_status(
        self,
        notification_id: int,
        *,
        status: str,
        last_error: str | None = None,
        increment_retry: bool = False,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        normalized_notification_id = int(notification_id)
        normalized_status = status.strip().lower()
        normalized_error = last_error.strip() if isinstance(last_error, str) and last_error.strip() else None

        if conn is None:
            with transaction() as tx:
                return self.mark_status(
                    normalized_notification_id,
                    status=normalized_status,
                    last_error=normalized_error,
                    increment_retry=increment_retry,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_notifications
                    SET status = %s,
                        last_error = %s,
                        retry_count = retry_count + %s
                    WHERE id = %s
                    RETURNING id, tenant_id, channel, target, subject, payload_json, status, retry_count, last_error, created_at
                    """,
                    (normalized_status, normalized_error, 1 if increment_retry else 0, normalized_notification_id),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "channel": str(row[2]),
                "target": str(row[3]),
                "subject": row[4],
                "payload": dict(row[5] or {}),
                "status": str(row[6]),
                "retry_count": int(row[7]),
                "last_error": row[8],
                "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
            }

        with self._lock:
            for item in self._rows:
                if int(item["id"]) != normalized_notification_id:
                    continue
                item["status"] = normalized_status
                item["last_error"] = normalized_error
                if increment_retry:
                    item["retry_count"] = int(item.get("retry_count", 0)) + 1
                return dict(item)
        return None
