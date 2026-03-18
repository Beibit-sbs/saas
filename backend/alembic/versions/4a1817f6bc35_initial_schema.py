"""initial_schema

Revision ID: 4a1817f6bc35
Revises: 
Create Date: 2026-03-15 04:46:52.327700

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4a1817f6bc35'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS app_languages (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            native_name TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            system BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        INSERT INTO app_languages(code, name, native_name, enabled, system)
        VALUES
            ('kk', 'Kazakh',   'Казакша', TRUE, TRUE),
            ('ru', 'Russian',  'Русский', TRUE, TRUE),
            ('en', 'English',  'English', TRUE, TRUE)
        ON CONFLICT (code) DO NOTHING
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS app_integration_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            is_secret BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS app_user_preferences (
            user_id TEXT PRIMARY KEY,
            language_code TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app_user_preferences")
    op.execute("DROP TABLE IF EXISTS app_integration_settings")
    op.execute("DROP TABLE IF EXISTS app_languages")
