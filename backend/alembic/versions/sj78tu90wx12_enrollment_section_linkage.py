"""enrollment section linkage for concrete Enrollment -> Section relation

Revision ID: sj78tu90wx12
Revises: ri67st89uv01
Create Date: 2026-04-28 10:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "sj78tu90wx12"
down_revision = "ri67st89uv01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_enrollments_enrollments",
        sa.Column("section_id", sa.BigInteger(), nullable=True),
    )

    # Data migration: resolve section linkage when (tenant_id, course_id, term_id) maps to exactly one section.
    op.execute(
        """
        UPDATE app_enrollments_enrollments AS e
        SET section_id = resolved.section_id
        FROM (
            SELECT
                e2.tenant_id,
                e2.id AS enrollment_id,
                MIN(s.id) AS section_id
            FROM app_enrollments_enrollments AS e2
            JOIN app_scheduling_course_sections AS s
              ON s.tenant_id = e2.tenant_id
             AND s.course_id = e2.course_id
             AND s.term_id = e2.term_id
            GROUP BY e2.tenant_id, e2.id
            HAVING COUNT(s.id) = 1
        ) AS resolved
        WHERE e.tenant_id = resolved.tenant_id
          AND e.id = resolved.enrollment_id
          AND e.section_id IS NULL
        """
    )

    # Persist unresolved backfill cases for manual remediation.
    op.create_table(
        "app_enrollments_section_linkage_issues",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("enrollment_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("candidate_section_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["app_enrollments_enrollments.tenant_id", "app_enrollments_enrollments.id"],
            ondelete="CASCADE",
            name="fk_enrollments_section_issues_enrollment",
        ),
        sa.UniqueConstraint("tenant_id", "enrollment_id", name="ux_enrollment_section_issue_once"),
    )

    op.execute(
        """
        INSERT INTO app_enrollments_section_linkage_issues (tenant_id, enrollment_id, reason, candidate_section_ids)
        SELECT
            e.tenant_id,
            e.id,
            CASE
                WHEN COUNT(s.id) = 0 THEN 'no_match'
                ELSE 'ambiguous'
            END AS reason,
            CASE
                WHEN COUNT(s.id) = 0 THEN NULL
                ELSE to_jsonb(array_agg(s.id ORDER BY s.id))
            END AS candidate_section_ids
        FROM app_enrollments_enrollments AS e
        LEFT JOIN app_scheduling_course_sections AS s
          ON s.tenant_id = e.tenant_id
         AND s.course_id = e.course_id
         AND s.term_id = e.term_id
        WHERE e.section_id IS NULL
        GROUP BY e.tenant_id, e.id
        """
    )

    op.execute(
        """
        UPDATE app_enrollments_enrollments AS e
        SET metadata_json = COALESCE(e.metadata_json, '{}'::jsonb) ||
            jsonb_build_object(
                'section_linkage_status', 'invalid',
                'section_linkage_reason', i.reason
            )
        FROM app_enrollments_section_linkage_issues AS i
        WHERE i.tenant_id = e.tenant_id
          AND i.enrollment_id = e.id
          AND e.section_id IS NULL
        """
    )

    op.create_foreign_key(
        "fk_enrollments_tenant_section_id",
        "app_enrollments_enrollments",
        "app_scheduling_course_sections",
        ["tenant_id", "section_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_enrollments_tenant_section",
        "app_enrollments_enrollments",
        ["tenant_id", "section_id"],
    )

    # Enforce NOT NULL only when all rows are resolvable; unresolved legacy rows stay fail-closed.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM app_enrollments_enrollments
                WHERE section_id IS NULL
            ) THEN
                ALTER TABLE app_enrollments_enrollments
                ALTER COLUMN section_id SET NOT NULL;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE app_enrollments_enrollments
        ALTER COLUMN section_id DROP NOT NULL
        """
    )

    op.drop_index("ix_enrollments_tenant_section", table_name="app_enrollments_enrollments")
    op.drop_constraint(
        "fk_enrollments_tenant_section_id",
        "app_enrollments_enrollments",
        type_="foreignkey",
    )

    op.drop_table("app_enrollments_section_linkage_issues")
    op.drop_column("app_enrollments_enrollments", "section_id")
