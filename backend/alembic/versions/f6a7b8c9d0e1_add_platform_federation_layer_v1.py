"""add platform federation layer v1

Revision ID: f6a7b8c9d0e2
Revises: e5f6a7b8c9d0
Create Date: 2026-03-24 11:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f6a7b8c9d0e2"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Institutions table
    op.create_table(
        "app_platform_institutions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("country", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False, server_default="university"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_platform_institutions_code", "app_platform_institutions", ["code"])
    op.create_index("ix_platform_institutions_status", "app_platform_institutions", ["status"])

    # 2. Add institution_id to tenants (additive, nullable)
    op.add_column(
        "app_tenants",
        sa.Column("institution_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tenants_institution_id",
        "app_tenants",
        "app_platform_institutions",
        ["institution_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tenants_institution_id", "app_tenants", ["institution_id"])

    # 3. Federation members table
    op.create_table(
        "app_platform_federation_members",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("institution_id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="institution_admin"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["institution_id"], ["app_platform_institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "tenant_id"),
    )
    op.create_index(
        "ix_federation_members_institution",
        "app_platform_federation_members",
        ["institution_id"],
    )
    op.create_index(
        "ix_federation_members_tenant",
        "app_platform_federation_members",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_federation_members_tenant", "app_platform_federation_members")
    op.drop_index("ix_federation_members_institution", "app_platform_federation_members")
    op.drop_table("app_platform_federation_members")

    op.drop_index("ix_tenants_institution_id", "app_tenants")
    op.drop_constraint("fk_tenants_institution_id", "app_tenants", type_="foreignkey")
    op.drop_column("app_tenants", "institution_id")

    op.drop_index("ix_platform_institutions_status", "app_platform_institutions")
    op.drop_index("ix_platform_institutions_code", "app_platform_institutions")
    op.drop_table("app_platform_institutions")
