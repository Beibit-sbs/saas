from __future__ import annotations

from contextlib import contextmanager
import os
from threading import Lock
from typing import Iterator

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


_schema_lock = Lock()
_MEMORY_TX = object()


def db_url() -> str | None:
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        return None
    return raw.replace("postgresql+psycopg://", "postgresql://", 1)


def db_available() -> bool:
    return bool(db_url()) and psycopg is not None


@contextmanager
def transaction() -> Iterator[object]:
    url = db_url()
    if not url or psycopg is None:
        # Use a sentinel object so repository methods don't recurse back into
        # transaction() when running in in-memory fallback mode.
        yield _MEMORY_TX
        return

    with psycopg.connect(url, connect_timeout=5) as conn:
        try:
            ensure_platform_core_schema(conn)
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def ensure_platform_core_schema(conn: object) -> None:
    if psycopg is None:
        return

    with _schema_lock:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_tenant_settings (
                    tenant_id BIGINT PRIMARY KEY REFERENCES app_tenants(id) ON DELETE CASCADE,
                    status TEXT NOT NULL DEFAULT 'active',
                    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    quotas_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    limits_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_feature_flags (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT REFERENCES app_tenants(id) ON DELETE CASCADE,
                    scope TEXT NOT NULL,
                    module TEXT NOT NULL,
                    key TEXT NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT false,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_plans (
                    id BIGSERIAL PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    price_cents INTEGER NOT NULL DEFAULT 0,
                    features_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    limits_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_subscriptions (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    plan_id BIGINT NOT NULL REFERENCES app_platform_plans(id) ON DELETE RESTRICT,
                    status TEXT NOT NULL DEFAULT 'active',
                    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    ends_at TIMESTAMPTZ
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_usage_counters (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    metric TEXT NOT NULL,
                    period_key TEXT NOT NULL,
                    value BIGINT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_jobs (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    result_json JSONB,
                    last_error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_notifications (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    channel TEXT NOT NULL,
                    target TEXT NOT NULL,
                    subject TEXT,
                    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    status TEXT NOT NULL DEFAULT 'queued',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute("ALTER TABLE app_platform_notifications ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0")
            cur.execute("ALTER TABLE app_platform_notifications ADD COLUMN IF NOT EXISTS last_error TEXT")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS platform_idempotency_keys (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    key TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL
                )
                """
            )

            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_platform_usage_tenant_metric_period ON app_platform_usage_counters (tenant_id, metric, period_key)"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_platform_feature_flags_scope_tenant_module_key ON app_platform_feature_flags (scope, tenant_id, module, key)"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_platform_subscriptions_active_per_tenant ON app_platform_subscriptions (tenant_id) WHERE status = 'active'"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_platform_idempotency_tenant_key_operation ON platform_idempotency_keys (tenant_id, key, operation)"
            )
