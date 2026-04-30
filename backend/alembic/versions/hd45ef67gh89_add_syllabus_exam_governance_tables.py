"""add syllabus and exam governance tables

Revision ID: hd45ef67gh89
Revises: gc34de56fg78
Create Date: 2026-04-24 12:00:00.000000

Creates tables for the syllabus_governance and exam_governance backend modules,
enabling the orphan frontend pages (syllabus-governance, exam-governance) to
persist data in the database.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "hd45ef67gh89"
down_revision: Union[str, None] = "gc34de56fg78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_syllabi",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Text, nullable=True),
        sa.Column("course_code", sa.Text, nullable=False),
        sa.Column("course_title", sa.Text, nullable=False),
        sa.Column("department_id", sa.Text, nullable=False),
        sa.Column("faculty_id", sa.Text, nullable=False),
        sa.Column("term_id", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "app_syllabi_approval_workflows",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Text, nullable=True),
        sa.Column("syllabus_id", sa.Integer, nullable=False),
        sa.Column("current_step", sa.Integer, nullable=False, server_default="1"),
        sa.Column("total_steps", sa.Integer, nullable=False, server_default="4"),
        sa.Column("status", sa.Text, nullable=False, server_default="in_progress"),
        sa.Column(
            "initiated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_table(
        "app_exams",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Text, nullable=True),
        sa.Column("course_code", sa.Text, nullable=False),
        sa.Column("course_title", sa.Text, nullable=False),
        sa.Column("faculty_id", sa.Text, nullable=False),
        sa.Column("exam_type", sa.Text, nullable=False, server_default="midterm"),
        sa.Column("term_id", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="scheduled"),
        sa.Column("scheduled_date", sa.Text, nullable=True),
        sa.Column("scheduled_time", sa.Text, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="120"),
        sa.Column("is_proctored", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("proctoring_mode", sa.Text, nullable=False, server_default="in_person"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_table(
        "app_exam_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Text, nullable=True),
        sa.Column("exam_id", sa.Integer, nullable=False),
        sa.Column("session_date", sa.Text, nullable=True),
        sa.Column("start_time", sa.Text, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="120"),
        sa.Column("room_code", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="scheduled"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("app_exam_sessions")
    op.drop_table("app_exams")
    op.drop_table("app_syllabi_approval_workflows")
    op.drop_table("app_syllabi")
