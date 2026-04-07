"""add platform events ingestion table v1

Revision ID: a1b2c3d4e5f6
Revises: f7b8c9d0e1f2
Create Date: 2026-04-04 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS platform_events (
            id          BIGSERIAL PRIMARY KEY,
            tenant_id   BIGINT NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
            event_type  TEXT NOT NULL,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_events_tenant_type_created "
        "ON platform_events (tenant_id, event_type, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_events_created "
        "ON platform_events (created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_platform_events_created")
    op.execute("DROP INDEX IF EXISTS ix_platform_events_tenant_type_created")
    op.execute("DROP TABLE IF EXISTS platform_events")
