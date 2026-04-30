"""add_model_eval_runs_table

Revision ID: ne23op45qr67
Revises: mi12jk34lm56
Create Date: 2026-01-01 00:00:00.000000

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "ne23op45qr67"
down_revision = "mi12jk34lm56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_model_eval_runs (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(16) NOT NULL,
            tenant_id BIGINT NOT NULL,
            model_name TEXT NOT NULL,
            eval_set_name TEXT NOT NULL,
            metric_names JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            metrics JSONB NOT NULL DEFAULT '[]'::jsonb,
            notes TEXT,
            created_by VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            CONSTRAINT uq_model_eval_runs_run_id UNIQUE (run_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_model_eval_runs_tenant_id ON university_model_eval_runs (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_model_eval_runs_tenant_status ON university_model_eval_runs (tenant_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_model_eval_runs_eval_set ON university_model_eval_runs (tenant_id, eval_set_name)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS university_model_eval_runs CASCADE")
