"""add auth session and mfa state tables

Revision ID: f3e4d5c6b7a9
Revises: f2e3d4c5b6a8
Create Date: 2026-04-01 08:15:00.000000

"""

from __future__ import annotations

from alembic import op


revision = "f3e4d5c6b7a9"
down_revision = "f2e3d4c5b6a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_auth_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            tenant_id BIGINT NOT NULL,
            auth_source TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            user_agent TEXT NOT NULL,
            device_id TEXT NOT NULL,
            device_name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ,
            is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
            revoked_at TIMESTAMPTZ,
            CHECK (length(trim(session_id)) > 0),
            CHECK (tenant_id > 0)
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_tenant_created
        ON app_auth_sessions (user_id, tenant_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_active_by_user
        ON app_auth_sessions (user_id, tenant_id, is_revoked)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_device_active
        ON app_auth_sessions (device_id, user_id, tenant_id, is_revoked)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_mfa_state (
            user_id TEXT NOT NULL,
            tenant_id BIGINT NOT NULL,
            secret_encrypted TEXT,
            pending_secret_encrypted TEXT,
            recovery_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
            enabled BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, tenant_id),
            CHECK (length(trim(user_id)) > 0),
            CHECK (tenant_id > 0)
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mfa_tenant_enabled
        ON app_mfa_state (tenant_id, enabled)
        """
    )



def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_mfa_tenant_enabled")
    op.execute("DROP TABLE IF EXISTS app_mfa_state")

    op.execute("DROP INDEX IF EXISTS idx_auth_sessions_device_active")
    op.execute("DROP INDEX IF EXISTS idx_auth_sessions_active_by_user")
    op.execute("DROP INDEX IF EXISTS idx_auth_sessions_user_tenant_created")
    op.execute("DROP TABLE IF EXISTS app_auth_sessions")
