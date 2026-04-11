"""add app_plans and app_tenant_subscriptions tables

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-04-11 00:00:00.000000

Formalises billing-core tables previously created at runtime via _ensure_db()
in modules/plans/service.py and modules/billing/service.py.
app_plans must be created before app_tenant_subscriptions (FK dependency).
Now that RUNTIME_SCHEMA_BOOTSTRAP_ENABLED defaults to false, this migration
is the authoritative source of both table schemas.
"""
from __future__ import annotations

from alembic import op


revision = "e3f4a5b6c7d8"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # app_plans must come first — app_tenant_subscriptions references it
    op.execute("""
        CREATE TABLE IF NOT EXISTS app_plans (
            id BIGSERIAL PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS app_tenant_subscriptions (
            tenant_id BIGINT PRIMARY KEY REFERENCES app_tenants(id) ON DELETE CASCADE,
            plan_id BIGINT NOT NULL REFERENCES app_plans(id) ON DELETE RESTRICT,
            status TEXT NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            trial_ends_at TIMESTAMPTZ,
            current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            current_period_end TIMESTAMPTZ,
            next_plan_id BIGINT REFERENCES app_plans(id) ON DELETE SET NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK (status IN ('trial', 'active', 'suspended', 'cancelled'))
        )
    """)
    op.execute("""
        ALTER TABLE app_tenant_subscriptions
            ADD COLUMN IF NOT EXISTS next_plan_id BIGINT REFERENCES app_plans(id) ON DELETE SET NULL
    """)


def downgrade() -> None:
    op.drop_table("app_tenant_subscriptions")
    op.drop_table("app_plans")
