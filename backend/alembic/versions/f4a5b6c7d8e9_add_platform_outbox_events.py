"""add platform outbox events

Revision ID: f4a5b6c7d8e9
Revises: f3a4b5c6d7e8
Create Date: 2026-03-24 05:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
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
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_outbox_status_available "
        "ON app_platform_outbox_events (status, available_at, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_outbox_tenant_created "
        "ON app_platform_outbox_events (tenant_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_outbox_aggregate "
        "ON app_platform_outbox_events (tenant_id, aggregate_type, aggregate_id)"
    )


def downgrade() -> None:
    op.drop_index("ix_platform_outbox_aggregate", table_name="app_platform_outbox_events")
    op.drop_index("ix_platform_outbox_tenant_created", table_name="app_platform_outbox_events")
    op.drop_index("ix_platform_outbox_status_available", table_name="app_platform_outbox_events")
    op.drop_table("app_platform_outbox_events")