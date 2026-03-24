"""create enrollment phase 2 tables

Revision ID: ab12cd34ef56
Revises: d1f3c7a9b4e8
Create Date: 2026-03-23 15:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "ab12cd34ef56"
down_revision = "d1f3c7a9b4e8"
branch_labels = None
depends_on = None


enrollment_status = postgresql.ENUM(
    "pending",
    "enrolled",
    "waitlist",
    "dropped",
    "completed",
    "withdrawn",
    "suspended",
    name="enrollment_status",
    create_type=False,
)
enrollment_type = postgresql.ENUM(
    "regular",
    "audit",
    "retake",
    "transfer_credit",
    name="enrollment_type",
    create_type=False,
)


def upgrade() -> None:
    for enum_type in [enrollment_status, enrollment_type]:
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "app_enrollments_enrollments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("term_key", sa.String(length=64), nullable=False),
        sa.Column(
            "enrollment_status",
            enrollment_status,
            nullable=False,
            server_default=sa.text("'enrolled'"),
        ),
        sa.Column(
            "enrollment_type",
            enrollment_type,
            nullable=False,
            server_default=sa.text("'regular'"),
        ),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("dropped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("version >= 1", name="ck_enrollments_version_positive"),
        sa.CheckConstraint(
            "dropped_at IS NULL OR dropped_at >= enrolled_at",
            name="ck_enrollments_dropped_after_enrolled",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_enrollments_tenant_id_id"),
    )
    op.create_index(
        "ix_enrollments_tenant_student_status",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "enrollment_status"],
    )
    op.create_index(
        "ix_enrollments_tenant_course_term_status",
        "app_enrollments_enrollments",
        ["tenant_id", "course_id", "term_key", "enrollment_status"],
    )
    op.create_index(
        "ix_enrollments_tenant_student_term",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "term_key"],
    )
    op.create_index(
        "ix_enrollments_tenant_enrolled_desc",
        "app_enrollments_enrollments",
        ["tenant_id", "enrolled_at"],
    )
    op.create_index(
        "ix_enrollments_one_active_triplet",
        "app_enrollments_enrollments",
        ["tenant_id", "student_profile_id", "course_id", "term_key"],
        unique=True,
        postgresql_where=sa.text(
            "enrollment_status IN ('pending', 'enrolled', 'waitlist', 'suspended')"
        ),
    )

    op.create_table(
        "app_enrollments_status_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("enrollment_id", sa.BigInteger(), nullable=False),
        sa.Column("from_status", enrollment_status, nullable=True),
        sa.Column("to_status", enrollment_status, nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint(
            "from_status IS NULL OR from_status <> to_status",
            name="ck_enrollment_status_history_transition_changed",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            name="ux_enrollment_status_history_tenant_id_id",
        ),
    )
    op.create_index(
        "ix_enrollment_status_history_tenant_enrollment_changed",
        "app_enrollments_status_history",
        ["tenant_id", "enrollment_id", "changed_at"],
    )
    op.create_index(
        "ix_enrollment_status_history_tenant_to_status_changed",
        "app_enrollments_status_history",
        ["tenant_id", "to_status", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_enrollment_status_history_tenant_to_status_changed",
        table_name="app_enrollments_status_history",
    )
    op.drop_index(
        "ix_enrollment_status_history_tenant_enrollment_changed",
        table_name="app_enrollments_status_history",
    )
    op.drop_table("app_enrollments_status_history")

    op.drop_index(
        "ix_enrollments_one_active_triplet",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_enrolled_desc",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_student_term",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_course_term_status",
        table_name="app_enrollments_enrollments",
    )
    op.drop_index(
        "ix_enrollments_tenant_student_status",
        table_name="app_enrollments_enrollments",
    )
    op.drop_table("app_enrollments_enrollments")

    enrollment_type.drop(op.get_bind(), checkfirst=True)
    enrollment_status.drop(op.get_bind(), checkfirst=True)