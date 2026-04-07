"""merge identity and platform heads

Revision ID: f0e1d2c3b4a5
Revises: b3c5d7e9f1a2, e1f2a3b4c5d6
Create Date: 2026-03-28 01:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "f0e1d2c3b4a5"
down_revision: str | Sequence[str] | None = ("b3c5d7e9f1a2", "e1f2a3b4c5d6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
