"""add interventions risk detection tables

Revision ID: d4c5e6f7a8b9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-06 10:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d4c5e6f7a8b9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


risk_threshold_category_enum = postgresql.ENUM(
    "attendance",
    "topic_mastery",
    "failed_assessment",
    name="risk_threshold_category",
    create_type=False,
)
risk_metric_enum = postgresql.ENUM(
    "absence_count",
    "quiz_best_score",
    name="risk_metric",
    create_type=False,
)
risk_threshold_comparison_enum = postgresql.ENUM(
    "lte",
    "gte",
    "eq",
    name="risk_threshold_comparison",
    create_type=False,
)
risk_signal_type_enum = postgresql.ENUM(
    "attendance_risk",
    "progress_risk",
    "assessment_risk",
    name="risk_signal_type",
    create_type=False,
)
outcome_tracking_status_enum = postgresql.ENUM(
    "improved",
    "unchanged",
    "worsened",
    name="outcome_tracking_status",
    create_type=False,
)


intervention_case_severity_enum = postgresql.ENUM(
    "low",
    "medium",
    "high",
    name="intervention_case_severity",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    risk_threshold_category_enum.create(bind, checkfirst=True)
    risk_metric_enum.create(bind, checkfirst=True)
    risk_threshold_comparison_enum.create(bind, checkfirst=True)
    risk_signal_type_enum.create(bind, checkfirst=True)
    outcome_tracking_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "app_risk_thresholds",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), sa.ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_category", risk_threshold_category_enum, nullable=False),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("metric", risk_metric_enum, nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("comparison", risk_threshold_comparison_enum, nullable=False),
        sa.Column("severity_level", intervention_case_severity_enum, nullable=False, server_default=sa.text("'medium'")),
        sa.Column("signal_type", risk_signal_type_enum, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("auto_create_case", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("escalate_to_refs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "id", name="ux_risk_thresholds_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "rule_name", name="ux_risk_thresholds_tenant_rule_name"),
        sa.CheckConstraint("threshold_value >= 0", name="ck_risk_thresholds_threshold_non_negative"),
        sa.CheckConstraint("window_days >= 1", name="ck_risk_thresholds_window_days_positive"),
    )
    op.create_index("ix_risk_thresholds_tenant_enabled", "app_risk_thresholds", ["tenant_id", "enabled"])
    op.create_index("ix_risk_thresholds_tenant_category", "app_risk_thresholds", ["tenant_id", "risk_category"])

    op.create_table(
        "app_risk_signals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), sa.ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("threshold_id", sa.BigInteger(), nullable=False),
        sa.Column("signal_type", risk_signal_type_enum, nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("detected_on", sa.Date(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("severity", intervention_case_severity_enum, nullable=False),
        sa.Column("signal_data_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("associated_case_id", sa.BigInteger(), nullable=True),
        sa.UniqueConstraint("tenant_id", "id", name="ux_risk_signals_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "student_profile_id",
            "threshold_id",
            "detected_on",
            name="ux_risk_signals_tenant_student_threshold_day",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "threshold_id"],
            ["app_risk_thresholds.tenant_id", "app_risk_thresholds.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "associated_case_id"],
            ["app_intervention_cases.tenant_id", "app_intervention_cases.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_risk_signals_tenant_student_detected",
        "app_risk_signals",
        ["tenant_id", "student_profile_id", "detected_at"],
    )
    op.create_index("ix_risk_signals_tenant_severity", "app_risk_signals", ["tenant_id", "severity"])

    op.create_table(
        "app_outcome_tracking",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), sa.ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("baseline_risk_score", sa.Float(), nullable=False),
        sa.Column("current_risk_score", sa.Float(), nullable=False),
        sa.Column("outcome", outcome_tracking_status_enum, nullable=False),
        sa.Column("improvement_date", sa.Date(), nullable=True),
        sa.Column("measurement_notes", sa.Text(), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tenant_id", "id", name="ux_outcome_tracking_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "case_id", name="ux_outcome_tracking_tenant_case"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["app_intervention_cases.tenant_id", "app_intervention_cases.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_outcome_tracking_tenant_outcome", "app_outcome_tracking", ["tenant_id", "outcome"])


def downgrade() -> None:
    op.drop_index("ix_outcome_tracking_tenant_outcome", table_name="app_outcome_tracking")
    op.drop_table("app_outcome_tracking")

    op.drop_index("ix_risk_signals_tenant_severity", table_name="app_risk_signals")
    op.drop_index("ix_risk_signals_tenant_student_detected", table_name="app_risk_signals")
    op.drop_table("app_risk_signals")

    op.drop_index("ix_risk_thresholds_tenant_category", table_name="app_risk_thresholds")
    op.drop_index("ix_risk_thresholds_tenant_enabled", table_name="app_risk_thresholds")
    op.drop_table("app_risk_thresholds")

    bind = op.get_bind()
    outcome_tracking_status_enum.drop(bind, checkfirst=True)
    risk_signal_type_enum.drop(bind, checkfirst=True)
    risk_threshold_comparison_enum.drop(bind, checkfirst=True)
    risk_metric_enum.drop(bind, checkfirst=True)
    risk_threshold_category_enum.drop(bind, checkfirst=True)
