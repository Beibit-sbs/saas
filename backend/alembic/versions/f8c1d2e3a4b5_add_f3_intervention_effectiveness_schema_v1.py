"""add f3 intervention effectiveness schema v1

Revision ID: f8c1d2e3a4b5
Revises: b2c4d6e8f0a1, a2b3c4d5e6f7
Create Date: 2026-04-13 12:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f8c1d2e3a4b5"
down_revision = ("b2c4d6e8f0a1", "a2b3c4d5e6f7")
branch_labels = None
depends_on = None


intervention_cohort_outcome_type = postgresql.ENUM(
    "dropout_rate",
    "gpa_improvement",
    "course_completion_rate",
    "persistence_rate",
    name="intervention_cohort_outcome_type",
    create_type=False,
)


def upgrade() -> None:
    intervention_cohort_outcome_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "app_intervention_cohorts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("playbook_id", sa.BigInteger(), nullable=False),
        sa.Column("cohort_name", sa.String(length=255), nullable=False),
        sa.Column("analysis_window_start", sa.Date(), nullable=False),
        sa.Column("analysis_window_end", sa.Date(), nullable=False),
        sa.Column("student_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("data_completeness_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["playbook_id"], ["app_playbooks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "playbook_id",
            "analysis_window_start",
            "analysis_window_end",
            name="uq_intervention_cohorts_window",
        ),
    )
    op.create_index("ix_intervention_cohorts_tenant_id", "app_intervention_cohorts", ["tenant_id"])
    op.create_index("ix_intervention_cohorts_playbook_id", "app_intervention_cohorts", ["playbook_id"])

    op.create_table(
        "app_intervention_cohort_members",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("cohort_id", sa.BigInteger(), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=True),
        sa.Column("playbook_execution_id", sa.BigInteger(), nullable=False),
        sa.Column("risk_band_at_intervention", sa.String(length=32), nullable=True),
        sa.Column("program_code", sa.String(length=64), nullable=True),
        sa.Column("segment_key", sa.String(length=128), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohort_id"], ["app_intervention_cohorts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["playbook_execution_id"], ["app_playbook_executions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cohort_id",
            "playbook_execution_id",
            name="uq_intervention_cohort_members_execution",
        ),
    )
    op.create_index("ix_intervention_cohort_members_tenant_id", "app_intervention_cohort_members", ["tenant_id"])
    op.create_index("ix_intervention_cohort_members_cohort_id", "app_intervention_cohort_members", ["cohort_id"])
    op.create_index(
        "ix_intervention_cohort_members_tenant_segment",
        "app_intervention_cohort_members",
        ["tenant_id", "segment_key"],
    )

    op.create_table(
        "app_intervention_cohort_outcomes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("cohort_id", sa.BigInteger(), nullable=False),
        sa.Column("outcome_type", intervention_cohort_outcome_type, nullable=False),
        sa.Column("segment_name", sa.String(length=128), nullable=True),
        sa.Column("outcome_value_treated", sa.Numeric(precision=7, scale=4), nullable=False),
        sa.Column("outcome_value_control", sa.Numeric(precision=7, scale=4), nullable=False),
        sa.Column("uplift_pp", sa.Numeric(precision=7, scale=3), nullable=False),
        sa.Column("uplift_confidence_p5", sa.Numeric(precision=7, scale=3), nullable=True),
        sa.Column("uplift_confidence_p95", sa.Numeric(precision=7, scale=3), nullable=True),
        sa.Column("measurement_completeness_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("measured_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohort_id"], ["app_intervention_cohorts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cohort_id",
            "outcome_type",
            "segment_name",
            name="uq_intervention_cohort_outcomes_key",
        ),
    )
    op.create_index("ix_intervention_cohort_outcomes_tenant_id", "app_intervention_cohort_outcomes", ["tenant_id"])
    op.create_index("ix_intervention_cohort_outcomes_cohort_id", "app_intervention_cohort_outcomes", ["cohort_id"])
    op.create_index(
        "ix_intervention_cohort_outcomes_type_segment",
        "app_intervention_cohort_outcomes",
        ["outcome_type", "segment_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_intervention_cohort_outcomes_type_segment", table_name="app_intervention_cohort_outcomes")
    op.drop_index("ix_intervention_cohort_outcomes_cohort_id", table_name="app_intervention_cohort_outcomes")
    op.drop_index("ix_intervention_cohort_outcomes_tenant_id", table_name="app_intervention_cohort_outcomes")
    op.drop_table("app_intervention_cohort_outcomes")

    op.drop_index("ix_intervention_cohort_members_tenant_segment", table_name="app_intervention_cohort_members")
    op.drop_index("ix_intervention_cohort_members_cohort_id", table_name="app_intervention_cohort_members")
    op.drop_index("ix_intervention_cohort_members_tenant_id", table_name="app_intervention_cohort_members")
    op.drop_table("app_intervention_cohort_members")

    op.drop_index("ix_intervention_cohorts_playbook_id", table_name="app_intervention_cohorts")
    op.drop_index("ix_intervention_cohorts_tenant_id", table_name="app_intervention_cohorts")
    op.drop_table("app_intervention_cohorts")

    intervention_cohort_outcome_type.drop(op.get_bind(), checkfirst=True)
