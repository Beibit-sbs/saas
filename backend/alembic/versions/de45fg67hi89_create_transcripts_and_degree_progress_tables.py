"""create transcripts and degree progress tables

Revision ID: de45fg67hi89
Revises: cd34ef56gh78
Create Date: 2026-03-23 19:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "de45fg67hi89"
down_revision = "cd34ef56gh78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_transcripts_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("enrollment_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("term_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_code", sa.String(length=32), nullable=True),
        sa.Column("grade_points", sa.Numeric(5, 2), nullable=True),
        sa.Column("credits", sa.BigInteger(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_transcript_records_student",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_transcript_records_enrollment",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["app_enrollments_terms.tenant_id", "app_enrollments_terms.id"],
            ondelete="RESTRICT",
            name="fk_transcript_records_term",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_transcript_records_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "enrollment_id", name="ux_transcript_records_enrollment"),
    )
    op.create_index(
        "ix_transcript_records_tenant_student_term",
        "app_transcripts_records",
        ["tenant_id", "student_profile_id", "term_id"],
    )

    op.create_table(
        "app_transcripts_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("generated_by", sa.String(length=255), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
            name="fk_transcript_snapshots_student",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_transcript_snapshots_tenant_id_id"),
    )
    op.create_index(
        "ix_transcript_snapshots_tenant_student_generated",
        "app_transcripts_snapshots",
        ["tenant_id", "student_profile_id", "generated_at"],
    )

    op.create_table(
        "app_degree_progress_requirements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("minimum_credits", sa.BigInteger(), nullable=False),
        sa.Column("minimum_gpa", sa.Numeric(4, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("minimum_credits >= 0", name="ck_degree_requirements_minimum_credits_non_negative"),
        sa.CheckConstraint("minimum_gpa >= 0", name="ck_degree_requirements_minimum_gpa_non_negative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_degree_requirements_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "program_id", "name", name="ux_degree_requirements_program_name"),
    )
    op.create_index(
        "ix_degree_requirements_tenant_program_active",
        "app_degree_progress_requirements",
        ["tenant_id", "program_id", "is_active"],
    )

    op.create_table(
        "app_degree_progress_requirement_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("requirement_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("credits", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("credits >= 0", name="ck_degree_requirement_items_credits_non_negative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "requirement_id"],
            ["app_degree_progress_requirements.tenant_id", "app_degree_progress_requirements.id"],
            ondelete="CASCADE",
            name="fk_degree_requirement_items_requirement",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_degree_requirement_items_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "requirement_id", "course_id", name="ux_degree_requirement_items_unique_course"),
    )
    op.create_index(
        "ix_degree_requirement_items_tenant_requirement",
        "app_degree_progress_requirement_items",
        ["tenant_id", "requirement_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_degree_requirement_items_tenant_requirement", table_name="app_degree_progress_requirement_items")
    op.drop_table("app_degree_progress_requirement_items")

    op.drop_index("ix_degree_requirements_tenant_program_active", table_name="app_degree_progress_requirements")
    op.drop_table("app_degree_progress_requirements")

    op.drop_index("ix_transcript_snapshots_tenant_student_generated", table_name="app_transcripts_snapshots")
    op.drop_table("app_transcripts_snapshots")

    op.drop_index("ix_transcript_records_tenant_student_term", table_name="app_transcripts_records")
    op.drop_table("app_transcripts_records")
