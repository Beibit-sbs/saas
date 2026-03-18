"""add ai gateway v1 registry and usage tables

Revision ID: f2b6d4a9c8e1
Revises: e4c4a8df6d21
Create Date: 2026-03-18 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f2b6d4a9c8e1"
down_revision = "e4c4a8df6d21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_ai_models (
            model_key TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            provider_model_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            priority INTEGER NOT NULL DEFAULT 100,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_ai_models_provider_enabled ON app_ai_models (provider, enabled)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_ai_usage_logs (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            actor TEXT NOT NULL,
            provider TEXT NOT NULL,
            model_key TEXT NOT NULL,
            provider_model_id TEXT NOT NULL,
            outcome TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            failure_reason TEXT,
            correlation_id TEXT
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_ai_usage_logs_timestamp ON app_ai_usage_logs (timestamp DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_app_ai_usage_logs_timestamp")
    op.execute("DROP TABLE IF EXISTS app_ai_usage_logs")

    op.execute("DROP INDEX IF EXISTS ix_app_ai_models_provider_enabled")
    op.execute("DROP TABLE IF EXISTS app_ai_models")
