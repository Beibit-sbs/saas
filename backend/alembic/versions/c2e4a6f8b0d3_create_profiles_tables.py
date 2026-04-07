"""Create profiles module tables.

Revision ID: c2e4a6f8b0d3
Revises: 7c2e9a4b1d0f
Create Date: 2026-03-23 06:00:00.000000

Creates:
  - app_profiles_people
  - app_profiles_departments
  - app_profiles_programs
  - app_profiles_students
  - app_profiles_faculty
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c2e4a6f8b0d3'
down_revision: Union[str, None] = '7c2e9a4b1d0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_profiles_people",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("last_name", sa.String(128), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("external_person_key", sa.String(128), nullable=True),
        sa.Column("status", sa.String(64), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_profiles_people_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "email", name="ux_profiles_people_tenant_email"),
    )
    op.create_index("ix_profiles_people_tenant_email", "app_profiles_people", ["tenant_id", "email"])
    op.create_index("ix_profiles_people_tenant_status", "app_profiles_people", ["tenant_id", "status"])
    op.create_index(
        "ux_profiles_people_tenant_external_person_key",
        "app_profiles_people",
        ["tenant_id", "external_person_key"],
        unique=True,
        postgresql_where=sa.text("external_person_key IS NOT NULL"),
    )

    op.create_table(
        "app_profiles_departments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_department_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(64), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "parent_department_id"],
            ["app_profiles_departments.tenant_id", "app_profiles_departments.id"],
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_profiles_departments_parent",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_profiles_departments_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "code", name="ux_profiles_departments_tenant_code"),
    )
    op.create_index("ix_profiles_departments_tenant_name", "app_profiles_departments", ["tenant_id", "name"])
    op.create_index("ix_profiles_departments_tenant_parent", "app_profiles_departments", ["tenant_id", "parent_department_id"])
    op.create_index("ix_profiles_departments_tenant_status", "app_profiles_departments", ["tenant_id", "status"])

    op.create_table(
        "app_profiles_programs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("department_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("degree_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["app_profiles_departments.tenant_id", "app_profiles_departments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_profiles_programs_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "code", name="ux_profiles_programs_tenant_code"),
    )
    op.create_index("ix_profiles_programs_tenant_department", "app_profiles_programs", ["tenant_id", "department_id"])
    op.create_index("ix_profiles_programs_tenant_degree_type", "app_profiles_programs", ["tenant_id", "degree_type"])
    op.create_index("ix_profiles_programs_tenant_status", "app_profiles_programs", ["tenant_id", "status"])

    op.create_table(
        "app_profiles_students",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("program_id", sa.BigInteger(), nullable=False),
        sa.Column("student_number", sa.String(64), nullable=False),
        sa.Column("cohort_year", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["app_profiles_programs.tenant_id", "app_profiles_programs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_profiles_students_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "person_id", name="ux_profiles_students_tenant_person"),
        sa.UniqueConstraint("tenant_id", "student_number", name="ux_profiles_students_tenant_student_number"),
    )
    op.create_index("ix_profiles_students_tenant_program", "app_profiles_students", ["tenant_id", "program_id"])
    op.create_index("ix_profiles_students_tenant_status", "app_profiles_students", ["tenant_id", "status"])
    op.create_index("ix_profiles_students_tenant_cohort", "app_profiles_students", ["tenant_id", "cohort_year"])

    op.create_table(
        "app_profiles_faculty",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("department_id", sa.BigInteger(), nullable=False),
        sa.Column("faculty_number", sa.String(64), nullable=False),
        sa.Column("academic_title", sa.String(128), nullable=True),
        sa.Column("status", sa.String(64), nullable=False, server_default=sa.text("'active'")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["app_profiles_people.tenant_id", "app_profiles_people.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "department_id"],
            ["app_profiles_departments.tenant_id", "app_profiles_departments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_profiles_faculty_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "person_id", name="ux_profiles_faculty_tenant_person"),
        sa.UniqueConstraint("tenant_id", "faculty_number", name="ux_profiles_faculty_tenant_faculty_number"),
    )
    op.create_index("ix_profiles_faculty_tenant_department", "app_profiles_faculty", ["tenant_id", "department_id"])
    op.create_index("ix_profiles_faculty_tenant_status", "app_profiles_faculty", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("app_profiles_faculty")
    op.drop_table("app_profiles_students")
    op.drop_table("app_profiles_programs")
    op.drop_table("app_profiles_departments")
    op.drop_table("app_profiles_people")
