"""migrate domain extension tenant_id to bigint fk with indexes

Revision ID: jf67gh89ij01
Revises: ie56fg78hi90
Create Date: 2026-04-26 13:00:00.000000
"""

from __future__ import annotations

import hashlib
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "jf67gh89ij01"
down_revision: Union[str, None] = "ie56fg78hi90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DOMAIN_TABLES: tuple[str, ...] = (
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
    "app_syllabi",
    "app_syllabi_approval_workflows",
    "app_exams",
    "app_exam_sessions",
    "accreditation_records",
    "thesis_records",
)


def _name(prefix: str, table: str) -> str:
    digest = hashlib.sha1(table.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def _table_exists(table: str) -> bool:
    return (
        op.get_bind()
        .execute(sa.text("SELECT to_regclass(:regclass)"), {"regclass": f"public.{table}"})
        .scalar()
        is not None
    )


def _tenant_column_exists(table: str) -> bool:
    query = f"""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = '{table}'
          AND column_name = 'tenant_id'
        LIMIT 1
    """
    return op.get_bind().execute(sa.text(query)).scalar() is not None


def _tenant_is_text_like(table: str) -> bool:
    query = f"""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = '{table}'
          AND column_name = 'tenant_id'
          AND data_type IN ('text', 'character varying', 'character')
        LIMIT 1
    """
    return op.get_bind().execute(sa.text(query)).scalar() is not None


def _constraint_exists(name: str) -> bool:
    query = """
        SELECT 1
        FROM pg_constraint
        WHERE conname = :constraint_name
        LIMIT 1
    """
    return (
        op.get_bind()
        .execute(sa.text(query), {"constraint_name": name})
        .scalar()
        is not None
    )


def _index_exists(name: str) -> bool:
    query = """
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname = :index_name
        LIMIT 1
    """
    return op.get_bind().execute(sa.text(query), {"index_name": name}).scalar() is not None


def upgrade() -> None:
    for table in _DOMAIN_TABLES:
        if not _table_exists(table) or not _tenant_column_exists(table):
            continue

        # Normalize blank values first so the cast does not fail.
        op.execute(f"UPDATE {table} SET tenant_id = NULL WHERE tenant_id::text ~ '^\\s*$'")

        if _tenant_is_text_like(table):
            op.execute(
                f"UPDATE {table} "
                "SET tenant_id = NULL "
                "WHERE tenant_id IS NOT NULL "
                "AND tenant_id::text !~ '^[0-9]+$'"
            )
            op.execute(
                f"ALTER TABLE {table} "
                "ALTER COLUMN tenant_id TYPE BIGINT USING tenant_id::BIGINT"
            )

        fk_name = _name("fk_tenant", table)
        ix_name = _name("ix_tenant", table)
        if not _constraint_exists(fk_name):
            op.execute(
                f"ALTER TABLE {table} "
                f"ADD CONSTRAINT {fk_name} "
                "FOREIGN KEY (tenant_id) REFERENCES app_tenants(id) ON DELETE SET NULL"
            )
        if not _index_exists(ix_name):
            op.execute(
                f"CREATE INDEX IF NOT EXISTS {ix_name} ON {table} (tenant_id)"
            )


def downgrade() -> None:
    for table in _DOMAIN_TABLES:
        if not _table_exists(table) or not _tenant_column_exists(table):
            continue

        fk_name = _name("fk_tenant", table)
        ix_name = _name("ix_tenant", table)
        op.execute(f"DROP INDEX IF EXISTS {ix_name}")
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {fk_name}")
        op.execute(
            f"ALTER TABLE {table} "
            "ALTER COLUMN tenant_id TYPE TEXT USING tenant_id::TEXT"
        )
