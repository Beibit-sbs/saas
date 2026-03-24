from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class BillingRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._plans: dict[int, dict[str, Any]] = {}
        self._plan_counter = 0
        self._subscriptions: dict[int, dict[str, Any]] = {}
        self._usage: dict[tuple[int, str, str], dict[str, Any]] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_plan(
        self,
        *,
        code: str,
        name: str,
        price_cents: int,
        features: dict[str, bool],
        limits: dict[str, int],
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_code = code.strip().lower()
        normalized_name = name.strip()
        normalized_price = int(price_cents)
        normalized_features = {str(k): bool(v) for k, v in features.items()}
        normalized_limits = {str(k): int(v) for k, v in limits.items()}

        if conn is None:
            with transaction() as tx:
                return self.create_plan(
                    code=normalized_code,
                    name=normalized_name,
                    price_cents=normalized_price,
                    features=normalized_features,
                    limits=normalized_limits,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_plans (code, name, price_cents, features_json, limits_json, active, created_at)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, true, NOW())
                    RETURNING id, code, name, price_cents, features_json, limits_json, active, created_at
                    """,
                    (
                        normalized_code,
                        normalized_name,
                        normalized_price,
                        psycopg.types.json.Jsonb(normalized_features),
                        psycopg.types.json.Jsonb(normalized_limits),
                    ),
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "code": str(row[1]),
                "name": str(row[2]),
                "price_cents": int(row[3]),
                "features": dict(row[4] or {}),
                "limits": {str(k): int(v) for k, v in dict(row[5] or {}).items()},
                "active": bool(row[6]),
                "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
            }

        with self._lock:
            for existing in self._plans.values():
                if str(existing["code"]) == normalized_code:
                    raise ValueError(f"Plan '{normalized_code}' already exists")
            self._plan_counter += 1
            row = {
                "id": self._plan_counter,
                "code": normalized_code,
                "name": normalized_name,
                "price_cents": normalized_price,
                "features": normalized_features,
                "limits": normalized_limits,
                "active": True,
                "created_at": self._now_iso(),
            }
            self._plans[self._plan_counter] = row
            return dict(row)

    def list_plans(self, *, conn: object | None = None) -> list[dict[str, Any]]:
        if conn is None:
            with transaction() as tx:
                return self.list_plans(conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, code, name, price_cents, features_json, limits_json, active, created_at
                    FROM app_platform_plans
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(row[0]),
                    "code": str(row[1]),
                    "name": str(row[2]),
                    "price_cents": int(row[3]),
                    "features": dict(row[4] or {}),
                    "limits": {str(k): int(v) for k, v in dict(row[5] or {}).items()},
                    "active": bool(row[6]),
                    "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
                }
                for row in rows
            ]

        with self._lock:
            rows = [dict(item) for item in self._plans.values()]
        rows.sort(key=lambda item: int(item["id"]))
        return rows

    def assign_subscription(self, tenant_id: int, plan_code: str, *, conn: object | None = None) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_plan_code = plan_code.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.assign_subscription(normalized_tenant_id, normalized_plan_code, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT id, code FROM app_platform_plans WHERE code = %s AND active = true", (normalized_plan_code,))
                plan = cur.fetchone()
                if plan is None:
                    raise ValueError(f"Plan '{normalized_plan_code}' not found")

                cur.execute(
                    "UPDATE app_platform_subscriptions SET status = 'replaced', ends_at = NOW() WHERE tenant_id = %s AND status = 'active'",
                    (normalized_tenant_id,),
                )
                cur.execute(
                    """
                    INSERT INTO app_platform_subscriptions (tenant_id, plan_id, status, started_at)
                    VALUES (%s, %s, 'active', NOW())
                    RETURNING tenant_id, plan_id, status, started_at
                    """,
                    (normalized_tenant_id, int(plan[0])),
                )
                row = cur.fetchone()
            return {
                "tenant_id": int(row[0]),
                "plan_id": int(row[1]),
                "plan_code": str(plan[1]),
                "status": str(row[2]),
                "started_at": row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
            }

        with self._lock:
            plan = next((item for item in self._plans.values() if str(item["code"]) == normalized_plan_code and bool(item.get("active", True))), None)
            if plan is None:
                raise ValueError(f"Plan '{normalized_plan_code}' not found")
            row = {
                "tenant_id": normalized_tenant_id,
                "plan_id": int(plan["id"]),
                "plan_code": str(plan["code"]),
                "status": "active",
                "started_at": self._now_iso(),
            }
            self._subscriptions[normalized_tenant_id] = row
            return dict(row)

    def get_subscription(self, tenant_id: int, *, conn: object | None = None) -> dict[str, Any] | None:
        normalized_tenant_id = int(tenant_id)
        if conn is None:
            with transaction() as tx:
                return self.get_subscription(normalized_tenant_id, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.tenant_id, s.plan_id, p.code, s.status, s.started_at
                    FROM app_platform_subscriptions s
                    JOIN app_platform_plans p ON p.id = s.plan_id
                    WHERE s.tenant_id = %s AND s.status = 'active'
                    ORDER BY s.started_at DESC
                    LIMIT 1
                    """,
                    (normalized_tenant_id,),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return {
                "tenant_id": int(row[0]),
                "plan_id": int(row[1]),
                "plan_code": str(row[2]),
                "status": str(row[3]),
                "started_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
            }

        with self._lock:
            row = self._subscriptions.get(normalized_tenant_id)
            return dict(row) if row else None

    def list_due_subscriptions(
        self,
        *,
        due_age_seconds: int,
        limit: int = 100,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        normalized_due_age = max(0, int(due_age_seconds))
        normalized_limit = max(1, min(int(limit), 1000))

        if conn is None:
            with transaction() as tx:
                return self.list_due_subscriptions(due_age_seconds=normalized_due_age, limit=normalized_limit, conn=tx)

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.tenant_id, s.plan_id, p.code, s.status, s.started_at
                    FROM app_platform_subscriptions s
                    JOIN app_platform_plans p ON p.id = s.plan_id
                    WHERE s.status = 'active'
                      AND s.started_at <= NOW() - (%s * INTERVAL '1 second')
                    ORDER BY s.started_at ASC
                    LIMIT %s
                    """,
                    (normalized_due_age, normalized_limit),
                )
                rows = cur.fetchall()
            return [
                {
                    "tenant_id": int(row[0]),
                    "plan_id": int(row[1]),
                    "plan_code": str(row[2]),
                    "status": str(row[3]),
                    "started_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                }
                for row in rows
            ]

        threshold = datetime.now(timezone.utc).timestamp() - normalized_due_age
        with self._lock:
            rows = [dict(item) for item in self._subscriptions.values() if str(item.get("status")) == "active"]

        due: list[dict[str, Any]] = []
        for row in rows:
            try:
                started = datetime.fromisoformat(str(row.get("started_at", ""))).timestamp()
            except Exception:
                started = 0.0
            if started <= threshold:
                due.append(row)

        due.sort(key=lambda item: str(item.get("started_at", "")))
        return due[:normalized_limit]

    def increment_usage(
        self,
        tenant_id: int,
        metric: str,
        value: int,
        *,
        period_key: str = "current",
        conn: object | None = None,
    ) -> dict[str, Any]:
        normalized_tenant_id = int(tenant_id)
        normalized_metric = metric.strip().lower()
        normalized_value = int(value)
        normalized_period_key = period_key.strip().lower()

        if conn is None:
            with transaction() as tx:
                return self.increment_usage(
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
                    new_value = int(inserted[0])
                    updated_at = inserted[1]
                else:
                    new_value = int(row[1]) + normalized_value
                    cur.execute(
                        """
                        UPDATE app_platform_usage_counters
                        SET value = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING updated_at
                        """,
                        (new_value, int(row[0])),
                    )
                    updated_at = cur.fetchone()[0]

            return {
                "tenant_id": normalized_tenant_id,
                "metric": normalized_metric,
                "period_key": normalized_period_key,
                "value": new_value,
                "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
            }

        with self._lock:
            key = (normalized_tenant_id, normalized_metric, normalized_period_key)
            current = self._usage.get(
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
            self._usage[key] = current
            return dict(current)
