"""rbac_tenant_scope

Revision ID: f9a1b2c3d4e5
Revises: e5d6f8a0b2c3
Create Date: 2026-03-20 03:50:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f9a1b2c3d4e5"
down_revision: Union[str, None] = "e5d6f8a0b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE app_roles ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
    op.execute("ALTER TABLE app_role_permissions ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
    op.execute("ALTER TABLE app_user_roles ADD COLUMN IF NOT EXISTS tenant_id BIGINT")

    op.execute("UPDATE app_roles SET tenant_id = 1 WHERE tenant_id IS NULL")

    op.execute(
        """
        UPDATE app_role_permissions rp
        SET tenant_id = r.tenant_id
        FROM app_roles r
        WHERE rp.role_id = r.id AND rp.tenant_id IS NULL
        """
    )
    op.execute("UPDATE app_role_permissions SET tenant_id = 1 WHERE tenant_id IS NULL")

    op.execute(
        """
        UPDATE app_user_roles ur
        SET tenant_id = r.tenant_id
        FROM app_roles r
        WHERE ur.role_id = r.id AND ur.tenant_id IS NULL
        """
    )
    op.execute("UPDATE app_user_roles SET tenant_id = 1 WHERE tenant_id IS NULL")

    op.execute("ALTER TABLE app_roles ALTER COLUMN tenant_id SET NOT NULL")
    op.execute("ALTER TABLE app_role_permissions ALTER COLUMN tenant_id SET NOT NULL")
    op.execute("ALTER TABLE app_user_roles ALTER COLUMN tenant_id SET NOT NULL")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_app_roles_tenant_id'
            ) THEN
                ALTER TABLE app_roles
                ADD CONSTRAINT fk_app_roles_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES app_tenants(id) ON DELETE CASCADE;
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
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_app_role_permissions_tenant_id'
            ) THEN
                ALTER TABLE app_role_permissions
                ADD CONSTRAINT fk_app_role_permissions_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES app_tenants(id) ON DELETE CASCADE;
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
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_app_user_roles_tenant_id'
            ) THEN
                ALTER TABLE app_user_roles
                ADD CONSTRAINT fk_app_user_roles_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES app_tenants(id) ON DELETE CASCADE;
            END IF;
        END
        $$;
        """
    )

    op.execute("ALTER TABLE app_roles DROP CONSTRAINT IF EXISTS app_roles_name_key")

    op.execute("CREATE INDEX IF NOT EXISTS ix_app_roles_tenant_name ON app_roles (tenant_id, name)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_app_roles_tenant_name ON app_roles (tenant_id, name)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_app_roles_tenant_name")
    op.execute("DROP INDEX IF EXISTS ix_app_roles_tenant_name")

    op.execute("ALTER TABLE app_roles DROP CONSTRAINT IF EXISTS fk_app_roles_tenant_id")
    op.execute("ALTER TABLE app_role_permissions DROP CONSTRAINT IF EXISTS fk_app_role_permissions_tenant_id")
    op.execute("ALTER TABLE app_user_roles DROP CONSTRAINT IF EXISTS fk_app_user_roles_tenant_id")

    op.execute("ALTER TABLE app_user_roles DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE app_role_permissions DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE app_roles DROP COLUMN IF EXISTS tenant_id")

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS app_roles_name_key ON app_roles (name)")
