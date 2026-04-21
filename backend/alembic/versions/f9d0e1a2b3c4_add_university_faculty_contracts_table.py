"""add university faculty contracts table

Revision ID: f9d0e1a2b3c4
Revises: f8c1d2e3a4b5
Create Date: 2026-04-21 06:05:00.000000
"""

from alembic import op


revision = "f9d0e1a2b3c4"
down_revision = "f8c1d2e3a4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_faculty_contracts (
            id BIGSERIAL PRIMARY KEY,
            faculty_id TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            fte_ratio TEXT NOT NULL,
            max_credit_hours TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            tenant_id TEXT NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_univ_faculty_contracts_tenant
        ON university_faculty_contracts(tenant_id)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_univ_faculty_contracts_tenant_faculty
        ON university_faculty_contracts(tenant_id, faculty_id)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_univ_faculty_contracts_tenant_status
        ON university_faculty_contracts(tenant_id, status)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_univ_faculty_contracts_tenant_status")
    op.execute("DROP INDEX IF EXISTS idx_univ_faculty_contracts_tenant_faculty")
    op.execute("DROP INDEX IF EXISTS idx_univ_faculty_contracts_tenant")
    op.execute("DROP TABLE IF EXISTS university_faculty_contracts")
