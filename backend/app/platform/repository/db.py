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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_outbox_events (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    processed_at TIMESTAMPTZ,
                    last_error TEXT,
                    correlation_id TEXT,
                    causation_id TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_webhook_subscriptions (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    signing_secret TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    version INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_webhook_deliveries (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    subscription_id BIGINT NOT NULL REFERENCES app_platform_webhook_subscriptions(id) ON DELETE CASCADE,
                    outbox_event_id BIGINT NOT NULL REFERENCES app_platform_outbox_events(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    request_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    response_status_code INTEGER,
                    response_body TEXT,
                    delivery_status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    next_retry_at TIMESTAMPTZ,
                    last_error TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    delivered_at TIMESTAMPTZ,
                    CONSTRAINT ck_platform_webhook_delivery_status CHECK (delivery_status IN ('pending', 'delivered', 'failed'))
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
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_outbox_status_available ON app_platform_outbox_events (status, available_at, created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_outbox_tenant_created ON app_platform_outbox_events (tenant_id, created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_outbox_aggregate ON app_platform_outbox_events (tenant_id, aggregate_type, aggregate_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_webhook_subscriptions_tenant_event ON app_platform_webhook_subscriptions (tenant_id, event_type, is_active)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_webhook_subscriptions_tenant_created ON app_platform_webhook_subscriptions (tenant_id, created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_webhook_deliveries_tenant_created ON app_platform_webhook_deliveries (tenant_id, created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_webhook_deliveries_status_retry ON app_platform_webhook_deliveries (delivery_status, next_retry_at, created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_webhook_deliveries_subscription_event ON app_platform_webhook_deliveries (subscription_id, outbox_event_id, id)"
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    outbox_event_id BIGINT NOT NULL REFERENCES app_platform_outbox_events(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_analytics_events_outbox_event_id UNIQUE (outbox_event_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_tenant_kpi_snapshots (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    snapshot_date DATE NOT NULL,
                    event_counts_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    total_events BIGINT NOT NULL DEFAULT 0,
                    version INTEGER NOT NULL DEFAULT 1,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_kpi_snapshots_tenant_date UNIQUE (tenant_id, snapshot_date)
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_analytics_events_tenant_type ON app_platform_analytics_events (tenant_id, event_type, id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_analytics_events_tenant_created ON app_platform_analytics_events (tenant_id, created_at)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_kpi_snapshots_tenant_date ON app_platform_tenant_kpi_snapshots (tenant_id, snapshot_date DESC)"
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_tenant_metric_snapshots (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    metric_key TEXT NOT NULL,
                    metric_value BIGINT NOT NULL DEFAULT 0,
                    snapshot_date DATE NOT NULL,
                    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    version INTEGER NOT NULL DEFAULT 1,
                    CONSTRAINT uq_metric_snapshots_tenant_metric_date UNIQUE (tenant_id, metric_key, snapshot_date)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_tenant_dashboard_snapshots (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    snapshot_date DATE NOT NULL,
                    snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    version INTEGER NOT NULL DEFAULT 1,
                    CONSTRAINT uq_dashboard_snapshots_tenant_date UNIQUE (tenant_id, snapshot_date)
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_metric_snapshots_tenant_date ON app_platform_tenant_metric_snapshots (tenant_id, snapshot_date DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_metric_snapshots_tenant_key_date ON app_platform_tenant_metric_snapshots (tenant_id, metric_key, snapshot_date DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_dashboard_snapshots_tenant_date ON app_platform_tenant_dashboard_snapshots (tenant_id, snapshot_date DESC)"
            )

            # ---- Automation / Workflow Engine v1 --------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_automation_rules (
                    id          BIGSERIAL PRIMARY KEY,
                    tenant_id   BIGINT NOT NULL,
                    name        VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    event_type  VARCHAR(128) NOT NULL,
                    condition_json  JSONB NOT NULL DEFAULT '{}',
                    actions_json    JSONB NOT NULL DEFAULT '[]',
                    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    version     INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_automation_executions (
                    id              BIGSERIAL PRIMARY KEY,
                    tenant_id       BIGINT NOT NULL,
                    rule_id         BIGINT NOT NULL,
                    event_id        BIGINT NOT NULL,
                    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
                    result_json     JSONB NOT NULL DEFAULT '{}',
                    error_message   TEXT,
                    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_automation_rules_tenant ON app_platform_automation_rules (tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_automation_rules_event_type ON app_platform_automation_rules (tenant_id, event_type)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_automation_executions_tenant ON app_platform_automation_executions (tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_automation_executions_rule ON app_platform_automation_executions (rule_id)"
            )

            # ---- Semantic Context Layer v1 -----------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_context_entities (
                    id          BIGSERIAL PRIMARY KEY,
                    tenant_id   BIGINT NOT NULL,
                    entity_type VARCHAR(64) NOT NULL,
                    entity_id   VARCHAR(128) NOT NULL,
                    data_json   JSONB NOT NULL DEFAULT '{}',
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (tenant_id, entity_type, entity_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_context_relations (
                    id                  BIGSERIAL PRIMARY KEY,
                    tenant_id           BIGINT NOT NULL,
                    source_entity_type  VARCHAR(64) NOT NULL,
                    source_entity_id    VARCHAR(128) NOT NULL,
                    relation_type       VARCHAR(64) NOT NULL,
                    target_entity_type  VARCHAR(64) NOT NULL,
                    target_entity_id    VARCHAR(128) NOT NULL,
                    metadata_json       JSONB NOT NULL DEFAULT '{}',
                    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (tenant_id, source_entity_type, source_entity_id,
                            relation_type, target_entity_type, target_entity_id)
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_context_entities_tenant ON app_platform_context_entities (tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_context_entities_type_id ON app_platform_context_entities (tenant_id, entity_type, entity_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_context_relations_tenant ON app_platform_context_relations (tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_context_relations_source ON app_platform_context_relations (tenant_id, source_entity_type, source_entity_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_context_relations_target ON app_platform_context_relations (tenant_id, target_entity_type, target_entity_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_context_relations_type ON app_platform_context_relations (tenant_id, relation_type)"
            )

            # ---- AI Copilot Foundation v1 -------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_ai_copilot_query_logs (
                    id                      BIGSERIAL PRIMARY KEY,
                    tenant_id               BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    actor_id                VARCHAR(255) NOT NULL,
                    question                TEXT NOT NULL,
                    query_type              VARCHAR(64) NOT NULL,
                    retrieved_sources_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
                    answer_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_ai_copilot_logs_tenant ON app_platform_ai_copilot_query_logs (tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_ai_copilot_logs_created_at ON app_platform_ai_copilot_query_logs (created_at DESC)"
            )

            # ---- AI Copilot Recommendation Layer v1 ---------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_platform_ai_copilot_recommendation_logs (
                    id                      BIGSERIAL PRIMARY KEY,
                    tenant_id               BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
                    actor_id                VARCHAR(255) NOT NULL,
                    question                TEXT NOT NULL,
                    recommendation_type     VARCHAR(128) NOT NULL,
                    context_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
                    recommendation_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_ai_rec_logs_tenant ON app_platform_ai_copilot_recommendation_logs (tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_ai_rec_logs_type ON app_platform_ai_copilot_recommendation_logs (recommendation_type)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_platform_ai_rec_logs_created_at ON app_platform_ai_copilot_recommendation_logs (created_at DESC)"
            )
