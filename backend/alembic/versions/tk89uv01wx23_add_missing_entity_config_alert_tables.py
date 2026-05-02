"""add missing entity_config alert and record tables

Revision ID: tk89uv01wx23
Revises: sj78tu90wx12
Create Date: 2026-04-28 09:00:00.000000

Creates the 52 tables referenced in ENTITY_CONFIGS that were not yet
present in the database after applying all prior migrations.
All tables follow the minimal pattern used throughout university_core:
    id          SERIAL PRIMARY KEY
    tenant_id   BIGINT
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tk89uv01wx23"
down_revision: Union[str, None] = "sj78tu90wx12"
branch_labels = None
depends_on = None

_SIMPLE_TABLES = [
    "campus_dining_capacity_alert_records",
    "campus_security_incident_escalation_records",
    "campus_transport_disruption_records",
    "finance_budget_overrun_alerts",
    "finance_expense_budget_exceeded_alerts",
    "finance_expense_policy_review_records",
    "ip_management_licensing_records",
    "research_ethics_alert_records",
    "university_academic_integrity_cases",
    "university_academic_integrity_escalation_alerts",
    "university_academic_withdrawal_alerts",
    "university_accreditation_risk_alerts",
    "university_advising_no_show_risk_alerts",
    "university_advising_support_alerts",
    "university_alumni_disengagement_risk_alerts",
    "university_alumni_engagement_events",
    "university_asset_condemned_risk_alerts",
    "university_asset_writeoff_records",
    "university_campus_sla_breach_risk_alerts",
    "university_career_placement_records",
    "university_career_stalled_opportunity_alerts",
    "university_collections_agent_records",
    "university_communication_broadcast_audits",
    "university_communication_broadcast_risk_alerts",
    "university_course_retirement_alerts",
    "university_delinquency_legal_escalation_alerts",
    "university_equipment_booking_overdue_alerts",
    "university_exam_proctoring_alerts",
    "university_facilities_overdue_work_order_alerts",
    "university_facilities_sla_assignment_records",
    "university_faculty_contract_termination_alerts",
    "university_faculty_kpi_low_performance_alerts",
    "university_financial_aid_disbursement_risk_alerts",
    "university_financial_aid_disbursements",
    "university_financial_aid_disbursement_watches",
    "university_housing_maintenance_risk_alerts",
    "university_hr_offboarding_alerts",
    "university_hr_payroll_cycle_risk_alerts",
    "university_operations_dispatch_records",
    "university_procurement_risk_alerts",
    "university_program_sunset_alerts",
    "university_publication_review_records",
    "university_research_grant_delay_alerts",
    "university_room_assignment_records",
    "university_scholarship_revocation_alerts",
    "university_student_life_alert_records",
    "university_student_life_disciplinary_escalation_alerts",
    "university_student_service_sla_alerts",
    "university_student_service_unresolved_alerts",
    "university_syllabus_review_backlogs",
    "university_thesis_overdue_alerts",
    "university_thesis_rejection_risk_alerts",
]


def upgrade() -> None:
    for table_name in _SIMPLE_TABLES:
        op.create_table(
            table_name,
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.BigInteger(), nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.Column("payload", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    for table_name in reversed(_SIMPLE_TABLES):
        op.drop_table(table_name)
