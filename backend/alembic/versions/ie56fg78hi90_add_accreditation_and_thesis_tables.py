"""add accreditation_records and thesis_records tables

Revision ID: ie56fg78hi90
Revises: hd45ef67gh89
Create Date: 2026-04-25 00:00:00.000000
"""

from alembic import op


revision: str = "ie56fg78hi90"
down_revision: str = "hd45ef67gh89"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS accreditation_records (
            id BIGSERIAL PRIMARY KEY,
            standard_code TEXT NOT NULL,
            standard_type TEXT NOT NULL,
            title TEXT NOT NULL,
            owner_department TEXT NOT NULL,
            review_cycle_year INTEGER NOT NULL,
            due_date TEXT,
            evidence_summary TEXT,
            risk_level TEXT NOT NULL,
            status TEXT NOT NULL,
            reviewer_notes TEXT,
            remediation_plan TEXT,
            tenant_id TEXT
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_accreditation_records_tenant_id ON accreditation_records (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_accreditation_records_status ON accreditation_records (status)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS thesis_records (
            id BIGSERIAL PRIMARY KEY,
            thesis_code TEXT NOT NULL,
            student_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            advisor_faculty_id BIGINT,
            status TEXT NOT NULL,
            defense_date TEXT,
            repository_url TEXT,
            tenant_id TEXT
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_thesis_records_tenant_id ON thesis_records (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_thesis_records_student_id ON thesis_records (student_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_thesis_records_status ON thesis_records (status)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS thesis_records")
    op.execute("DROP TABLE IF EXISTS accreditation_records")
