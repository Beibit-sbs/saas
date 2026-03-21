"""audit_tenant_scope

Revision ID: a1d4e9c7b2f6
Revises: f9a1b2c3d4e5
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1d4e9c7b2f6"
down_revision: Union[str, None] = "f9a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("app_audit_events", sa.Column("tenant_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_app_audit_events_tenant_id",
        "app_audit_events",
        "app_tenants",
        ["tenant_id"],
        ["id"],
    )
    op.execute("UPDATE app_audit_events SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.create_index(
        "ix_app_audit_events_tenant_created",
        "app_audit_events",
        ["tenant_id", "timestamp"],
        unique=False,
    )
    op.alter_column("app_audit_events", "tenant_id", nullable=False)


def downgrade() -> None:
    op.alter_column("app_audit_events", "tenant_id", nullable=True)
    op.drop_index("ix_app_audit_events_tenant_created", table_name="app_audit_events")
    op.drop_constraint("fk_app_audit_events_tenant_id", "app_audit_events", type_="foreignkey")
    op.drop_column("app_audit_events", "tenant_id")
