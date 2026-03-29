from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class InvoiceRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[tuple[int, str], dict[str, Any]] = {}
        self._counter = 0

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_api(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "period_key": str(row[2]),
            "plan_code": str(row[3]),
            "base_amount_cents": int(row[4]),
            "usage_amount_cents": int(row[5]),
            "total_amount_cents": int(row[6]),
            "currency": str(row[7]),
            "breakdown": dict(row[8] or {}),
            "created_at": row[9].isoformat() if hasattr(row[9], "isoformat") else str(row[9]),
        }

    def clear_state(self, *, conn: object | None = None) -> None:
        if conn is None:
            with transaction() as tx:
                self.clear_state(conn=tx)
                return

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM app_platform_invoices")
            return

        with self._lock:
            self._rows.clear()
            self._counter = 0

    def create_or_get(
        self,
        *,
        tenant_id: int,
        period_key: str,
        plan_code: str,
        base_amount_cents: int,
        usage_amount_cents: int,
        breakdown: dict[str, int],
        currency: str = "USD",
        conn: object | None = None,
    ) -> tuple[dict[str, Any], bool]:
        normalized_tenant_id = int(tenant_id)
        normalized_period_key = str(period_key or "").strip().lower()
        normalized_plan_code = str(plan_code or "").strip().lower()
        normalized_base = int(base_amount_cents)
        normalized_usage = int(usage_amount_cents)
        normalized_total = normalized_base + normalized_usage
        normalized_currency = str(currency or "USD").strip().upper() or "USD"
        normalized_breakdown = {str(k): int(v) for k, v in dict(breakdown or {}).items()}

        if normalized_tenant_id <= 0:
            raise ValueError("tenant_id must be positive")
        if not normalized_period_key:
            raise ValueError("period_key is required")
        if not normalized_plan_code:
            raise ValueError("plan_code is required")

        if conn is None:
            with transaction() as tx:
                return self.create_or_get(
                    tenant_id=normalized_tenant_id,
                    period_key=normalized_period_key,
                    plan_code=normalized_plan_code,
                    base_amount_cents=normalized_base,
                    usage_amount_cents=normalized_usage,
                    breakdown=normalized_breakdown,
                    currency=normalized_currency,
                    conn=tx,
                )

        if conn is not None and db_available() and psycopg is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_invoices (
                        tenant_id,
                        period_key,
                        plan_code,
                        base_amount_cents,
                        usage_amount_cents,
                        total_amount_cents,
                        currency,
                        breakdown_json,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
                    ON CONFLICT (tenant_id, period_key) DO NOTHING
                    RETURNING id, tenant_id, period_key, plan_code, base_amount_cents,
                              usage_amount_cents, total_amount_cents, currency, breakdown_json, created_at
                    """,
                    (
                        normalized_tenant_id,
                        normalized_period_key,
                        normalized_plan_code,
                        normalized_base,
                        normalized_usage,
                        normalized_total,
                        normalized_currency,
                        psycopg.types.json.Jsonb(normalized_breakdown),
                    ),
                )
                created_row = cur.fetchone()
                if created_row is not None:
                    return self._row_to_api(created_row), True

                cur.execute(
                    """
                    SELECT id, tenant_id, period_key, plan_code, base_amount_cents,
                           usage_amount_cents, total_amount_cents, currency, breakdown_json, created_at
                    FROM app_platform_invoices
                    WHERE tenant_id = %s AND period_key = %s
                    LIMIT 1
                    """,
                    (normalized_tenant_id, normalized_period_key),
                )
                existing_row = cur.fetchone()
            if existing_row is None:
                raise RuntimeError("invoice insert/get race detected")
            return self._row_to_api(existing_row), False

        with self._lock:
            key = (normalized_tenant_id, normalized_period_key)
            existing = self._rows.get(key)
            if existing is not None:
                return dict(existing), False

            self._counter += 1
            row = {
                "id": self._counter,
                "tenant_id": normalized_tenant_id,
                "period_key": normalized_period_key,
                "plan_code": normalized_plan_code,
                "base_amount_cents": normalized_base,
                "usage_amount_cents": normalized_usage,
                "total_amount_cents": normalized_total,
                "currency": normalized_currency,
                "breakdown": normalized_breakdown,
                "created_at": self._now_iso(),
            }
            self._rows[key] = row
            return dict(row), True

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
                    SELECT id, tenant_id, period_key, plan_code, base_amount_cents,
                           usage_amount_cents, total_amount_cents, currency, breakdown_json, created_at
                    FROM app_platform_invoices
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
        rows.sort(key=lambda item: (str(item.get("created_at", "")), int(item.get("id", 0))), reverse=True)
        return rows[:normalized_limit]
