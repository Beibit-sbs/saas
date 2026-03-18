"""add_rbac_persistence_tables

Revision ID: b7d3f1a9c2e4
Revises: 9c6f3f3d0d7a
Create Date: 2026-03-15 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7d3f1a9c2e4"
down_revision: Union[str, None] = "9c6f3f3d0d7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_roles (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_permissions (
            id BIGSERIAL PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_role_permissions (
            role_id BIGINT NOT NULL REFERENCES app_roles(id) ON DELETE CASCADE,
            permission_id BIGINT NOT NULL REFERENCES app_permissions(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (role_id, permission_id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_user_roles (
            user_id TEXT NOT NULL,
            role_id BIGINT NOT NULL REFERENCES app_roles(id) ON DELETE CASCADE,
            assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, role_id)
        )
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_role_permissions_role_id ON app_role_permissions (role_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_role_permissions_permission_id ON app_role_permissions (permission_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_user_roles_user_id ON app_user_roles (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_user_roles_role_id ON app_user_roles (role_id)"
    )

    op.execute(
        """
        INSERT INTO app_roles (name, description)
        VALUES
            ('superadmin', 'Full platform access'),
            ('admin', 'Platform administration access'),
            ('auditor', 'Read-only audit and dashboard access')
        ON CONFLICT (name) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_permissions (code, description)
        VALUES
            ('admin.dashboard.read', 'Read admin dashboard'),
            ('admin.roles.manage', 'Manage RBAC roles and assignments'),
            ('admin.audit.read', 'Read audit events'),
            ('admin.integrations.manage', 'Manage integrations settings'),
            ('admin.ai.providers.manage', 'Manage AI providers configuration'),
            ('admin.i18n.manage', 'Manage language catalog'),
            ('admin.users.manage', 'Manage local users'),
            ('admin.backup.manage', 'Manage backups and run backup jobs')
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM app_roles r
        JOIN app_permissions p ON p.code IN (
            'admin.dashboard.read',
            'admin.roles.manage',
            'admin.audit.read',
            'admin.integrations.manage',
            'admin.ai.providers.manage',
            'admin.i18n.manage',
            'admin.users.manage',
            'admin.backup.manage'
        )
        WHERE r.name IN ('superadmin', 'admin')
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM app_roles r
        JOIN app_permissions p ON p.code IN (
            'admin.dashboard.read',
            'admin.audit.read'
        )
        WHERE r.name = 'auditor'
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_app_user_roles_role_id")
    op.execute("DROP INDEX IF EXISTS ix_app_user_roles_user_id")
    op.execute("DROP INDEX IF EXISTS ix_app_role_permissions_permission_id")
    op.execute("DROP INDEX IF EXISTS ix_app_role_permissions_role_id")

    op.execute("DROP TABLE IF EXISTS app_user_roles")
    op.execute("DROP TABLE IF EXISTS app_role_permissions")
    op.execute("DROP TABLE IF EXISTS app_permissions")
    op.execute("DROP TABLE IF EXISTS app_roles")
