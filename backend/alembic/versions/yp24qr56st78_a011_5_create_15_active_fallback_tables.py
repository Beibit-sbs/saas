"""A-011.5: Create 15 active fallback tables for university_core ENTITY_CONFIGS.

Revision ID: yp24qr56st78
Revises: wn02xy34za56
Create Date: 2026-05-04

Tables created (15 active, classified as ACTIVE_PRODUCTION_REQUIRED or
ACTIVE_INTERNAL_REQUIRED in A-011.4 classification report):

ACTIVE_PRODUCTION_REQUIRED (6):
  1.  currency_exchange_rates
  2.  tenant_localization_profiles
  3.  personnel_orders
  4.  portal_requests
  5.  university_syllabus_approval_actions
  6.  university_syllabus_approval_workflows

ACTIVE_INTERNAL_REQUIRED (9):
  7.  hr_contracts
  8.  university_equipment_booking_action_logs
  9.  patents
  10. university_ip_asset_action_logs
  11. university_research_ethics_action_logs
  12. university_scheduling_section_action_logs
  13. university_scheduling_section_outcomes
  14. university_syllabus_approval_outcomes
  15. university_teaching_quality_action_logs

Excluded from this migration (per A-011.4 classification):
  - 63 PLANNED_NOT_ACTIVE tables (deferred, no service usage)
  - 3 TEST_ONLY_OR_STUB tables

References: A-011 Security/Gate Debt Closure (A-011.5)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "yp24qr56st78"
down_revision = "wn02xy34za56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. currency_exchange_rates (ACTIVE_PRODUCTION_REQUIRED)
    #    Phase LX: Multi-currency support
    # ------------------------------------------------------------------
    op.create_table(
        "currency_exchange_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("base_currency", sa.String(10), nullable=False),
        sa.Column("quote_currency", sa.String(10), nullable=False),
        sa.Column("rate", sa.Numeric(20, 8), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_currency_exchange_rates_tenant_id", "currency_exchange_rates", ["tenant_id"])
    op.create_index("ix_currency_exchange_rates_base_quote", "currency_exchange_rates", ["base_currency", "quote_currency"])

    # ------------------------------------------------------------------
    # 2. tenant_localization_profiles (ACTIVE_PRODUCTION_REQUIRED)
    #    Phase LX: Multi-language / locale support
    # ------------------------------------------------------------------
    op.create_table(
        "tenant_localization_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.String(10), nullable=False),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenant_localization_profiles_tenant_id", "tenant_localization_profiles", ["tenant_id"])

    # ------------------------------------------------------------------
    # 3. personnel_orders (ACTIVE_PRODUCTION_REQUIRED)
    #    Phase XLVIII: HR Personnel Orders (canonical table name)
    # ------------------------------------------------------------------
    op.create_table(
        "personnel_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("order_type", sa.String(50), nullable=False),
        sa.Column("employee_id", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("signed_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personnel_orders_tenant_id", "personnel_orders", ["tenant_id"])
    op.create_index("ix_personnel_orders_employee_id", "personnel_orders", ["employee_id"])

    # ------------------------------------------------------------------
    # 4. portal_requests (ACTIVE_PRODUCTION_REQUIRED)
    #    Phase XLIX: Student Portal self-service requests
    # ------------------------------------------------------------------
    op.create_table(
        "portal_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.String(100), nullable=False),
        sa.Column("request_type", sa.String(100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_requests_tenant_id", "portal_requests", ["tenant_id"])
    op.create_index("ix_portal_requests_student_id", "portal_requests", ["student_id"])

    # ------------------------------------------------------------------
    # 5. university_syllabus_approval_workflows (ACTIVE_PRODUCTION_REQUIRED)
    #    Phase XXXIV.5: Syllabus lifecycle FSM
    # ------------------------------------------------------------------
    op.create_table(
        "university_syllabus_approval_workflows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("syllabus_id", sa.String(100), nullable=False),
        sa.Column("workflow_status", sa.String(50), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("total_steps", sa.Integer(), nullable=False),
        sa.Column("initiated_by", sa.String(100), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_syllabus_approval_workflows_tenant_id", "university_syllabus_approval_workflows", ["tenant_id"])
    op.create_index("ix_syllabus_approval_workflows_syllabus_id", "university_syllabus_approval_workflows", ["syllabus_id"])

    # ------------------------------------------------------------------
    # 6. university_syllabus_approval_actions (ACTIVE_PRODUCTION_REQUIRED)
    #    Phase XXXIV.5: Per-step action records within workflow
    # ------------------------------------------------------------------
    op.create_table(
        "university_syllabus_approval_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("workflow_id", sa.String(100), nullable=False),
        sa.Column("syllabus_id", sa.String(100), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(100), nullable=False),
        sa.Column("assigned_to", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("action_status", sa.String(50), nullable=False),
        sa.Column("course_code", sa.String(100), nullable=True),
        sa.Column("department_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_syllabus_approval_actions_tenant_id", "university_syllabus_approval_actions", ["tenant_id"])
    op.create_index("ix_syllabus_approval_actions_workflow_id", "university_syllabus_approval_actions", ["workflow_id"])

    # ------------------------------------------------------------------
    # 7. hr_contracts (ACTIVE_INTERNAL_REQUIRED)
    #    Phase XLVIII: HR employee contracts
    # ------------------------------------------------------------------
    op.create_table(
        "hr_contracts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("employee_id", sa.String(100), nullable=False),
        sa.Column("position", sa.String(200), nullable=False),
        sa.Column("salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("termination_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hr_contracts_tenant_id", "hr_contracts", ["tenant_id"])
    op.create_index("ix_hr_contracts_employee_id", "hr_contracts", ["employee_id"])

    # ------------------------------------------------------------------
    # 8. university_equipment_booking_action_logs (ACTIVE_INTERNAL_REQUIRED)
    #    Phase XXXIV.8: Equipment booking FSM audit log
    # ------------------------------------------------------------------
    op.create_table(
        "university_equipment_booking_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("booking_id", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("requester_id", sa.String(100), nullable=False),
        sa.Column("equipment_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_booking_action_logs_tenant_id", "university_equipment_booking_action_logs", ["tenant_id"])
    op.create_index("ix_equipment_booking_action_logs_booking_id", "university_equipment_booking_action_logs", ["booking_id"])

    # ------------------------------------------------------------------
    # 9. patents (ACTIVE_INTERNAL_REQUIRED)
    #    Phase XLV: IP / research publications module
    # ------------------------------------------------------------------
    op.create_table(
        "patents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("inventors", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patents_tenant_id", "patents", ["tenant_id"])

    # ------------------------------------------------------------------
    # 10. university_ip_asset_action_logs (ACTIVE_INTERNAL_REQUIRED)
    #     Phase XXXIV.9: IP asset FSM audit log
    # ------------------------------------------------------------------
    op.create_table(
        "university_ip_asset_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("asset_id", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("ip_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ip_asset_action_logs_tenant_id", "university_ip_asset_action_logs", ["tenant_id"])
    op.create_index("ix_ip_asset_action_logs_asset_id", "university_ip_asset_action_logs", ["asset_id"])

    # ------------------------------------------------------------------
    # 11. university_research_ethics_action_logs (ACTIVE_INTERNAL_REQUIRED)
    #     Phase XXXIV.7: Research ethics review FSM audit log
    # ------------------------------------------------------------------
    op.create_table(
        "university_research_ethics_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("review_id", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("pi_id", sa.String(100), nullable=False),
        sa.Column("review_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_ethics_action_logs_tenant_id", "university_research_ethics_action_logs", ["tenant_id"])
    op.create_index("ix_research_ethics_action_logs_review_id", "university_research_ethics_action_logs", ["review_id"])

    # ------------------------------------------------------------------
    # 12. university_scheduling_section_action_logs (ACTIVE_INTERNAL_REQUIRED)
    #     Phase XXXIV.5: Section scheduling FSM audit log
    # ------------------------------------------------------------------
    op.create_table(
        "university_scheduling_section_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("section_id", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("time_slot_id", sa.String(100), nullable=True),
        sa.Column("classroom_id", sa.String(100), nullable=True),
        sa.Column("day_of_week", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduling_section_action_logs_tenant_id", "university_scheduling_section_action_logs", ["tenant_id"])
    op.create_index("ix_scheduling_section_action_logs_section_id", "university_scheduling_section_action_logs", ["section_id"])

    # ------------------------------------------------------------------
    # 13. university_scheduling_section_outcomes (ACTIVE_INTERNAL_REQUIRED)
    #     Phase XXXIV.5: Section scheduling FSM outcome records
    # ------------------------------------------------------------------
    op.create_table(
        "university_scheduling_section_outcomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("section_id", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("source_entity_type", sa.String(100), nullable=True),
        sa.Column("source_entity_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduling_section_outcomes_tenant_id", "university_scheduling_section_outcomes", ["tenant_id"])
    op.create_index("ix_scheduling_section_outcomes_section_id", "university_scheduling_section_outcomes", ["section_id"])

    # ------------------------------------------------------------------
    # 14. university_syllabus_approval_outcomes (ACTIVE_INTERNAL_REQUIRED)
    #     Phase XXXIV.5: Final syllabus approval outcome records
    # ------------------------------------------------------------------
    op.create_table(
        "university_syllabus_approval_outcomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("syllabus_id", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(100), nullable=False),
        sa.Column("recorded_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_syllabus_approval_outcomes_tenant_id", "university_syllabus_approval_outcomes", ["tenant_id"])
    op.create_index("ix_syllabus_approval_outcomes_syllabus_id", "university_syllabus_approval_outcomes", ["syllabus_id"])

    # ------------------------------------------------------------------
    # 15. university_teaching_quality_action_logs (ACTIVE_INTERNAL_REQUIRED)
    #     Phase XXXIV.6: Teaching quality KPI FSM audit log
    # ------------------------------------------------------------------
    op.create_table(
        "university_teaching_quality_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("record_id", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("faculty_id", sa.String(100), nullable=False),
        sa.Column("course_id", sa.String(100), nullable=True),
        sa.Column("term_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teaching_quality_action_logs_tenant_id", "university_teaching_quality_action_logs", ["tenant_id"])
    op.create_index("ix_teaching_quality_action_logs_faculty_id", "university_teaching_quality_action_logs", ["faculty_id"])


def downgrade() -> None:
    # Drop all tables in reverse creation order
    op.drop_table("university_teaching_quality_action_logs")
    op.drop_table("university_syllabus_approval_outcomes")
    op.drop_table("university_scheduling_section_outcomes")
    op.drop_table("university_scheduling_section_action_logs")
    op.drop_table("university_research_ethics_action_logs")
    op.drop_table("university_ip_asset_action_logs")
    op.drop_table("patents")
    op.drop_table("university_equipment_booking_action_logs")
    op.drop_table("hr_contracts")
    op.drop_table("university_syllabus_approval_actions")
    op.drop_table("university_syllabus_approval_workflows")
    op.drop_table("portal_requests")
    op.drop_table("personnel_orders")
    op.drop_table("tenant_localization_profiles")
    op.drop_table("currency_exchange_rates")
