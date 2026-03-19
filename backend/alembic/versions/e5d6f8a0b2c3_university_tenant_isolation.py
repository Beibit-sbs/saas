"""university core tenant isolation: backfill, NOT NULL, indexes

Revision ID: e5d6f8a0b2c3
Revises: d3e5f7a9b1c2
Create Date: 2026-03-20 14:00:00.000000
"""

from alembic import op


revision = "e5d6f8a0b2c3"
down_revision = "d3e5f7a9b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Backfill tenant_id = '1' for all existing university rows
    for table in (
        "university_students",
        "university_faculty",
        "university_programs",
        "university_courses",
        "university_enrollments",
        "university_academic_records",
    ):
        op.execute(f"UPDATE {table} SET tenant_id = '1' WHERE tenant_id IS NULL")

    # 2. Make tenant_id NOT NULL in all 6 tables
    for table in (
        "university_students",
        "university_faculty",
        "university_programs",
        "university_courses",
        "university_enrollments",
        "university_academic_records",
    ):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")

    # 3. Add indexes for tenant-aware queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_univ_students_tenant ON university_students(tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_univ_faculty_tenant ON university_faculty(tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_univ_programs_tenant ON university_programs(tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_univ_courses_tenant ON university_courses(tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_univ_enrollments_tenant ON university_enrollments(tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_univ_records_tenant ON university_academic_records(tenant_id)"
    )

    # 4. Composite unique indexes for common tenant-scoped lookups
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_univ_students_tenant_sid "
        "ON university_students(tenant_id, student_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_univ_programs_tenant_code "
        "ON university_programs(tenant_id, program_code)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_univ_courses_tenant_code "
        "ON university_courses(tenant_id, course_code)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_univ_faculty_tenant_fid "
        "ON university_faculty(tenant_id, faculty_id)"
    )


def downgrade() -> None:
    for idx in (
        "idx_univ_students_tenant_sid",
        "idx_univ_programs_tenant_code",
        "idx_univ_courses_tenant_code",
        "idx_univ_faculty_tenant_fid",
        "idx_univ_students_tenant",
        "idx_univ_faculty_tenant",
        "idx_univ_programs_tenant",
        "idx_univ_courses_tenant",
        "idx_univ_enrollments_tenant",
        "idx_univ_records_tenant",
    ):
        op.execute(f"DROP INDEX IF EXISTS {idx}")

    for table in (
        "university_students",
        "university_faculty",
        "university_programs",
        "university_courses",
        "university_enrollments",
        "university_academic_records",
    ):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP NOT NULL")
