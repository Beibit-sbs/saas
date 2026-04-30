"""add domain extension tables for all university_core entity configs

Revision ID: gc34de56fg78
Revises: fb23cd45ef67
Create Date: 2026-04-24 10:00:00.000000

This migration creates all tables referenced in
app.modules.university_core.shared.ENTITY_CONFIGS that were not yet present
in the database.  Each table follows the same minimal schema pattern:

    id          SERIAL PRIMARY KEY
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    tenant_id   TEXT
    <domain columns>  TEXT / NUMERIC / BOOLEAN depending on the field

All domain columns are TEXT unless the EntityConfig marks them with a
recognisable numeric/boolean name (amount, score, count, rate, days, etc.).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "gc34de56fg78"
down_revision: Union[str, None] = "fb23cd45ef67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Helper: columns that should be NUMERIC rather than TEXT
# ---------------------------------------------------------------------------
_NUMERIC_COLS = frozenset(
    {
        "amount",
        "total_amount",
        "allocated_amount",
        "spent_amount",
        "budget_limit",
        "licensing_revenue",
        "requested_amount",
        "original_value",
        "current_value",
        "depreciation_rate",
        "funding_amount",
        "total_gross",
        "total_net",
        "employee_count",
        "recipient_count",
        "recipients_count",
        "delivered_count",
        "opened_count",
        "capacity",
        "available_capacity",
        "gpa",
        "gpa_threshold",
        "current_gpa",
        "quality_score",
        "kpi_score",
        "overall_score",
        "teaching_score",
        "research_score",
        "service_score",
        "health_score",
        "risk_score",
        "wellbeing_score",
        "seat_number",
        "duration_minutes",
        "target_sla_minutes",
        "actual_minutes",
        "days_since_maintenance",
        "expected_service_interval_days",
        "daily_usage_rate",
        "lead_time_days",
        "reorder_point",
        "current_stock",
        "sla_breach_rate",
        "on_time_delivery_rate",
        "amount_due",
        "days_overdue",
        "max_credit_hours",
        "fte_ratio",
        "last_activity_days",
        "usage_value",
        "baseline_value",
    }
)

_BOOLEAN_COLS = frozenset(
    {
        "auto_reorder_enabled",
        "sla_target_met",
        "no_show",
        "conflict_flag",
        "active",
    }
)


def _col(name: str) -> sa.Column:
    if name == "tenant_id":
        return sa.Column(name, sa.Text(), nullable=True)
    if name == "id":
        return sa.Column(name, sa.Integer(), primary_key=True, autoincrement=True)
    if name in _BOOLEAN_COLS:
        return sa.Column(name, sa.Boolean(), nullable=True)
    if name in _NUMERIC_COLS:
        return sa.Column(name, sa.Numeric(), nullable=True)
    return sa.Column(name, sa.Text(), nullable=True)


def _table(name: str, *field_names: str) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        *[_col(f) for f in field_names],
    )


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Advising & student services
    # ------------------------------------------------------------------
    _table(
        "university_advising_sessions",
        "student_id", "advisor_id", "session_type", "status",
        "scheduled_at", "notes", "outcome", "tenant_id",
    )
    _table(
        "university_student_service_tickets",
        "student_id", "category", "subject", "description",
        "priority", "status", "owner_id", "channel", "resolution_notes", "tenant_id",
    )
    _table(
        "university_career_opportunities",
        "student_id", "title", "company", "opportunity_type",
        "status", "owner_id", "start_date", "notes", "tenant_id",
    )
    _table(
        "university_financial_aid_records",
        "student_id", "aid_type", "amount", "currency",
        "status", "term", "reviewer_id", "notes", "tenant_id",
    )
    _table(
        "university_housing_requests",
        "student_id", "request_type", "dormitory", "room_preference",
        "status", "manager_id", "notes", "tenant_id",
    )
    _table(
        "university_alumni_records",
        "student_id", "graduation_year", "status", "engagement_type",
        "employer", "contact_email", "notes", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Research
    # ------------------------------------------------------------------
    _table(
        "university_research_grants",
        "grant_code", "title", "pi_faculty_id", "deadline",
        "funding_amount", "status", "tenant_id",
    )
    _table(
        "university_research_publications",
        "publication_code", "title", "lead_author_id", "target_venue",
        "last_activity_days", "status", "tenant_id",
    )
    _table(
        "university_research_labs",
        "lab_code", "name", "status", "tenant_id",
    )
    _table(
        "university_research_ip_assets",
        "asset_code", "title", "status", "tenant_id",
    )
    _table(
        "university_research_experiments",
        "experiment_code", "title", "lab_code",
        "principal_investigator_id", "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Faculty performance
    # ------------------------------------------------------------------
    _table(
        "university_faculty_performance_kpis",
        "faculty_id", "name", "department_id", "kpi_period",
        "teaching_score", "research_score", "service_score", "overall_score",
        "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # HR / Payroll
    # ------------------------------------------------------------------
    _table(
        "university_hr_employees",
        "employee_code", "full_name", "department_id", "role_title",
        "status", "tenant_id",
    )
    _table(
        "university_hr_payroll_cycles",
        "cycle_code", "period_label", "total_gross", "total_net",
        "employee_count", "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Finance
    # ------------------------------------------------------------------
    _table(
        "university_delinquency_records",
        "student_id", "invoice_code", "amount_due", "days_overdue",
        "escalation_stage", "status", "tenant_id",
    )
    _table(
        "finance_budget_plans",
        "department_id", "fiscal_year", "total_amount", "currency",
        "status", "description", "tenant_id",
    )
    _table(
        "finance_budget_allocations",
        "plan_id", "category", "allocated_amount", "spent_amount",
        "currency", "notes", "tenant_id",
    )
    _table(
        "finance_expense_records",
        "cost_center_id", "category", "amount", "currency",
        "status", "description", "payroll_ref", "tenant_id",
    )
    _table(
        "finance_cost_centers",
        "name", "code", "department_id", "budget_limit",
        "currency", "active", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Facilities & Assets
    # ------------------------------------------------------------------
    _table(
        "university_facilities_work_orders",
        "order_code", "facility_code", "title", "work_type",
        "priority", "assigned_to", "status", "tenant_id",
    )
    _table(
        "university_facilities_maintenance_requests",
        "request_code", "facility_code", "issue_type", "severity",
        "notes", "status", "tenant_id",
    )
    _table(
        "university_asset_inventory_items",
        "asset_code", "name", "category", "location", "condition",
        "purchase_year", "vendor", "status", "tenant_id",
    )
    _table(
        "university_asset_depreciation_records",
        "asset_code", "depreciation_method", "original_value", "current_value",
        "depreciation_rate", "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Campus Operations
    # ------------------------------------------------------------------
    _table(
        "university_operations_facility_issues",
        "facility_code", "issue_type", "severity", "status", "tenant_id",
    )
    _table(
        "university_operations_work_orders",
        "work_order_code", "facility_code", "summary", "status", "tenant_id",
    )
    _table(
        "university_operations_cleaning_checks",
        "room_code", "scheduled_slot", "status", "tenant_id",
    )
    _table(
        "university_operations_room_readiness",
        "room_code", "building_code", "status", "tenant_id",
    )
    _table(
        "university_operations_maintenance_assets",
        "asset_code", "facility_code", "asset_type", "health_score",
        "days_since_maintenance", "expected_service_interval_days", "status", "tenant_id",
    )
    _table(
        "university_operations_utility_readings",
        "meter_code", "building_code", "utility_type", "usage_value",
        "baseline_value", "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Procurement
    # ------------------------------------------------------------------
    _table(
        "university_procurement_vendors",
        "vendor_code", "name", "category", "sla_breach_rate",
        "on_time_delivery_rate", "status", "tenant_id",
    )
    _table(
        "university_procurement_contracts",
        "contract_code", "vendor_code", "title", "risk_score",
        "sla_target_met", "status", "tenant_id",
    )
    _table(
        "university_procurement_assets",
        "asset_code", "title", "asset_category", "status", "tenant_id",
    )
    _table(
        "university_procurement_inventory_items",
        "item_code", "title", "current_stock", "reorder_point",
        "daily_usage_rate", "lead_time_days", "auto_reorder_enabled", "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Student Life
    # ------------------------------------------------------------------
    _table(
        "university_student_life_counseling_cases",
        "case_code", "student_id", "concern_type", "status", "tenant_id",
    )
    _table(
        "university_student_life_wellbeing_checkins",
        "student_id", "wellbeing_score", "status", "tenant_id",
    )
    _table(
        "university_student_life_accessibility_supports",
        "support_code", "student_id", "support_type", "status", "tenant_id",
    )
    _table(
        "university_student_life_disciplinary_cases",
        "incident_code", "student_id", "incident_type", "severity",
        "status", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Faculty quality & exam governance
    # ------------------------------------------------------------------
    _table(
        "university_teaching_quality_records",
        "faculty_id", "course_id", "term_id", "quality_score", "kpi_score",
        "improvement_plan", "notes", "tenant_id",
    )
    _table(
        "university_proctoring_records",
        "exam_id", "faculty_id", "room_id", "violation_type", "severity",
        "student_id", "notes", "status", "tenant_id",
    )
    _table(
        "university_office_hours_records",
        "faculty_id", "scheduled_at", "duration_minutes", "location",
        "status", "student_id", "notes", "no_show", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Security & Transport & Dining
    # ------------------------------------------------------------------
    _table(
        "campus_security_incidents",
        "incident_code", "facility_code", "category", "severity",
        "status", "reported_at", "description", "visitor_id",
        "access_control_event_id", "integration_source", "tenant_id",
    )
    _table(
        "campus_security_visitors",
        "visitor_name", "host_faculty_id", "visit_purpose", "status",
        "access_status", "badge_id", "check_in_at", "check_out_at",
        "access_control_event_id", "tenant_id",
    )
    _table(
        "campus_transport_routes",
        "route_code", "route_name", "status", "vehicle_type",
        "departure_time", "arrival_time", "capacity",
        "assigned_driver", "tenant_id",
    )
    _table(
        "campus_transport_bookings",
        "route_code", "student_id", "booking_status",
        "seat_number", "journey_date", "tenant_id",
    )
    _table(
        "campus_dining_menus",
        "menu_code", "facility_code", "meal_type", "date",
        "status", "capacity", "available_capacity", "tenant_id",
    )
    _table(
        "campus_dining_orders",
        "order_code", "menu_code", "facility_code", "meal_type",
        "status", "student_id", "special_request", "tenant_id",
    )
    _table(
        "campus_sla_records",
        "service_type", "facility_code", "target_sla_minutes", "actual_minutes",
        "status", "reported_at", "resolved_at", "description",
        "integration_source", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Research Ethics, IP, Equipment
    # ------------------------------------------------------------------
    _table(
        "research_ethics_reviews",
        "review_code", "project_title", "principal_investigator_id",
        "review_type", "status", "submission_date", "decision_date",
        "risk_level", "notes", "integration_source", "tenant_id",
    )
    _table(
        "ip_management_assets",
        "asset_code", "title", "inventor_ids", "ip_type",
        "status", "filing_date", "grant_date", "commercialization_status",
        "licensing_revenue", "notes", "integration_source", "tenant_id",
    )
    _table(
        "research_equipment_items",
        "equipment_code", "name", "category", "location",
        "status", "capacity", "notes", "integration_source", "tenant_id",
    )
    _table(
        "research_equipment_bookings",
        "equipment_code", "requester_id", "start_time", "end_time",
        "booking_status", "purpose", "conflict_flag",
        "integration_source", "tenant_id",
    )

    # ------------------------------------------------------------------
    # Scholarship & Communications
    # ------------------------------------------------------------------
    _table(
        "scholarship_applications",
        "application_code", "student_id", "scholarship_type",
        "status", "gpa", "requested_amount", "notes",
        "integration_source", "tenant_id",
    )
    _table(
        "scholarship_awards",
        "award_code", "student_id", "scholarship_type", "status",
        "amount", "renewal_deadline", "gpa_threshold", "current_gpa",
        "notes", "integration_source", "tenant_id",
    )
    _table(
        "communication_messages",
        "message_code", "title", "message_type", "target_audience",
        "status", "recipients_count", "delivered_count", "opened_count",
        "integration_source", "tenant_id",
    )


def downgrade() -> None:
    tables = [
        "communication_messages",
        "scholarship_awards",
        "scholarship_applications",
        "research_equipment_bookings",
        "research_equipment_items",
        "ip_management_assets",
        "research_ethics_reviews",
        "campus_sla_records",
        "campus_dining_orders",
        "campus_dining_menus",
        "campus_transport_bookings",
        "campus_transport_routes",
        "campus_security_visitors",
        "campus_security_incidents",
        "university_office_hours_records",
        "university_proctoring_records",
        "university_teaching_quality_records",
        "university_student_life_disciplinary_cases",
        "university_student_life_accessibility_supports",
        "university_student_life_wellbeing_checkins",
        "university_student_life_counseling_cases",
        "university_procurement_inventory_items",
        "university_procurement_assets",
        "university_procurement_contracts",
        "university_procurement_vendors",
        "university_operations_utility_readings",
        "university_operations_maintenance_assets",
        "university_operations_room_readiness",
        "university_operations_cleaning_checks",
        "university_operations_work_orders",
        "university_operations_facility_issues",
        "university_asset_depreciation_records",
        "university_asset_inventory_items",
        "university_facilities_maintenance_requests",
        "university_facilities_work_orders",
        "finance_cost_centers",
        "finance_expense_records",
        "finance_budget_allocations",
        "finance_budget_plans",
        "university_delinquency_records",
        "university_hr_payroll_cycles",
        "university_hr_employees",
        "university_faculty_performance_kpis",
        "university_research_experiments",
        "university_research_ip_assets",
        "university_research_labs",
        "university_research_publications",
        "university_research_grants",
        "university_alumni_records",
        "university_housing_requests",
        "university_financial_aid_records",
        "university_career_opportunities",
        "university_student_service_tickets",
        "university_advising_sessions",
    ]
    for t in tables:
        op.drop_table(t)
