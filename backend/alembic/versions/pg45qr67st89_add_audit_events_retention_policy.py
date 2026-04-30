"""add audit events retention policy and cleanup function

Revision ID: pg45qr67st89
Revises: of34pq56rs78
Create Date: 2026-04-26

Policy: app_audit_events rows older than 90 days are eligible for deletion.
A PostgreSQL function cleanup_old_audit_events(cutoff_days INT DEFAULT 90) is
created to perform the deletion on demand.  Schedule this function periodically
(e.g. via pg_cron or the platform jobs scheduler) to enforce the policy.
"""

from __future__ import annotations

from alembic import op

revision = "pg45qr67st89"
down_revision = "of34pq56rs78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add index to support efficient time-range queries and cleanup
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_app_audit_events_created_at
        ON app_audit_events ("timestamp");
        """
    )

    # Create cleanup function — call periodically to enforce 90-day retention
    op.execute(
        """
        CREATE OR REPLACE FUNCTION cleanup_old_audit_events(cutoff_days INT DEFAULT 90)
        RETURNS INT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            deleted_count INT;
        BEGIN
            DELETE FROM app_audit_events
            WHERE "timestamp" < NOW() - (cutoff_days || ' days')::INTERVAL;
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_audit_events(INT);")
    op.execute("DROP INDEX IF EXISTS ix_app_audit_events_created_at;")
