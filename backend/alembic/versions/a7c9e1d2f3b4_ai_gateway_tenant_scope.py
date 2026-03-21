"""ai gateway tenant scope for model registry and usage logs

Revision ID: a7c9e1d2f3b4
Revises: e5d6f8a0b2c3
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op


revision = "a7c9e1d2f3b4"
down_revision = "e5d6f8a0b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE app_ai_models ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
    op.execute("UPDATE app_ai_models SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.execute("ALTER TABLE app_ai_models ALTER COLUMN tenant_id SET NOT NULL")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'app_ai_models_pkey'
                  AND conrelid = 'app_ai_models'::regclass
            ) THEN
                ALTER TABLE app_ai_models DROP CONSTRAINT app_ai_models_pkey;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'pk_app_ai_models_tenant_model'
                  AND conrelid = 'app_ai_models'::regclass
            ) THEN
                ALTER TABLE app_ai_models
                ADD CONSTRAINT pk_app_ai_models_tenant_model PRIMARY KEY (tenant_id, model_key);
            END IF;
        END
        $$;
        """
    )

    op.execute("DROP INDEX IF EXISTS ix_app_ai_models_provider_enabled")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_ai_models_tenant_provider_enabled ON app_ai_models (tenant_id, provider, enabled)"
    )

    op.execute("ALTER TABLE app_ai_usage_logs ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
    op.execute("UPDATE app_ai_usage_logs SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.execute("ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id SET NOT NULL")

    op.execute("DROP INDEX IF EXISTS ix_app_ai_usage_logs_timestamp")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_ai_usage_logs_tenant_timestamp ON app_ai_usage_logs (tenant_id, timestamp DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_app_ai_usage_logs_tenant_timestamp")
    op.execute("CREATE INDEX IF NOT EXISTS ix_app_ai_usage_logs_timestamp ON app_ai_usage_logs (timestamp DESC)")
    op.execute("ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id DROP NOT NULL")

    op.execute("DROP INDEX IF EXISTS ix_app_ai_models_tenant_provider_enabled")
    op.execute("CREATE INDEX IF NOT EXISTS ix_app_ai_models_provider_enabled ON app_ai_models (provider, enabled)")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM app_ai_models
                GROUP BY model_key
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION 'cannot downgrade ai model tenant scope: duplicate model_key values exist across tenants';
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'pk_app_ai_models_tenant_model'
                  AND conrelid = 'app_ai_models'::regclass
            ) THEN
                ALTER TABLE app_ai_models DROP CONSTRAINT pk_app_ai_models_tenant_model;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'app_ai_models_pkey'
                  AND conrelid = 'app_ai_models'::regclass
            ) THEN
                ALTER TABLE app_ai_models ADD CONSTRAINT app_ai_models_pkey PRIMARY KEY (model_key);
            END IF;
        END
        $$;
        """
    )

    op.execute("ALTER TABLE app_ai_models ALTER COLUMN tenant_id DROP NOT NULL")
