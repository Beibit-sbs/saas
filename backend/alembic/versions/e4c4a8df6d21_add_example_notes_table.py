"""add_example_notes_table

Revision ID: e4c4a8df6d21
Revises: b7d3f1a9c2e4
Create Date: 2026-03-18 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e4c4a8df6d21"
down_revision: Union[str, None] = "b7d3f1a9c2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS example_notes (
            id BIGSERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        INSERT INTO app_permissions (code, description)
        VALUES
            ('example.notes.read', 'Read example notes reference module'),
            ('example.notes.manage', 'Manage example notes reference module')
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM app_roles r
        JOIN app_permissions p ON p.code IN ('example.notes.read', 'example.notes.manage')
        WHERE r.name IN ('superadmin', 'admin')
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM app_roles r
        JOIN app_permissions p ON p.code = 'example.notes.read'
        WHERE r.name = 'auditor'
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM app_role_permissions
        WHERE permission_id IN (
            SELECT id FROM app_permissions WHERE code IN ('example.notes.read', 'example.notes.manage')
        )
        """
    )
    op.execute(
        "DELETE FROM app_permissions WHERE code IN ('example.notes.read', 'example.notes.manage')"
    )
    op.execute("DROP TABLE IF EXISTS example_notes")
