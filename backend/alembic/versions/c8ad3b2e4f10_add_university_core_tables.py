"""add university core tables

Revision ID: c8ad3b2e4f10
Revises: f2b6d4a9c8e1
Create Date: 2026-03-20 10:00:00.000000
"""

from alembic import op


revision = "c8ad3b2e4f10"
down_revision = "f2b6d4a9c8e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_students (
            id BIGSERIAL PRIMARY KEY,
            student_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            tenant_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_faculty (
            id BIGSERIAL PRIMARY KEY,
            faculty_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            tenant_id TEXT
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_programs (
            id BIGSERIAL PRIMARY KEY,
            program_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            degree_type TEXT NOT NULL,
            faculty TEXT NOT NULL,
            status TEXT NOT NULL,
            tenant_id TEXT
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_courses (
            id BIGSERIAL PRIMARY KEY,
            course_code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            credits INTEGER NOT NULL,
            program_id BIGINT NOT NULL REFERENCES university_programs(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            tenant_id TEXT
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_enrollments (
            id BIGSERIAL PRIMARY KEY,
            student_id BIGINT NOT NULL REFERENCES university_students(id) ON DELETE CASCADE,
            course_id BIGINT NOT NULL REFERENCES university_courses(id) ON DELETE CASCADE,
            semester TEXT NOT NULL,
            status TEXT NOT NULL,
            tenant_id TEXT
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_academic_records (
            id BIGSERIAL PRIMARY KEY,
            student_id BIGINT NOT NULL REFERENCES university_students(id) ON DELETE CASCADE,
            course_id BIGINT NOT NULL REFERENCES university_courses(id) ON DELETE CASCADE,
            grade TEXT NOT NULL,
            semester TEXT NOT NULL,
            status TEXT NOT NULL,
            tenant_id TEXT
        )
        """
    )

    op.execute(
        """
        INSERT INTO app_permissions (code, description)
        VALUES
            ('admin.students.read', 'Read university students in admin UI'),
            ('admin.students.write', 'Manage university students in admin UI'),
            ('admin.faculty.read', 'Read university faculty in admin UI'),
            ('admin.faculty.write', 'Manage university faculty in admin UI'),
            ('admin.programs.read', 'Read university programs in admin UI'),
            ('admin.programs.write', 'Manage university programs in admin UI'),
            ('admin.courses.read', 'Read university courses in admin UI'),
            ('admin.courses.write', 'Manage university courses in admin UI'),
            ('admin.enrollments.read', 'Read university enrollments in admin UI'),
            ('admin.enrollments.write', 'Manage university enrollments in admin UI'),
            ('admin.records.read', 'Read university academic records in admin UI'),
            ('admin.records.write', 'Manage university academic records in admin UI')
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM app_roles r
        JOIN app_permissions p ON p.code IN (
            'admin.students.read', 'admin.students.write',
            'admin.faculty.read', 'admin.faculty.write',
            'admin.programs.read', 'admin.programs.write',
            'admin.courses.read', 'admin.courses.write',
            'admin.enrollments.read', 'admin.enrollments.write',
            'admin.records.read', 'admin.records.write'
        )
        WHERE r.name IN ('superadmin', 'admin')
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO app_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM app_roles r
        JOIN app_permissions p ON p.code IN (
            'admin.students.read',
            'admin.faculty.read',
            'admin.programs.read',
            'admin.courses.read',
            'admin.enrollments.read',
            'admin.records.read'
        )
        WHERE r.name = 'auditor'
        ON CONFLICT (role_id, permission_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM app_role_permissions
        WHERE permission_id IN (
            SELECT id FROM app_permissions
            WHERE code IN (
                'admin.students.read', 'admin.students.write',
                'admin.faculty.read', 'admin.faculty.write',
                'admin.programs.read', 'admin.programs.write',
                'admin.courses.read', 'admin.courses.write',
                'admin.enrollments.read', 'admin.enrollments.write',
                'admin.records.read', 'admin.records.write'
            )
        )
        """
    )

    op.execute(
        """
        DELETE FROM app_permissions
        WHERE code IN (
            'admin.students.read', 'admin.students.write',
            'admin.faculty.read', 'admin.faculty.write',
            'admin.programs.read', 'admin.programs.write',
            'admin.courses.read', 'admin.courses.write',
            'admin.enrollments.read', 'admin.enrollments.write',
            'admin.records.read', 'admin.records.write'
        )
        """
    )

    op.execute("DROP TABLE IF EXISTS university_academic_records")
    op.execute("DROP TABLE IF EXISTS university_enrollments")
    op.execute("DROP TABLE IF EXISTS university_courses")
    op.execute("DROP TABLE IF EXISTS university_programs")
    op.execute("DROP TABLE IF EXISTS university_faculty")
    op.execute("DROP TABLE IF EXISTS university_students")
