from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class WebhookRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._subscription_counter = 0
        self._delivery_counter = 0
        self._subscriptions: dict[int, dict[str, Any]] = {}
        self._deliveries: dict[int, dict[str, Any]] = {}

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

    @staticmethod
    def _subscription_row_to_api(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "event_type": str(row[2]),
            "target_url": str(row[3]),
            "signing_secret": str(row[4]),
            "is_active": bool(row[5]),
            "created_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            "updated_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
            "version": int(row[8]),
        }

    @staticmethod
    def _delivery_row_to_api(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "subscription_id": int(row[2]),
            "outbox_event_id": int(row[3]),
            "event_type": str(row[4]),
            "target_url": str(row[5]),
            "request_payload_json": dict(row[6] or {}),
            "response_status_code": int(row[7]) if row[7] is not None else None,
            "response_body": row[8],
            "delivery_status": str(row[9]),
            "retry_count": int(row[10]),
            "next_retry_at": row[11].isoformat() if hasattr(row[11], "isoformat") and row[11] is not None else (str(row[11]) if row[11] is not None else None),
            "last_error": row[12],
            "created_at": row[13].isoformat() if hasattr(row[13], "isoformat") else str(row[13]),
            "delivered_at": row[14].isoformat() if hasattr(row[14], "isoformat") and row[14] is not None else (str(row[14]) if row[14] is not None else None),
        }

    def clear_state(self) -> None:
        with self._lock:
            self._subscription_counter = 0
            self._delivery_counter = 0
            self._subscriptions.clear()
            self._deliveries.clear()

    def create_subscription(
        self,
        *,
        tenant_id: int,
        event_type: str,
        target_url: str,
        signing_secret: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_event_type = event_type.strip().lower()
        normalized_target_url = target_url.strip()
        normalized_signing_secret = signing_secret.strip()
        if not normalized_target_url:
            raise ValueError("webhook target_url is required")
        if not normalized_signing_secret:
            raise ValueError("webhook signing_secret is required")

        if conn is None:
            with transaction() as tx:
                return self.create_subscription(
                    tenant_id=normalized_tenant_id,
                    event_type=normalized_event_type,
                    target_url=normalized_target_url,
                    signing_secret=normalized_signing_secret,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_webhook_subscriptions (
                        tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                    )
                    VALUES (%s, %s, %s, %s, true, NOW(), NOW(), 1)
                    RETURNING id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                    """,
                    (normalized_tenant_id, normalized_event_type, normalized_target_url, normalized_signing_secret),
                )
                row = cur.fetchone()
            return self._subscription_row_to_api(row)

        with self._lock:
            self._subscription_counter += 1
            row = {
                "id": self._subscription_counter,
                "tenant_id": normalized_tenant_id,
                "event_type": normalized_event_type,
                "target_url": normalized_target_url,
                "signing_secret": normalized_signing_secret,
                "is_active": True,
                "created_at": self._now_iso(),
                "updated_at": self._now_iso(),
                "version": 1,
            }
            self._subscriptions[self._subscription_counter] = row
            return dict(row)

    def list_subscriptions(
        self,
        *,
        tenant_id: int,
        event_type: str | None = None,
        active_only: bool = False,
        limit: int = 200,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_event_type = event_type.strip().lower() if isinstance(event_type, str) and event_type.strip() else None
        normalized_limit = max(1, min(int(limit), 1000))

        if conn is None:
            with transaction() as tx:
                return self.list_subscriptions(
                    tenant_id=normalized_tenant_id,
                    event_type=normalized_event_type,
                    active_only=active_only,
                    limit=normalized_limit,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                if normalized_event_type is not None and active_only:
                    cur.execute(
                        """
                        SELECT id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                        FROM app_platform_webhook_subscriptions
                        WHERE tenant_id = %s AND event_type = %s AND is_active = true
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_event_type, normalized_limit),
                    )
                elif normalized_event_type is not None:
                    cur.execute(
                        """
                        SELECT id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                        FROM app_platform_webhook_subscriptions
                        WHERE tenant_id = %s AND event_type = %s
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_event_type, normalized_limit),
                    )
                elif active_only:
                    cur.execute(
                        """
                        SELECT id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                        FROM app_platform_webhook_subscriptions
                        WHERE tenant_id = %s AND is_active = true
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                        FROM app_platform_webhook_subscriptions
                        WHERE tenant_id = %s
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                        """,
                        (normalized_tenant_id, normalized_limit),
                    )
                rows = cur.fetchall()
            return [self._subscription_row_to_api(row) for row in rows]

        with self._lock:
            rows = [dict(item) for item in self._subscriptions.values() if int(item["tenant_id"]) == normalized_tenant_id]
        if normalized_event_type is not None:
            rows = [item for item in rows if str(item["event_type"]) == normalized_event_type]
        if active_only:
            rows = [item for item in rows if bool(item.get("is_active"))]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows[:normalized_limit]

    def get_subscription(self, subscription_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_subscription_id = int(subscription_id)
        if conn is None:
            with transaction() as tx:
                return self.get_subscription(normalized_subscription_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                    FROM app_platform_webhook_subscriptions
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (normalized_subscription_id,),
                )
                row = cur.fetchone()
            return self._subscription_row_to_api(row) if row else None

        with self._lock:
            row = self._subscriptions.get(normalized_subscription_id)
            return dict(row) if row else None

    def deactivate_subscription(self, subscription_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_subscription_id = int(subscription_id)
        if conn is None:
            with transaction() as tx:
                return self.deactivate_subscription(normalized_subscription_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_webhook_subscriptions
                    SET is_active = false,
                        version = version + 1,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, tenant_id, event_type, target_url, signing_secret, is_active, created_at, updated_at, version
                    """,
                    (normalized_subscription_id,),
                )
                row = cur.fetchone()
            return self._subscription_row_to_api(row) if row else None

        with self._lock:
            row = self._subscriptions.get(normalized_subscription_id)
            if row is None:
                return None
            row["is_active"] = False
            row["version"] = int(row.get("version", 0)) + 1
            row["updated_at"] = self._now_iso()
            return dict(row)

    def create_delivery_attempt(
        self,
        *,
        tenant_id: int,
        subscription_id: int,
        outbox_event_id: int,
        event_type: str,
        target_url: str,
        request_payload_json: dict[str, Any],
        retry_count: int,
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_subscription_id = int(subscription_id)
        normalized_outbox_event_id = int(outbox_event_id)
        normalized_event_type = event_type.strip().lower()
        normalized_target_url = target_url.strip()
        normalized_retry_count = max(0, int(retry_count))

        if conn is None:
            with transaction() as tx:
                return self.create_delivery_attempt(
                    tenant_id=normalized_tenant_id,
                    subscription_id=normalized_subscription_id,
                    outbox_event_id=normalized_outbox_event_id,
                    event_type=normalized_event_type,
                    target_url=normalized_target_url,
                    request_payload_json=request_payload_json,
                    retry_count=normalized_retry_count,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_webhook_deliveries (
                        tenant_id, subscription_id, outbox_event_id, event_type, target_url,
                        request_payload_json, response_status_code, response_body, delivery_status,
                        retry_count, next_retry_at, last_error, created_at, delivered_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, NULL, NULL, 'pending', %s, NULL, NULL, NOW(), NULL)
                    RETURNING id, tenant_id, subscription_id, outbox_event_id, event_type, target_url,
                              request_payload_json, response_status_code, response_body, delivery_status,
                              retry_count, next_retry_at, last_error, created_at, delivered_at
                    """,
                    (
                        normalized_tenant_id,
                        normalized_subscription_id,
                        normalized_outbox_event_id,
                        normalized_event_type,
                        normalized_target_url,
                        psycopg.types.json.Jsonb(dict(request_payload_json)),
                        normalized_retry_count,
                    ),
                )
                row = cur.fetchone()
            return self._delivery_row_to_api(row)

        with self._lock:
            self._delivery_counter += 1
            row = {
                "id": self._delivery_counter,
                "tenant_id": normalized_tenant_id,
                "subscription_id": normalized_subscription_id,
                "outbox_event_id": normalized_outbox_event_id,
                "event_type": normalized_event_type,
                "target_url": normalized_target_url,
                "request_payload_json": dict(request_payload_json),
                "response_status_code": None,
                "response_body": None,
                "delivery_status": "pending",
                "retry_count": normalized_retry_count,
                "next_retry_at": None,
                "last_error": None,
                "created_at": self._now_iso(),
                "delivered_at": None,
            }
            self._deliveries[self._delivery_counter] = row
            return dict(row)

    def finalize_delivery_attempt(
        self,
        delivery_id: int,
        *,
        delivery_status: str,
        response_status_code: int | None,
        response_body: str | None,
        next_retry_at: datetime | None,
        last_error: str | None,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        normalized_delivery_id = int(delivery_id)
        normalized_status = delivery_status.strip().lower()
        normalized_next_retry_at = self._normalize_datetime(next_retry_at) if next_retry_at is not None else None

        if conn is None:
            with transaction() as tx:
                return self.finalize_delivery_attempt(
                    normalized_delivery_id,
                    delivery_status=normalized_status,
                    response_status_code=response_status_code,
                    response_body=response_body,
                    next_retry_at=normalized_next_retry_at,
                    last_error=last_error,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_webhook_deliveries
                    SET delivery_status = %s,
                        response_status_code = %s,
                        response_body = %s,
                        next_retry_at = %s,
                        last_error = %s,
                        delivered_at = CASE WHEN %s = 'delivered' THEN NOW() ELSE delivered_at END
                    WHERE id = %s
                    RETURNING id, tenant_id, subscription_id, outbox_event_id, event_type, target_url,
                              request_payload_json, response_status_code, response_body, delivery_status,
                              retry_count, next_retry_at, last_error, created_at, delivered_at
                    """,
                    (
                        normalized_status,
                        response_status_code,
                        response_body,
                        normalized_next_retry_at,
                        last_error,
                        normalized_status,
                        normalized_delivery_id,
                    ),
                )
                row = cur.fetchone()
            return self._delivery_row_to_api(row) if row else None

        with self._lock:
            row = self._deliveries.get(normalized_delivery_id)
            if row is None:
                return None
            row["delivery_status"] = normalized_status
            row["response_status_code"] = response_status_code
            row["response_body"] = response_body
            row["next_retry_at"] = normalized_next_retry_at.isoformat() if normalized_next_retry_at else None
            row["last_error"] = last_error
            if normalized_status == "delivered":
                row["delivered_at"] = self._now_iso()
            return dict(row)

    def list_deliveries(
        self,
        *,
        tenant_id: int,
        limit: int = 200,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_tenant_id = int(tenant_id)
        normalized_limit = max(1, min(int(limit), 1000))

        if conn is None:
            with transaction() as tx:
                return self.list_deliveries(tenant_id=normalized_tenant_id, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, subscription_id, outbox_event_id, event_type, target_url,
                           request_payload_json, response_status_code, response_body, delivery_status,
                           retry_count, next_retry_at, last_error, created_at, delivered_at
                    FROM app_platform_webhook_deliveries
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (normalized_tenant_id, normalized_limit),
                )
                rows = cur.fetchall()
            return [self._delivery_row_to_api(row) for row in rows]

        with self._lock:
            rows = [dict(item) for item in self._deliveries.values() if int(item["tenant_id"]) == normalized_tenant_id]
        rows.sort(key=lambda item: (str(item["created_at"]), int(item["id"])), reverse=True)
        return rows[:normalized_limit]

    def fetch_retryable_deliveries(
        self,
        *,
        as_of: datetime | None = None,
        limit: int = 200,
        max_retry_count: int = 5,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_as_of = self._normalize_datetime(as_of)
        normalized_limit = max(1, min(int(limit), 1000))
        normalized_max_retry = max(0, int(max_retry_count))

        if conn is None:
            with transaction() as tx:
                return self.fetch_retryable_deliveries(
                    as_of=normalized_as_of,
                    limit=normalized_limit,
                    max_retry_count=normalized_max_retry,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH latest AS (
                        SELECT MAX(id) AS id
                        FROM app_platform_webhook_deliveries
                        GROUP BY subscription_id, outbox_event_id
                    )
                    SELECT d.id, d.tenant_id, d.subscription_id, d.outbox_event_id, d.event_type, d.target_url,
                           d.request_payload_json, d.response_status_code, d.response_body, d.delivery_status,
                           d.retry_count, d.next_retry_at, d.last_error, d.created_at, d.delivered_at
                    FROM app_platform_webhook_deliveries d
                    INNER JOIN latest l ON l.id = d.id
                    WHERE d.delivery_status = 'failed'
                      AND d.retry_count < %s
                      AND d.next_retry_at IS NOT NULL
                      AND d.next_retry_at <= %s
                    ORDER BY d.next_retry_at ASC, d.id ASC
                    LIMIT %s
                    """,
                    (normalized_max_retry, normalized_as_of, normalized_limit),
                )
                rows = cur.fetchall()
            return [self._delivery_row_to_api(row) for row in rows]

        with self._lock:
            grouped: dict[tuple[int, int], dict[str, Any]] = {}
            for item in self._deliveries.values():
                key = (int(item["subscription_id"]), int(item["outbox_event_id"]))
                current = grouped.get(key)
                if current is None or int(item["id"]) > int(current["id"]):
                    grouped[key] = dict(item)

        rows = []
        for item in grouped.values():
            if str(item.get("delivery_status")) != "failed":
                continue
            if int(item.get("retry_count", 0)) >= normalized_max_retry:
                continue
            next_retry_raw = item.get("next_retry_at")
            if not next_retry_raw:
                continue
            next_retry = datetime.fromisoformat(str(next_retry_raw))
            if next_retry.tzinfo is None:
                next_retry = next_retry.replace(tzinfo=timezone.utc)
            if next_retry > normalized_as_of:
                continue
            rows.append(dict(item))

        rows.sort(key=lambda item: (str(item.get("next_retry_at")), int(item["id"])))
        return rows[:normalized_limit]

    def has_delivered_event(
        self,
        *,
        subscription_id: int,
        outbox_event_id: int,
        conn: object | None = None,
    ) -> bool:
        normalized_subscription_id = int(subscription_id)
        normalized_outbox_event_id = int(outbox_event_id)
        if conn is None:
            with transaction() as tx:
                return self.has_delivered_event(
                    subscription_id=normalized_subscription_id,
                    outbox_event_id=normalized_outbox_event_id,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM app_platform_webhook_deliveries
                    WHERE subscription_id = %s
                      AND outbox_event_id = %s
                      AND delivery_status = 'delivered'
                    LIMIT 1
                    """,
                    (normalized_subscription_id, normalized_outbox_event_id),
                )
                row = cur.fetchone()
            return row is not None

        with self._lock:
            return any(
                int(item.get("subscription_id", 0)) == normalized_subscription_id
                and int(item.get("outbox_event_id", 0)) == normalized_outbox_event_id
                and str(item.get("delivery_status", "")).lower() == "delivered"
                for item in self._deliveries.values()
            )

    def count_failed_deliveries(self, *, conn: object | None = None) -> int:
        if conn is None:
            with transaction() as tx:
                return self.count_failed_deliveries(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM app_platform_webhook_deliveries WHERE delivery_status = 'failed'"
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(1 for item in self._deliveries.values() if str(item.get("delivery_status", "")).lower() == "failed")

    def count_dead_deliveries(self, *, conn: object | None = None) -> int:
        if conn is None:
            with transaction() as tx:
                return self.count_dead_deliveries(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM app_platform_webhook_deliveries WHERE delivery_status = 'failed' AND next_retry_at IS NULL"
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(
                1
                for item in self._deliveries.values()
                if str(item.get("delivery_status", "")).lower() == "failed"
                and item.get("next_retry_at") is None
            )

    def count_retry_backlog(self, *, conn: object | None = None) -> int:
        if conn is None:
            with transaction() as tx:
                return self.count_retry_backlog(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM app_platform_webhook_deliveries WHERE delivery_status = 'failed' AND next_retry_at IS NOT NULL"
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return sum(
                1 for item in self._deliveries.values()
                if str(item.get("delivery_status", "")).lower() == "failed" and item.get("next_retry_at") is not None
            )


SHARED_WEBHOOK_REPOSITORY = WebhookRepository()