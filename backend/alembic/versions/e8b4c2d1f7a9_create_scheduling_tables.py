"""create scheduling tables

Revision ID: e8b4c2d1f7a9
Revises: de45fg67hi89
Create Date: 2026-03-24 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e8b4c2d1f7a9"
down_revision = "de45fg67hi89"
branch_labels = None
depends_on = None


def upgrade() -> None:
    day_of_week_enum = postgresql.ENUM(
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        name="scheduling_day_of_week",
        create_type=False,
    )
    room_type_enum = postgresql.ENUM("lecture", "lab", "seminar", name="scheduling_room_type", create_type=False)
    section_status_enum = postgresql.ENUM("planned", "scheduled", "cancelled", name="scheduling_section_status", create_type=False)
    instructor_role_enum = postgresql.ENUM("primary", "assistant", name="scheduling_instructor_role", create_type=False)

    bind = op.get_bind()
    day_of_week_enum.create(bind, checkfirst=True)
    room_type_enum.create(bind, checkfirst=True)
    section_status_enum.create(bind, checkfirst=True)
    instructor_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "app_scheduling_time_slots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("day_of_week", day_of_week_enum, nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("end_time > start_time", name="ck_scheduling_time_slots_end_after_start"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_time_slots_tenant_id_id"),
    )
    op.create_index(
        "ix_scheduling_time_slots_tenant_day_active",
        "app_scheduling_time_slots",
        ["tenant_id", "day_of_week", "is_active"],
    )

    op.create_table(
        "app_scheduling_classrooms",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("building", sa.String(length=128), nullable=True),
        sa.Column("capacity", sa.BigInteger(), nullable=False),
        sa.Column("room_type", room_type_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("capacity >= 0", name="ck_scheduling_classrooms_capacity_non_negative"),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_classrooms_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_classrooms_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "name", name="ux_scheduling_classrooms_tenant_name"),
    )
    op.create_index(
        "ix_scheduling_classrooms_tenant_active",
        "app_scheduling_classrooms",
        ["tenant_id", "is_active"],
    )

    op.create_table(
        "app_scheduling_course_sections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("term_id", sa.BigInteger(), nullable=False),
        sa.Column("section_code", sa.String(length=32), nullable=False),
        sa.Column("instructor_id", sa.String(length=255), nullable=True),
        sa.Column("max_capacity", sa.BigInteger(), nullable=False),
        sa.Column("status", section_status_enum, nullable=False, server_default=sa.text("'planned'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("max_capacity >= 0", name="ck_scheduling_sections_capacity_non_negative"),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_sections_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["app_enrollments_terms.tenant_id", "app_enrollments_terms.id"],
            ondelete="RESTRICT",
            name="fk_scheduling_sections_term",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_sections_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "course_id",
            "term_id",
            "section_code",
            name="ux_scheduling_sections_course_term_code",
        ),
    )
    op.create_index(
        "ix_scheduling_sections_tenant_term_status",
        "app_scheduling_course_sections",
        ["tenant_id", "term_id", "status"],
    )
    op.create_index(
        "ix_scheduling_sections_tenant_course",
        "app_scheduling_course_sections",
        ["tenant_id", "course_id"],
    )

    op.create_table(
        "app_scheduling_section_schedules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("time_slot_id", sa.BigInteger(), nullable=False),
        sa.Column("classroom_id", sa.BigInteger(), nullable=False),
        sa.Column("day_of_week", day_of_week_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("version", sa.BigInteger(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint("version >= 1", name="ck_scheduling_section_schedules_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["app_scheduling_course_sections.tenant_id", "app_scheduling_course_sections.id"],
            ondelete="CASCADE",
            name="fk_scheduling_section_schedules_section",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "time_slot_id"],
            ["app_scheduling_time_slots.tenant_id", "app_scheduling_time_slots.id"],
            ondelete="RESTRICT",
            name="fk_scheduling_section_schedules_time_slot",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "classroom_id"],
            ["app_scheduling_classrooms.tenant_id", "app_scheduling_classrooms.id"],
            ondelete="RESTRICT",
            name="fk_scheduling_section_schedules_classroom",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_section_schedules_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "classroom_id",
            "time_slot_id",
            "day_of_week",
            name="ux_scheduling_room_slot_day",
        ),
        sa.UniqueConstraint("tenant_id", "section_id", name="ux_scheduling_one_schedule_per_section"),
    )
    op.create_index(
        "ix_scheduling_section_schedules_tenant_day_slot",
        "app_scheduling_section_schedules",
        ["tenant_id", "day_of_week", "time_slot_id"],
    )

    op.create_table(
        "app_scheduling_instructor_assignments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("instructor_id", sa.String(length=255), nullable=False),
        sa.Column("role", instructor_role_enum, nullable=False, server_default=sa.text("'primary'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["app_scheduling_course_sections.tenant_id", "app_scheduling_course_sections.id"],
            ondelete="CASCADE",
            name="fk_scheduling_instructor_assignments_section",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_scheduling_instructor_assignments_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "section_id",
            "instructor_id",
            name="ux_scheduling_instructor_assignment_unique",
        ),
    )
    op.create_index(
        "ix_scheduling_instructor_assignments_tenant_instructor",
        "app_scheduling_instructor_assignments",
        ["tenant_id", "instructor_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scheduling_instructor_assignments_tenant_instructor",
        table_name="app_scheduling_instructor_assignments",
    )
    op.drop_table("app_scheduling_instructor_assignments")

    op.drop_index("ix_scheduling_section_schedules_tenant_day_slot", table_name="app_scheduling_section_schedules")
    op.drop_table("app_scheduling_section_schedules")

    op.drop_index("ix_scheduling_sections_tenant_course", table_name="app_scheduling_course_sections")
    op.drop_index("ix_scheduling_sections_tenant_term_status", table_name="app_scheduling_course_sections")
    op.drop_table("app_scheduling_course_sections")

    op.drop_index("ix_scheduling_classrooms_tenant_active", table_name="app_scheduling_classrooms")
    op.drop_table("app_scheduling_classrooms")

    op.drop_index("ix_scheduling_time_slots_tenant_day_active", table_name="app_scheduling_time_slots")
    op.drop_table("app_scheduling_time_slots")

    bind = op.get_bind()
    postgresql.ENUM(name="scheduling_instructor_role").drop(bind, checkfirst=True)
    postgresql.ENUM(name="scheduling_section_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="scheduling_room_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="scheduling_day_of_week").drop(bind, checkfirst=True)
