"""Add org_structure org_units table.

Revision ID: b1c2d3e4f5a6
Revises: f2d3e4a5b6c7
Create Date: 2026-04-06 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "f2d3e4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_org_org_units",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column(
            "unit_type",
            sa.Enum(
                "university", "school", "faculty", "department",
                "umo", "registrar_office", "deans_office",
                "advisory_unit", "academic_committee", "academic_commission",
                name="org_unit_type",
            ),
            nullable=False,
        ),
        sa.Column("parent_unit_id", sa.BigInteger(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("head_person_id", sa.BigInteger(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_org_org_units"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app_tenants.id"],
            name="fk_org_org_units_tenant",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "parent_unit_id"],
            ["app_org_org_units.tenant_id", "app_org_org_units.id"],
            name="fk_org_units_parent",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("tenant_id", "code", name="ux_org_org_units_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_org_org_units_tenant_id_id"),
        sa.CheckConstraint(
            "parent_unit_id IS NULL OR parent_unit_id != id",
            name="ck_org_org_units_no_self_parent",
        ),
    )

    op.create_index(
        "ix_org_org_units_tenant_type",
        "app_org_org_units",
        ["tenant_id", "unit_type"],
    )
    op.create_index(
        "ix_org_org_units_tenant_parent",
        "app_org_org_units",
        ["tenant_id", "parent_unit_id"],
    )
    op.create_index(
        "ix_org_org_units_tenant_active",
        "app_org_org_units",
        ["tenant_id", "active"],
    )


def downgrade() -> None:
    op.drop_index("ix_org_org_units_tenant_active", table_name="app_org_org_units")
    op.drop_index("ix_org_org_units_tenant_parent", table_name="app_org_org_units")
    op.drop_index("ix_org_org_units_tenant_type", table_name="app_org_org_units")
    op.drop_table("app_org_org_units")
    op.execute("DROP TYPE IF EXISTS org_unit_type")
