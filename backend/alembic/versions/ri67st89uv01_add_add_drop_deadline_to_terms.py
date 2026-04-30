"""add add_drop_deadline to enrollment terms

Revision ID: ri67st89uv01
Revises: qh56rs78tu90
Create Date: 2026-04-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ri67st89uv01"
down_revision = "qh56rs78tu90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_enrollments_terms",
        sa.Column("add_drop_deadline", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_enrollments_terms", "add_drop_deadline")
