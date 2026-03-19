"""add tenants table

Revision ID: d3e5f7a9b1c2
Revises: c8ad3b2e4f10
Create Date: 2026-03-20 12:00:00.000000
"""

from alembic import op


revision = "d3e5f7a9b1c2"
down_revision = "c8ad3b2e4f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_tenants (
            id BIGSERIAL PRIMARY KEY,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        INSERT INTO app_tenants (id, slug, name, status)
        VALUES (1, 'default', 'Default Organization', 'active')
        ON CONFLICT (slug) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_permissions (code, description)
        VALUES
            ('admin.tenants.read', 'Read tenants in admin UI'),
            ('admin.tenants.write', 'Manage tenants in admin UI')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app_tenants")
