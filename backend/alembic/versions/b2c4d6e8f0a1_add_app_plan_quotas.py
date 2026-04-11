"""add app_plan_quotas table

Revision ID: b2c4d6e8f0a1
Revises: e3f4a5b6c7d8
Create Date: 2026-04-11 00:00:01.000000

Formalises quota limits table previously created at runtime via _ensure_db()
in modules/quotas/service.py.
RUNTIME_SCHEMA_BOOTSTRAP_ENABLED defaults to false, so Alembic is now the
authoritative source for this schema.
"""
from __future__ import annotations

from alembic import op


revision = "b2c4d6e8f0a1"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS app_plan_quotas (
            id BIGSERIAL PRIMARY KEY,
            plan_id BIGINT NOT NULL REFERENCES app_plans(id) ON DELETE CASCADE,
            key TEXT NOT NULL,
            limit_value BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (plan_id, key)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_app_plan_quotas_plan_id
            ON app_plan_quotas (plan_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app_plan_quotas")
