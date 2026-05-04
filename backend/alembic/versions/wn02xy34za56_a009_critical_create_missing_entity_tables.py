"""A-009 CRITICAL: Create 10 missing entity tables required for operability.

Revision ID: wn02xy34za56
Revises: vm01wx23yz45
Create Date: 2026-05-04

This migration creates 10 missing entity tables identified by the
OPERABILITY AUDIT PROTOCOL (A-005) that are referenced in ENTITY_CONFIGS
but missing from the database schema:

Tables created:
  1. campus_rooms — room master data for room_booking service
  2. room_bookings — booking records
  3. university_cohort_risk_snapshots — intervention analytics
  4. university_auto_triggered_interventions — auto-triggered cases
  5-10. payment_* family (orders, transactions, failures, refunds, processing_log, failure_alerts)

Severity: CRITICAL — these tables are actively referenced in production
service code and missing tables trigger fail-closed mode in production.

References: A-009 Phase 1.3 (FIX PACK execution)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "wn02xy34za56"
down_revision = "vm01wx23yz45"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create campus_rooms table (room_booking service master data)
    # ------------------------------------------------------------------
    op.create_table(
        "campus_rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("room_code", sa.String(50), nullable=False),
        sa.Column("building_code", sa.String(50), nullable=False),
        sa.Column("room_name", sa.String(200), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("features", postgresql.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campus_rooms_tenant_id", "campus_rooms", ["tenant_id"])
    op.create_index("ix_campus_rooms_room_code", "campus_rooms", ["room_code"])

    # ------------------------------------------------------------------
    # 2. Create room_bookings table (room_booking service)
    # ------------------------------------------------------------------
    op.create_table(
        "room_bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("booking_ref", sa.String(100), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("requested_by", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_room_bookings_tenant_id", "room_bookings", ["tenant_id"])
    op.create_index("ix_room_bookings_booking_ref", "room_bookings", ["booking_ref"])

    # ------------------------------------------------------------------
    # 3. Create university_cohort_risk_snapshots table (interventions service)
    # ------------------------------------------------------------------
    op.create_table(
        "university_cohort_risk_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("cohort_id", sa.String(100), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("high_risk_count", sa.Integer(), nullable=True),
        sa.Column("medium_risk_count", sa.Integer(), nullable=True),
        sa.Column("low_risk_count", sa.Integer(), nullable=True),
        sa.Column("snapshot_data", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cohort_risk_snapshots_tenant_id", "university_cohort_risk_snapshots", ["tenant_id"])
    op.create_index("ix_cohort_risk_snapshots_cohort_id", "university_cohort_risk_snapshots", ["cohort_id"])

    # ------------------------------------------------------------------
    # 4. Create university_auto_triggered_interventions table (interventions service)
    # ------------------------------------------------------------------
    op.create_table(
        "university_auto_triggered_interventions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.String(100), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("trigger_reason", sa.String(200), nullable=True),
        sa.Column("case_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auto_triggered_interventions_tenant_id", "university_auto_triggered_interventions", ["tenant_id"])
    op.create_index("ix_auto_triggered_interventions_student_id", "university_auto_triggered_interventions", ["student_id"])

    # ------------------------------------------------------------------
    # 5. Create payment_orders table (online_payments service)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("order_ref", sa.String(100), nullable=False),
        sa.Column("student_id", sa.String(100), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_orders_tenant_id", "payment_orders", ["tenant_id"])
    op.create_index("ix_payment_orders_order_ref", "payment_orders", ["order_ref"])

    # ------------------------------------------------------------------
    # 6. Create payment_transactions table (online_payments service)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("transaction_ref", sa.String(100), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_transactions_tenant_id", "payment_transactions", ["tenant_id"])
    op.create_index("ix_payment_transactions_transaction_ref", "payment_transactions", ["transaction_ref"])

    # ------------------------------------------------------------------
    # 7. Create payment_failures table (online_payments service)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_failures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_failures_tenant_id", "payment_failures", ["tenant_id"])
    op.create_index("ix_payment_failures_transaction_id", "payment_failures", ["transaction_id"])

    # ------------------------------------------------------------------
    # 8. Create payment_refunds table (online_payments service)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("refund_ref", sa.String(100), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_refunds_tenant_id", "payment_refunds", ["tenant_id"])
    op.create_index("ix_payment_refunds_refund_ref", "payment_refunds", ["refund_ref"])

    # ------------------------------------------------------------------
    # 9. Create payment_processing_log table (payment_reconciliation service)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_processing_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("details", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_processing_log_tenant_id", "payment_processing_log", ["tenant_id"])
    op.create_index("ix_payment_processing_log_order_id", "payment_processing_log", ["order_id"])

    # ------------------------------------------------------------------
    # 10. Create payment_failure_alerts table (payment_reconciliation service)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_failure_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.String(100), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=True),
        sa.Column("alert_reason", sa.String(200), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_failure_alerts_tenant_id", "payment_failure_alerts", ["tenant_id"])
    op.create_index("ix_payment_failure_alerts_student_id", "payment_failure_alerts", ["student_id"])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table("payment_failure_alerts")
    op.drop_table("payment_processing_log")
    op.drop_table("payment_refunds")
    op.drop_table("payment_failures")
    op.drop_table("payment_transactions")
    op.drop_table("payment_orders")
    op.drop_table("university_auto_triggered_interventions")
    op.drop_table("university_cohort_risk_snapshots")
    op.drop_table("room_bookings")
    op.drop_table("campus_rooms")
