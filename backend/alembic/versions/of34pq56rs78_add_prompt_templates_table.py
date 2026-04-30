"""add_prompt_templates_table

Revision ID: of34pq56rs78
Revises: ne23op45qr67
Create Date: 2026-01-01 00:00:00.000000

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "of34pq56rs78"
down_revision = "ne23op45qr67"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS university_prompt_templates (
            id SERIAL PRIMARY KEY,
            template_id VARCHAR(16) NOT NULL,
            tenant_id BIGINT NOT NULL,
            name VARCHAR(256) NOT NULL,
            description TEXT,
            template_text TEXT NOT NULL,
            variables JSONB NOT NULL DEFAULT '[]'::jsonb,
            category VARCHAR(64) NOT NULL DEFAULT 'general',
            version INT NOT NULL DEFAULT 1,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_by VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_prompt_templates_id UNIQUE (template_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_prompt_templates_tenant "
        "ON university_prompt_templates (tenant_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS university_prompt_templates")
