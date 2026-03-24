"""platform core sprint c1 application idempotency

Revision ID: f3a4b5c6d7e8
Revises: f2a3b4c5d6e7
Create Date: 2026-03-23 21:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE app_platform_notifications ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE app_platform_notifications ADD COLUMN IF NOT EXISTS last_error TEXT")
    op.execute("ALTER TABLE app_platform_notifications ALTER COLUMN retry_count DROP DEFAULT")

    op.execute(
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
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_platform_idempotency_tenant_key_operation "
        "ON platform_idempotency_keys (tenant_id, key, operation)"
    )


def downgrade() -> None:
    op.drop_index("ux_platform_idempotency_tenant_key_operation", table_name="platform_idempotency_keys")
    op.drop_table("platform_idempotency_keys")
    op.drop_column("app_platform_notifications", "last_error")
    op.drop_column("app_platform_notifications", "retry_count")
