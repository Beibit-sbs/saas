"""add i18n settings table for default language persistence

Revision ID: f2e3d4c5b6a8
Revises: f1c2d3e4a5b7
Create Date: 2026-03-30 00:40:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision = "f2e3d4c5b6a8"
down_revision = "f1c2d3e4a5b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_languages (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            native_name TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            system BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        INSERT INTO app_languages(code, name, native_name, enabled, system)
        VALUES
            ('kk', 'Kazakh', 'Казакша', TRUE, TRUE),
            ('ru', 'Russian', 'Русский', TRUE, TRUE),
            ('en', 'English', 'English', TRUE, TRUE)
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_i18n_settings (
            id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            default_language TEXT NOT NULL DEFAULT 'ru',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        INSERT INTO app_i18n_settings(id, default_language)
        VALUES (1, 'ru')
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app_i18n_settings")
