"""add platform webhook system v1

Revision ID: f5a6b7c8d9e0
Revises: f4a5b6c7d8e9
Create Date: 2026-03-24 09:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
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
    op.execute(
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_webhook_subscriptions_tenant_event "
        "ON app_platform_webhook_subscriptions (tenant_id, event_type, is_active)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_webhook_subscriptions_tenant_created "
        "ON app_platform_webhook_subscriptions (tenant_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_webhook_deliveries_tenant_created "
        "ON app_platform_webhook_deliveries (tenant_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_webhook_deliveries_status_retry "
        "ON app_platform_webhook_deliveries (delivery_status, next_retry_at, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_webhook_deliveries_subscription_event "
        "ON app_platform_webhook_deliveries (subscription_id, outbox_event_id, id)"
    )


def downgrade() -> None:
    op.drop_index("ix_platform_webhook_deliveries_subscription_event", table_name="app_platform_webhook_deliveries")
    op.drop_index("ix_platform_webhook_deliveries_status_retry", table_name="app_platform_webhook_deliveries")
    op.drop_index("ix_platform_webhook_deliveries_tenant_created", table_name="app_platform_webhook_deliveries")
    op.drop_index("ix_platform_webhook_subscriptions_tenant_created", table_name="app_platform_webhook_subscriptions")
    op.drop_index("ix_platform_webhook_subscriptions_tenant_event", table_name="app_platform_webhook_subscriptions")
    op.drop_table("app_platform_webhook_deliveries")
    op.drop_table("app_platform_webhook_subscriptions")