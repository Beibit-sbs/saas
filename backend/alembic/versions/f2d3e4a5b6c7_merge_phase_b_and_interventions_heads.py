"""merge phase b scheduling and interventions heads

Revision ID: f2d3e4a5b6c7
Revises: 1b2c3d4e5f6a, f1c2d3e4a5b6
Create Date: 2026-04-05 18:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "f2d3e4a5b6c7"
down_revision: str | Sequence[str] | None = ("1b2c3d4e5f6a", "f1c2d3e4a5b6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
