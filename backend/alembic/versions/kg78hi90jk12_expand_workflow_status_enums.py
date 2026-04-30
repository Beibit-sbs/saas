"""expand workflow status enums with failed and timed_out

Revision ID: kg78hi90jk12
Revises: jf67gh89ij01
Create Date: 2026-04-26 14:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "kg78hi90jk12"
down_revision: Union[str, None] = "jf67gh89ij01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE workflow_instance_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE workflow_instance_status ADD VALUE IF NOT EXISTS 'timed_out'")
    op.execute("ALTER TYPE workflow_task_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE workflow_task_status ADD VALUE IF NOT EXISTS 'timed_out'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely in-place.
    # Downgrade is intentionally a no-op to avoid destructive type recreation.
    pass
