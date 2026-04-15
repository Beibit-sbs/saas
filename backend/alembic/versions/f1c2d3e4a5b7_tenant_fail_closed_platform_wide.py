"""tenant fail-closed platform-wide hardening

Revision ID: f1c2d3e4a5b7
Revises: f0e1d2c3b4a5
Create Date: 2026-03-29 00:00:00.000000

"""

from __future__ import annotations

from alembic import op


revision = "f1c2d3e4a5b7"
down_revision = "f0e1d2c3b4a5"
branch_labels = None
depends_on = None


def _assert_no_null_or_orphan(table: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM {table} WHERE tenant_id IS NULL) THEN
                RAISE EXCEPTION 'tenant remediation required: {table} has NULL tenant_id rows';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM {table} t
                LEFT JOIN app_tenants ten ON ten.id = t.tenant_id
                WHERE ten.id IS NULL
            ) THEN
                RAISE EXCEPTION 'tenant remediation required: {table} has orphan tenant_id rows';
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    # 1) Remove legacy DEFAULT 1 from tenant columns (no implicit tenant assignment).
    op.execute("ALTER TABLE app_audit_events ALTER COLUMN tenant_id DROP DEFAULT")
    op.execute("ALTER TABLE app_ai_models ALTER COLUMN tenant_id DROP DEFAULT")
    op.execute("ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id DROP DEFAULT")
    op.execute("ALTER TABLE app_roles ALTER COLUMN tenant_id DROP DEFAULT")
    op.execute("ALTER TABLE app_role_permissions ALTER COLUMN tenant_id DROP DEFAULT")
    op.execute("ALTER TABLE app_user_roles ALTER COLUMN tenant_id DROP DEFAULT")

    # 2) Deterministic normalization for platform-scoped feature flags only.
    op.execute(
        """
        UPDATE app_platform_feature_flags
        SET tenant_id = 1
        WHERE scope = 'platform' AND tenant_id IS NULL
        """
    )

    # 3) Fail-fast validation for NULL/orphan rows.
    for table in (
        "app_audit_events",
        "app_ai_models",
        "app_ai_usage_logs",
        "app_roles",
        "app_role_permissions",
        "app_user_roles",
        "app_platform_feature_flags",
    ):
        _assert_no_null_or_orphan(table)

    # 4) Enforce non-null tenant constraints where tenant context is mandatory.
    op.execute("ALTER TABLE app_platform_feature_flags ALTER COLUMN tenant_id SET NOT NULL")
        op.execute("ALTER TABLE app_platform_developer_apps ALTER COLUMN tenant_id SET NOT NULL")
    op.execute("ALTER TABLE app_platform_developer_apps ALTER COLUMN tenant_id SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE app_platform_developer_apps ALTER COLUMN tenant_id DROP NOT NULL")
    op.execute("ALTER TABLE app_platform_feature_flags ALTER COLUMN tenant_id DROP NOT NULL")

    op.execute("ALTER TABLE app_user_roles ALTER COLUMN tenant_id SET DEFAULT 1")
    op.execute("ALTER TABLE app_role_permissions ALTER COLUMN tenant_id SET DEFAULT 1")
    op.execute("ALTER TABLE app_roles ALTER COLUMN tenant_id SET DEFAULT 1")
    op.execute("ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id SET DEFAULT 1")
    op.execute("ALTER TABLE app_ai_models ALTER COLUMN tenant_id SET DEFAULT 1")
    op.execute("ALTER TABLE app_audit_events ALTER COLUMN tenant_id SET DEFAULT 1")
