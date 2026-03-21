"""phase l saas commercial layer

Revision ID: c3f1a7b9d2e4
Revises: b2c7d1e4f9a8
Create Date: 2026-03-21 00:00:00.000000
"""

from typing import Union

from alembic import op


revision: str = "c3f1a7b9d2e4"
down_revision: Union[str, None] = "b2c7d1e4f9a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_plans (
            id BIGSERIAL PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_app_plans_active ON app_plans (active)")

    op.execute(
        """
        INSERT INTO app_plans (code, name, description, active)
        VALUES
            ('free', 'Free', 'Starter plan', TRUE),
            ('pro', 'Pro', 'Professional plan', TRUE),
            ('enterprise', 'Enterprise', 'Enterprise plan', TRUE)
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_plan_quotas (
            id BIGSERIAL PRIMARY KEY,
            plan_id BIGINT NOT NULL REFERENCES app_plans(id) ON DELETE CASCADE,
            key TEXT NOT NULL,
            limit_value BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (plan_id, key)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_app_plan_quotas_plan_id ON app_plan_quotas (plan_id)")

    op.execute(
        """
        INSERT INTO app_plan_quotas (plan_id, key, limit_value)
        SELECT p.id, q.key, q.limit_value
        FROM app_plans p
        JOIN (
            VALUES
                ('free', 'users', 10),
                ('free', 'jobs_per_day', 100),
                ('free', 'backup_storage_mb', 1024),
                ('free', 'ai_requests_per_day', 200),
                ('free', 'feature_flags', 20),
                ('free', 'integrations', 3),
                ('pro', 'users', 100),
                ('pro', 'jobs_per_day', 1000),
                ('pro', 'backup_storage_mb', 10240),
                ('pro', 'ai_requests_per_day', 5000),
                ('pro', 'feature_flags', 200),
                ('pro', 'integrations', 20),
                ('enterprise', 'users', 100000),
                ('enterprise', 'jobs_per_day', 100000),
                ('enterprise', 'backup_storage_mb', 1048576),
                ('enterprise', 'ai_requests_per_day', 1000000),
                ('enterprise', 'feature_flags', 10000),
                ('enterprise', 'integrations', 1000)
        ) AS q(plan_code, key, limit_value)
          ON p.code = q.plan_code
        ON CONFLICT (plan_id, key) DO NOTHING
        """
    )

    op.execute("ALTER TABLE app_tenants ADD COLUMN IF NOT EXISTS plan_id BIGINT")
    op.execute(
        """
        UPDATE app_tenants
        SET plan_id = p.id
        FROM app_plans p
        WHERE app_tenants.plan_id IS NULL
          AND p.code = 'enterprise'
        """
    )
    op.execute("ALTER TABLE app_tenants ALTER COLUMN plan_id SET NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_app_tenants_plan_id ON app_tenants (plan_id)")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_app_tenants_plan_id'
            ) THEN
                ALTER TABLE app_tenants
                ADD CONSTRAINT fk_app_tenants_plan_id
                FOREIGN KEY (plan_id) REFERENCES app_plans(id);
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_usage_events (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL REFERENCES app_tenants(id),
            metric TEXT NOT NULL,
            value BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_usage_events_tenant_metric_created ON app_usage_events (tenant_id, metric, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_app_usage_events_tenant_metric_created")
    op.execute("DROP TABLE IF EXISTS app_usage_events")

    op.execute("ALTER TABLE app_tenants DROP CONSTRAINT IF EXISTS fk_app_tenants_plan_id")
    op.execute("DROP INDEX IF EXISTS ix_app_tenants_plan_id")
    op.execute("ALTER TABLE app_tenants DROP COLUMN IF EXISTS plan_id")

    op.execute("DROP INDEX IF EXISTS ix_app_plan_quotas_plan_id")
    op.execute("DROP TABLE IF EXISTS app_plan_quotas")

    op.execute("DROP INDEX IF EXISTS ix_app_plans_active")
    op.execute("DROP TABLE IF EXISTS app_plans")
