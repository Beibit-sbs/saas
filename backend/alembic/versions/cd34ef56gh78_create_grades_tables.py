"""create grades tables

Revision ID: cd34ef56gh78
Revises: bc23de45fg67
Create Date: 2026-03-23 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "cd34ef56gh78"
down_revision = "bc23de45fg67"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_grades_scales",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_grades_scales_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "name", name="ux_grades_scales_tenant_name"),
    )
    op.create_index("ix_grades_scales_tenant_active", "app_grades_scales", ["tenant_id", "is_active"])

    op.create_table(
        "app_grades_scale_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("scale_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_code", sa.String(length=32), nullable=False),
        sa.Column("grade_points", sa.Numeric(5, 2), nullable=False),
        sa.Column("min_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_percentage", sa.Numeric(5, 2), nullable=False),
        sa.CheckConstraint("min_percentage >= 0", name="ck_grades_scale_items_min_non_negative"),
        sa.CheckConstraint("max_percentage <= 100", name="ck_grades_scale_items_max_hundred"),
        sa.CheckConstraint("min_percentage <= max_percentage", name="ck_grades_scale_items_range_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "scale_id"],
            ["app_grades_scales.tenant_id", "app_grades_scales.id"],
            ondelete="CASCADE",
            name="fk_grades_scale_items_scale",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_grades_scale_items_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "scale_id", "grade_code", name="ux_grades_scale_items_scale_code"),
    )
    op.create_index("ix_grades_scale_items_tenant_scale", "app_grades_scale_items", ["tenant_id", "scale_id"])

    op.create_table(
        "app_grades_submissions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("enrollment_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_code", sa.String(length=32), nullable=False),
        sa.Column("grade_points", sa.Numeric(5, 2), nullable=False),
        sa.Column("grading_scale_id", sa.BigInteger(), nullable=False),
        sa.Column("submitted_by", sa.String(length=255), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("version >= 1", name="ck_grades_submissions_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_grades_submissions_enrollment",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "grading_scale_id"],
            ["app_grades_scales.tenant_id", "app_grades_scales.id"],
            ondelete="RESTRICT",
            name="fk_grades_submissions_scale",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_grades_submissions_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "enrollment_id", name="ux_grades_submissions_active_enrollment"),
    )
    op.create_index("ix_grades_submissions_tenant_scale", "app_grades_submissions", ["tenant_id", "grading_scale_id"])

    op.create_table(
        "app_grades_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("enrollment_id", sa.BigInteger(), nullable=False),
        sa.Column("previous_grade_code", sa.String(length=32), nullable=True),
        sa.Column("new_grade_code", sa.String(length=32), nullable=False),
        sa.Column("previous_grade_points", sa.Numeric(5, 2), nullable=True),
        sa.Column("new_grade_points", sa.Numeric(5, 2), nullable=False),
        sa.Column("changed_by", sa.String(length=255), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("version", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_grades_history_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_grades_history_enrollment",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_grades_history_tenant_id_id"),
    )
    op.create_index(
        "ix_grades_history_tenant_enrollment_changed",
        "app_grades_history",
        ["tenant_id", "enrollment_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_grades_history_tenant_enrollment_changed", table_name="app_grades_history")
    op.drop_table("app_grades_history")

    op.drop_index("ix_grades_submissions_tenant_scale", table_name="app_grades_submissions")
    op.drop_table("app_grades_submissions")

    op.drop_index("ix_grades_scale_items_tenant_scale", table_name="app_grades_scale_items")
    op.drop_table("app_grades_scale_items")

    op.drop_index("ix_grades_scales_tenant_active", table_name="app_grades_scales")
    op.drop_table("app_grades_scales")
