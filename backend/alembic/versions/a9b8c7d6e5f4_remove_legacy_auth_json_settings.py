"""remove legacy auth json settings with backup

Revision ID: a9b8c7d6e5f4
Revises: f3e4d5c6b7a9
Create Date: 2026-04-01 09:40:00.000000

"""

from __future__ import annotations

from alembic import op


revision = "a9b8c7d6e5f4"
down_revision = "f3e4d5c6b7a9"
branch_labels = None
depends_on = None


LEGACY_KEYS = ("auth.sessions_json", "auth.mfa_state_json")


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_integration_settings_legacy_auth_backup (
            id BIGSERIAL PRIMARY KEY,
            setting_key TEXT NOT NULL,
            setting_value TEXT NOT NULL,
            is_secret BOOLEAN NOT NULL DEFAULT FALSE,
            backed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            source_revision TEXT NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_app_integration_settings_legacy_auth_backup_key
        ON app_integration_settings_legacy_auth_backup (setting_key)
        """
    )
    op.execute(
        f"""
        DO $$
        BEGIN
            IF to_regclass('public.app_integration_settings') IS NULL THEN
                RETURN;
            END IF;

            INSERT INTO app_integration_settings_legacy_auth_backup (
                setting_key,
                setting_value,
                is_secret,
                source_revision
            )
            SELECT
                key,
                value,
                is_secret,
                '{revision}'
            FROM app_integration_settings
            WHERE key IN {LEGACY_KEYS}
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                is_secret = EXCLUDED.is_secret,
                backed_up_at = NOW(),
                source_revision = EXCLUDED.source_revision;

            DELETE FROM app_integration_settings
            WHERE key IN {LEGACY_KEYS};
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF to_regclass('public.app_integration_settings') IS NULL THEN
                RETURN;
            END IF;

            INSERT INTO app_integration_settings (key, value, is_secret)
            SELECT
                backup.setting_key,
                backup.setting_value,
                backup.is_secret
            FROM app_integration_settings_legacy_auth_backup AS backup
            WHERE backup.setting_key IN {LEGACY_KEYS}
            ON CONFLICT (key)
            DO UPDATE SET
                value = EXCLUDED.value,
                is_secret = EXCLUDED.is_secret,
                updated_at = NOW();
        END
        $$;
        """
    )
