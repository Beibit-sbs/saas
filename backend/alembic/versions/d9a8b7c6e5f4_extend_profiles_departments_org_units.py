"""Extend profiles departments with org unit fields.

Revision ID: d9a8b7c6e5f4
Revises: c51043de2d5f
Create Date: 2026-04-05 18:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9a8b7c6e5f4"
down_revision: Union[str, None] = "c51043de2d5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_profiles_departments",
        sa.Column("unit_type", sa.String(length=64), nullable=False, server_default=sa.text("'department'")),
    )
    op.add_column("app_profiles_departments", sa.Column("head_person_id", sa.BigInteger(), nullable=True))
    op.add_column("app_profiles_departments", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("app_profiles_departments", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("app_profiles_departments", sa.Column("location", sa.String(length=500), nullable=True))

    op.create_index(
        "ix_profiles_departments_tenant_type",
        "app_profiles_departments",
        ["tenant_id", "unit_type"],
        unique=False,
    )
    op.create_index(
        "ix_profiles_departments_tenant_head",
        "app_profiles_departments",
        ["tenant_id", "head_person_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_profiles_departments_head_person",
        "app_profiles_departments",
        "app_profiles_people",
        ["tenant_id", "head_person_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_profiles_departments_head_person", "app_profiles_departments", type_="foreignkey")
    op.drop_index("ix_profiles_departments_tenant_head", table_name="app_profiles_departments")
    op.drop_index("ix_profiles_departments_tenant_type", table_name="app_profiles_departments")

    op.drop_column("app_profiles_departments", "location")
    op.drop_column("app_profiles_departments", "phone")
    op.drop_column("app_profiles_departments", "email")
    op.drop_column("app_profiles_departments", "head_person_id")
    op.drop_column("app_profiles_departments", "unit_type")
