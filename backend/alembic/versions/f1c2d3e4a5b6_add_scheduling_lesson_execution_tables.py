"""add scheduling lesson execution tables

Revision ID: f1c2d3e4a5b6
Revises: d9a8b7c6e5f4
Create Date: 2026-04-05 12:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f1c2d3e4a5b6"
down_revision: str | Sequence[str] | None = "d9a8b7c6e5f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_scheduling_lesson_instances",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("actual_date", sa.Date(), nullable=True),
        sa.Column("topic_title", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("planned", "completed", "cancelled", name="scheduling_lesson_status"),
            nullable=False,
            server_default=sa.text("'planned'"),
        ),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_lesson_instances_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["app_scheduling_course_sections.tenant_id", "app_scheduling_course_sections.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_instances_section",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_lesson_instances_tenant_id_id"),
    )
    op.create_index(
        "ix_scheduling_lesson_instances_tenant_section_date",
        "app_scheduling_lesson_instances",
        ["tenant_id", "section_id", "scheduled_date"],
        unique=False,
    )
    op.create_index(
        "ix_scheduling_lesson_instances_tenant_status",
        "app_scheduling_lesson_instances",
        ["tenant_id", "status"],
        unique=False,
    )

    op.create_table(
        "app_scheduling_lesson_attendance",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("lesson_instance_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "attendance_status",
            sa.Enum("present", "absent", "late", "excused", name="scheduling_attendance_status"),
            nullable=False,
            server_default=sa.text("'present'"),
        ),
        sa.Column("marked_by", sa.String(length=255), nullable=False),
        sa.Column("marked_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_lesson_attendance_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "lesson_instance_id"],
            ["app_scheduling_lesson_instances.tenant_id", "app_scheduling_lesson_instances.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_attendance_lesson_instance",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_attendance_student_profile",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_lesson_attendance_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "lesson_instance_id",
            "student_profile_id",
            name="ux_scheduling_lesson_attendance_one_row_per_student",
        ),
    )
    op.create_index(
        "ix_scheduling_lesson_attendance_tenant_lesson",
        "app_scheduling_lesson_attendance",
        ["tenant_id", "lesson_instance_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduling_lesson_attendance_tenant_student",
        "app_scheduling_lesson_attendance",
        ["tenant_id", "student_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scheduling_lesson_attendance_tenant_student", table_name="app_scheduling_lesson_attendance")
    op.drop_index("ix_scheduling_lesson_attendance_tenant_lesson", table_name="app_scheduling_lesson_attendance")
    op.drop_table("app_scheduling_lesson_attendance")

    op.drop_index("ix_scheduling_lesson_instances_tenant_status", table_name="app_scheduling_lesson_instances")
    op.drop_index("ix_scheduling_lesson_instances_tenant_section_date", table_name="app_scheduling_lesson_instances")
    op.drop_table("app_scheduling_lesson_instances")

    op.execute("DROP TYPE IF EXISTS scheduling_attendance_status")
    op.execute("DROP TYPE IF EXISTS scheduling_lesson_status")
