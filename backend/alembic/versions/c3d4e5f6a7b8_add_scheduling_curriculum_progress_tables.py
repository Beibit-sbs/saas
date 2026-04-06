"""add scheduling curriculum and progress tables

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-04-06 05:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_scheduling_disciplines",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("unique_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("credits", sa.BigInteger(), nullable=True),
        sa.Column("prerequisites_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("learning_outcomes_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("credits IS NULL OR credits >= 0", name="ck_scheduling_disciplines_credits_non_negative"),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_disciplines_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_disciplines_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "unique_code", name="ux_scheduling_disciplines_tenant_code"),
    )
    op.create_index(
        "ix_scheduling_disciplines_tenant_active",
        "app_scheduling_disciplines",
        ["tenant_id", "is_active"],
        unique=False,
    )

    op.create_table(
        "app_scheduling_lesson_topics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("discipline_id", sa.BigInteger(), nullable=False),
        sa.Column("module_num", sa.BigInteger(), nullable=False),
        sa.Column("topic_num", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column(
            "difficulty_level",
            sa.Enum("beginner", "intermediate", "advanced", name="scheduling_topic_difficulty_level"),
            nullable=False,
            server_default=sa.text("'beginner'"),
        ),
        sa.Column("recommended_materials_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("module_num >= 1", name="ck_scheduling_lesson_topics_module_num_positive"),
        sa.CheckConstraint("topic_num >= 1", name="ck_scheduling_lesson_topics_topic_num_positive"),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_lesson_topics_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "discipline_id"],
            ["app_scheduling_disciplines.tenant_id", "app_scheduling_disciplines.id"],
            ondelete="CASCADE",
            name="fk_scheduling_lesson_topics_discipline",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_lesson_topics_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "discipline_id",
            "module_num",
            "topic_num",
            name="ux_scheduling_lesson_topics_tenant_discipline_module_topic",
        ),
    )
    op.create_index(
        "ix_scheduling_lesson_topics_tenant_discipline",
        "app_scheduling_lesson_topics",
        ["tenant_id", "discipline_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduling_lesson_topics_tenant_difficulty",
        "app_scheduling_lesson_topics",
        ["tenant_id", "difficulty_level"],
        unique=False,
    )

    op.create_table(
        "app_scheduling_student_topic_progress",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("topic_id", sa.BigInteger(), nullable=False),
        sa.Column("discipline_id", sa.BigInteger(), nullable=False),
        sa.Column("first_seen_date", sa.Date(), nullable=True),
        sa.Column("last_reviewed_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("not_started", "in_progress", "completed", name="scheduling_topic_progress_status"),
            nullable=False,
            server_default=sa.text("'not_started'"),
        ),
        sa.Column("materials_opened", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("materials_completed", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("quiz_attempts", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("quiz_best_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("materials_opened >= 0", name="ck_sched_stp_mat_open_ge0"),
        sa.CheckConstraint(
            "materials_completed >= 0",
            name="ck_sched_stp_mat_done_ge0",
        ),
        sa.CheckConstraint("quiz_attempts >= 0", name="ck_sched_stp_quiz_attempts_ge0"),
        sa.CheckConstraint(
            "quiz_best_score IS NULL OR (quiz_best_score >= 0 AND quiz_best_score <= 100)",
            name="ck_sched_stp_quiz_score_range",
        ),
        sa.CheckConstraint("version >= 1", name="ck_sched_stp_ver_ge1"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "discipline_id"],
            ["app_scheduling_disciplines.tenant_id", "app_scheduling_disciplines.id"],
            ondelete="CASCADE",
            name="fk_scheduling_student_topic_progress_discipline",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "topic_id"],
            ["app_scheduling_lesson_topics.tenant_id", "app_scheduling_lesson_topics.id"],
            ondelete="CASCADE",
            name="fk_scheduling_student_topic_progress_topic",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_scheduling_student_topic_progress_student_profile",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_student_topic_progress_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_profile_id",
            "topic_id",
            name="ux_scheduling_student_topic_progress_student_topic",
        ),
    )
    op.create_index(
        "ix_scheduling_student_topic_progress_tenant_student",
        "app_scheduling_student_topic_progress",
        ["tenant_id", "student_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduling_student_topic_progress_tenant_topic",
        "app_scheduling_student_topic_progress",
        ["tenant_id", "topic_id"],
        unique=False,
    )
    op.create_index(
        "ix_scheduling_student_topic_progress_tenant_status",
        "app_scheduling_student_topic_progress",
        ["tenant_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scheduling_student_topic_progress_tenant_status",
        table_name="app_scheduling_student_topic_progress",
    )
    op.drop_index(
        "ix_scheduling_student_topic_progress_tenant_topic",
        table_name="app_scheduling_student_topic_progress",
    )
    op.drop_index(
        "ix_scheduling_student_topic_progress_tenant_student",
        table_name="app_scheduling_student_topic_progress",
    )
    op.drop_table("app_scheduling_student_topic_progress")

    op.drop_index("ix_scheduling_lesson_topics_tenant_difficulty", table_name="app_scheduling_lesson_topics")
    op.drop_index("ix_scheduling_lesson_topics_tenant_discipline", table_name="app_scheduling_lesson_topics")
    op.drop_table("app_scheduling_lesson_topics")

    op.drop_index("ix_scheduling_disciplines_tenant_active", table_name="app_scheduling_disciplines")
    op.drop_table("app_scheduling_disciplines")

    op.execute("DROP TYPE IF EXISTS scheduling_topic_progress_status")
    op.execute("DROP TYPE IF EXISTS scheduling_topic_difficulty_level")
