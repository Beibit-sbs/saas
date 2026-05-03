"""Add 7-year audit log retention policy.

Revision ID: vm01wx23yz45
Revises: ul90vw12xy34
Create Date: 2026-05-01

This migration implements PDPL-SA / GCC-SEC-003 requirement for
7-year (2,555 days) minimum retention of all audit events.

Changes:
  1. Adds 'retention_years' comment to app_audit_events table.
  2. Creates the pg_cron extension (if available) and schedules a nightly
     purge job that removes rows older than 7 years.  Falls back gracefully
     when pg_cron is not installed (cloud-managed Postgres without the
     extension — the comment still serves as policy evidence).
  3. Creates a helper function audit_enforce_7y_retention() that can be
     called manually or by a scheduled job.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "vm01wx23yz45"
down_revision = "ul90vw12xy34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Annotate the audit table with the retention policy
    # ------------------------------------------------------------------
    op.execute(
        """
        COMMENT ON TABLE app_audit_events IS
            'PDPL-SA / GCC-SEC-003: minimum 7-year (2555 day) retention required.
             Rows must NOT be deleted before retention_expires_at.
             Managed by audit_enforce_7y_retention() / pg_cron job.';
        """
    )

    # ------------------------------------------------------------------
    # 2. Add retention_expires_at materialized column and keep it synced
    #    via trigger. Generated columns cannot use timestamptz arithmetic
    #    because PostgreSQL marks that expression as non-immutable.
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE app_audit_events
            ADD COLUMN IF NOT EXISTS retention_expires_at TIMESTAMPTZ
            ;

        UPDATE app_audit_events
        SET retention_expires_at = ("timestamp" + INTERVAL '7 years')
        WHERE retention_expires_at IS NULL;

        CREATE OR REPLACE FUNCTION app_audit_events_set_retention_expires_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.retention_expires_at := NEW."timestamp" + INTERVAL '7 years';
            RETURN NEW;
        END;
        $$;

        DROP TRIGGER IF EXISTS trg_app_audit_events_set_retention_expires_at
            ON app_audit_events;

        CREATE TRIGGER trg_app_audit_events_set_retention_expires_at
        BEFORE INSERT OR UPDATE OF "timestamp"
        ON app_audit_events
        FOR EACH ROW
        EXECUTE FUNCTION app_audit_events_set_retention_expires_at();
        """
    )

    # ------------------------------------------------------------------
    # 3. Index on retention_expires_at for efficient purge queries
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_retention_expires_at
            ON app_audit_events (retention_expires_at);
        """
    )

    # ------------------------------------------------------------------
    # 4. Create the enforcement function
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_enforce_7y_retention()
        RETURNS TABLE(deleted_count BIGINT, purge_before TIMESTAMPTZ)
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            v_purge_before TIMESTAMPTZ;
            v_deleted      BIGINT;
        BEGIN
            -- Only remove rows whose retention window has fully expired
            v_purge_before := NOW() - INTERVAL '7 years';

            WITH deleted AS (
                DELETE FROM app_audit_events
                WHERE "timestamp" < v_purge_before
                RETURNING 1
            )
            SELECT COUNT(*) INTO v_deleted FROM deleted;

            RETURN QUERY SELECT v_deleted, v_purge_before;
        END;
        $$;

        COMMENT ON FUNCTION audit_enforce_7y_retention() IS
            'PDPL-SA compliance: purges audit events older than 7 years.
             Safe to call multiple times. Returns (deleted_count, purge_before).';
        """
    )

    # ------------------------------------------------------------------
    # 5. Schedule via pg_cron if the extension is available
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_available_extensions WHERE name = 'pg_cron'
            ) THEN
                CREATE EXTENSION IF NOT EXISTS pg_cron;

                -- Remove any existing duplicate job first
                PERFORM cron.unschedule(jobid)
                FROM cron.job
                WHERE jobname = 'audit-7y-retention-purge';

                -- Schedule nightly at 02:00 UTC
                PERFORM cron.schedule(
                    'audit-7y-retention-purge',
                    '0 2 * * *',
                    'SELECT * FROM audit_enforce_7y_retention()'
                );
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_app_audit_events_set_retention_expires_at
            ON app_audit_events;
        DROP FUNCTION IF EXISTS app_audit_events_set_retention_expires_at();
        """
    )

    # Remove cron job if pg_cron is available
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
                PERFORM cron.unschedule(jobid)
                FROM cron.job
                WHERE jobname = 'audit-7y-retention-purge';
            END IF;
        END
        $$;
        """
    )
    op.execute("DROP FUNCTION IF EXISTS audit_enforce_7y_retention();")
    op.execute(
        "DROP INDEX IF EXISTS ix_audit_events_retention_expires_at;"
    )
    op.execute(
        "ALTER TABLE app_audit_events DROP COLUMN IF EXISTS retention_expires_at;"
    )
    op.execute("COMMENT ON TABLE app_audit_events IS NULL;")
