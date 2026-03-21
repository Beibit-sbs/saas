"""enable rls for ai gateway tenant tables

Revision ID: f6a2d1e9b3c4
Revises: c51043de2d5f
Create Date: 2026-03-22 03:00:00.000000
"""

from alembic import op


revision = "f6a2d1e9b3c4"
down_revision = "c51043de2d5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.app_ai_models') IS NOT NULL THEN
                ALTER TABLE app_ai_models ENABLE ROW LEVEL SECURITY;
                ALTER TABLE app_ai_models FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS app_ai_models_tenant_rls ON app_ai_models;
                CREATE POLICY app_ai_models_tenant_rls
                  ON app_ai_models
                  USING (
                    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::BIGINT
                  )
                  WITH CHECK (
                    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::BIGINT
                  );
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.app_ai_usage_logs') IS NOT NULL THEN
                ALTER TABLE app_ai_usage_logs ENABLE ROW LEVEL SECURITY;
                ALTER TABLE app_ai_usage_logs FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS app_ai_usage_logs_tenant_rls ON app_ai_usage_logs;
                CREATE POLICY app_ai_usage_logs_tenant_rls
                  ON app_ai_usage_logs
                  USING (
                    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::BIGINT
                  )
                  WITH CHECK (
                    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::BIGINT
                  );
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.app_ai_models') IS NOT NULL THEN
                DROP POLICY IF EXISTS app_ai_models_tenant_rls ON app_ai_models;
                ALTER TABLE app_ai_models NO FORCE ROW LEVEL SECURITY;
                ALTER TABLE app_ai_models DISABLE ROW LEVEL SECURITY;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.app_ai_usage_logs') IS NOT NULL THEN
                DROP POLICY IF EXISTS app_ai_usage_logs_tenant_rls ON app_ai_usage_logs;
                ALTER TABLE app_ai_usage_logs NO FORCE ROW LEVEL SECURITY;
                ALTER TABLE app_ai_usage_logs DISABLE ROW LEVEL SECURITY;
            END IF;
        END
        $$;
        """
    )
