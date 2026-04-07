"""create students phase 1 tables

Revision ID: d1f3c7a9b4e8
Revises: 7c2e9a4b1d0f
Create Date: 2026-03-23 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "d1f3c7a9b4e8"
down_revision = "c2e4a6f8b0d3"
branch_labels = None
depends_on = None


student_status = postgresql.ENUM(
    "admitted",
    "active",
    "inactive",
    "leave_of_absence",
    "suspended",
    "graduated",
    "withdrawn",
    name="student_status",
    create_type=False,
)
student_academic_level = postgresql.ENUM(
    "undergraduate",
    "graduate",
    "doctoral",
    "non_degree",
    "certificate",
    name="student_academic_level",
    create_type=False,
)
student_admission_source = postgresql.ENUM(
    "admissions_workflow",
    "manual",
    "external_sync",
    "migration",
    name="student_admission_source",
    create_type=False,
)
student_program_binding_state = postgresql.ENUM(
    "active",
    "inactive",
    name="student_program_binding_state",
    create_type=False,
)


def upgrade() -> None:
    enum_types = [
        student_status,
        student_academic_level,
        student_admission_source,
        student_program_binding_state,
    ]
    for enum_type in enum_types:
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "app_students_profiles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("student_number", sa.String(length=64), nullable=False),
        sa.Column("cohort_year", sa.SmallInteger(), nullable=False),
        sa.Column("academic_level", student_academic_level, nullable=True),
        sa.Column("current_status", student_status, nullable=False, server_default=sa.text("'admitted'")),
        sa.Column(
            "admission_source",
            student_admission_source,
            nullable=False,
            server_default=sa.text("'admissions_workflow'"),
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_students_profiles_version_positive"),
        sa.CheckConstraint(
            "cohort_year >= 2000 AND cohort_year <= 2100",
            name="ck_students_profiles_cohort_year_range",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_students_profiles_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "person_id", name="ux_students_profiles_tenant_person"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_number",
            name="ux_students_profiles_tenant_student_number",
        ),
    )
    op.create_index(
        "ix_students_profiles_tenant_status",
        "app_students_profiles",
        ["tenant_id", "current_status"],
    )
    op.create_index(
        "ix_students_profiles_tenant_cohort",
        "app_students_profiles",
        ["tenant_id", "cohort_year"],
    )
    op.create_index(
        "ix_students_profiles_tenant_person",
        "app_students_profiles",
        ["tenant_id", "person_id"],
    )

    op.create_table(
        "app_students_status_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("from_status", student_status, nullable=True),
        sa.Column("to_status", student_status, nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint(
            "from_status IS NULL OR from_status <> to_status",
            name="ck_students_status_history_transition_changed",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_students_status_history_tenant_id_id"),
    )
    op.create_index(
        "ix_students_status_history_tenant_student_changed_desc",
        "app_students_status_history",
        ["tenant_id", "student_profile_id", "changed_at"],
    )
    op.create_index(
        "ix_students_status_history_tenant_to_status_changed_desc",
        "app_students_status_history",
        ["tenant_id", "to_status", "changed_at"],
    )

    op.create_table(
        "app_students_program_bindings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "binding_state",
            student_program_binding_state,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_students_program_bindings_version_positive",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_students_program_bindings_end_after_start",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["app_profiles_programs.tenant_id", "app_profiles_programs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            name="ux_students_program_bindings_tenant_id_id",
        ),
    )
    op.create_index(
        "ix_students_program_bindings_tenant_student_state",
        "app_students_program_bindings",
        ["tenant_id", "student_profile_id", "binding_state"],
    )
    op.create_index(
        "ix_students_program_bindings_tenant_program_state",
        "app_students_program_bindings",
        ["tenant_id", "program_id", "binding_state"],
    )
    op.create_index(
        "ix_students_program_bindings_one_active_primary",
        "app_students_program_bindings",
        ["tenant_id", "student_profile_id"],
        unique=True,
        postgresql_where=sa.text("binding_state = 'active' AND is_primary = true"),
    )
    op.create_index(
        "ix_students_program_bindings_one_active_program",
        "app_students_program_bindings",
        ["tenant_id", "student_profile_id", "program_id"],
        unique=True,
        postgresql_where=sa.text("binding_state = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_students_program_bindings_one_active_program",
        table_name="app_students_program_bindings",
    )
    op.drop_index(
        "ix_students_program_bindings_one_active_primary",
        table_name="app_students_program_bindings",
    )
    op.drop_index(
        "ix_students_program_bindings_tenant_program_state",
        table_name="app_students_program_bindings",
    )
    op.drop_index(
        "ix_students_program_bindings_tenant_student_state",
        table_name="app_students_program_bindings",
    )
    op.drop_table("app_students_program_bindings")

    op.drop_index(
        "ix_students_status_history_tenant_to_status_changed_desc",
        table_name="app_students_status_history",
    )
    op.drop_index(
        "ix_students_status_history_tenant_student_changed_desc",
        table_name="app_students_status_history",
    )
    op.drop_table("app_students_status_history")

    op.drop_index("ix_students_profiles_tenant_person", table_name="app_students_profiles")
    op.drop_index("ix_students_profiles_tenant_cohort", table_name="app_students_profiles")
    op.drop_index("ix_students_profiles_tenant_status", table_name="app_students_profiles")
    op.drop_table("app_students_profiles")

    enum_types = [
        student_program_binding_state,
        student_admission_source,
        student_academic_level,
        student_status,
    ]
    for enum_type in enum_types:
        enum_type.drop(op.get_bind(), checkfirst=True)
