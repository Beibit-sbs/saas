"""add termination_reason column to university_faculty_contracts

Revision ID: ul90vw12xy34
Revises: tk89uv01wx23
Create Date: 2026-04-28 10:00:00.000000

Adds the missing termination_reason text column that is present in
ENTITY_CONFIGS["faculty_contracts"] fields list but was absent from
the physical table, causing SELECT queries to raise ProgrammingError
and silently fall back to the in-memory store.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "ul90vw12xy34"
down_revision = "tk89uv01wx23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE university_faculty_contracts "
        "ADD COLUMN IF NOT EXISTS termination_reason TEXT"
    )


def downgrade() -> None:
    op.drop_column("university_faculty_contracts", "termination_reason")
