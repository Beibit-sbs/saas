"""merge ai-gateway and saas-commercial heads

Revision ID: c51043de2d5f
Revises: a7c9e1d2f3b4, c3f1a7b9d2e4
Create Date: 2026-03-22 00:29:01.469683

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'c51043de2d5f'
down_revision: Union[str, None] = ('a7c9e1d2f3b4', 'c3f1a7b9d2e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
