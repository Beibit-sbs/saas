"""add_jobs_table

Revision ID: b2c7d1e4f9a8
Revises: a1d4e9c7b2f6
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c7d1e4f9a8"
down_revision: Union[str, None] = "a1d4e9c7b2f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_jobs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), sa.ForeignKey("app_tenants.id"), nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_app_jobs_tenant_status_created",
        "app_jobs",
        ["tenant_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_app_jobs_status_created",
        "app_jobs",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_app_jobs_status_created", table_name="app_jobs")
    op.drop_index("ix_app_jobs_tenant_status_created", table_name="app_jobs")
    op.drop_table("app_jobs")
