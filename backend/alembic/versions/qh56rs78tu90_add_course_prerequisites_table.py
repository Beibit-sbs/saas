"""add_course_prerequisites_table

Revision ID: qh56rs78tu90
Revises: pg45qr67st89
Create Date: 2026-01-01 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "qh56rs78tu90"
down_revision: str | None = "pg45qr67st89"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "university_course_prerequisites",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("prerequisite_course_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["university_courses.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["prerequisite_course_id"],
            ["university_courses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prereq",
        ),
    )
    op.create_index(
        "ix_course_prereq_course_id",
        "university_course_prerequisites",
        ["tenant_id", "course_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_course_prereq_course_id", table_name="university_course_prerequisites")
    op.drop_table("university_course_prerequisites")
