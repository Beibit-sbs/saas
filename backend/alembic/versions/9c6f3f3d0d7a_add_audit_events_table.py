"""add_audit_events_table

Revision ID: 9c6f3f3d0d7a
Revises: 4a1817f6bc35
Create Date: 2026-03-15 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9c6f3f3d0d7a"
down_revision: Union[str, None] = "4a1817f6bc35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_audit_events (
            event_id TEXT PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            entity TEXT NOT NULL,
            path TEXT NOT NULL,
            ip TEXT NOT NULL,
            result TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_audit_events_timestamp ON app_audit_events (timestamp DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_audit_events_actor ON app_audit_events (actor)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_app_audit_events_action ON app_audit_events (action)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_app_audit_events_action")
    op.execute("DROP INDEX IF EXISTS ix_app_audit_events_actor")
    op.execute("DROP INDEX IF EXISTS ix_app_audit_events_timestamp")
    op.execute("DROP TABLE IF EXISTS app_audit_events")