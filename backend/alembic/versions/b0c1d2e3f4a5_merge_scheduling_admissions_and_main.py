"""merge scheduling, admissions and main heads

Revision ID: b0c1d2e3f4a5
Revises: a9b8c7d6e5f4, e8b4c2d1f7a9, e9f7a5b3c1d0
Create Date: 2026-04-04 14:00:00.000000

Merge migration to unify three branch heads:
- a9b8c7d6e5f4: main platform chain (remove legacy auth json settings)
- e8b4c2d1f7a9: university scheduling tables chain
- e9f7a5b3c1d0: admissions module tables (previously had duplicate revision ID)
"""

from __future__ import annotations

from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "b0c1d2e3f4a5"
down_revision: str | Sequence[str] | None = (
    "a9b8c7d6e5f4",
    "e8b4c2d1f7a9",
    "e9f7a5b3c1d0",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
