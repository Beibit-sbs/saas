from __future__ import annotations

import os

import pytest

from app.modules.university_core import shared as university_shared
from app.modules.university_core.entity_impl import validate_entity_tables_impl

# Capture DATABASE_URL at module import time — before conftest's reset_shared_state
# autouse fixture pops it from os.environ for test isolation.
_DATABASE_URL_AT_IMPORT = os.environ.get("DATABASE_URL")

# A-011.5: 15 ACTIVE tables that have Alembic migrations (migration yp24qr56st78).
# The remaining 66 ENTITY_CONFIGS tables are PLANNED_NOT_ACTIVE (63) or TEST_ONLY (3);
# they fall back to in-memory store intentionally and are NOT asserted here.
_A011_ACTIVE_TABLES = frozenset([
    "currency_exchange_rates",
    "tenant_localization_profiles",
    "personnel_orders",
    "portal_requests",
    "university_syllabus_approval_actions",
    "university_syllabus_approval_workflows",
    "hr_contracts",
    "university_equipment_booking_action_logs",
    "patents",
    "university_ip_asset_action_logs",
    "university_research_ethics_action_logs",
    "university_scheduling_section_action_logs",
    "university_scheduling_section_outcomes",
    "university_syllabus_approval_outcomes",
    "university_teaching_quality_action_logs",
])


def test_all_entity_tables_exist() -> None:
    """Assert that the 15 ACTIVE university_core tables (migrated in A-011.5) are
    present in the database.  PLANNED_NOT_ACTIVE and TEST_ONLY entries are excluded
    because their tables are intentionally not yet migrated (in-memory fallback).
    """
    if not _DATABASE_URL_AT_IMPORT:
        pytest.skip("DATABASE_URL is not configured for DB integration checks")

    # Restore DATABASE_URL for this test only (conftest pops it for isolation).
    os.environ["DATABASE_URL"] = _DATABASE_URL_AT_IMPORT

    result = validate_entity_tables_impl()
    present = set(result.get("present", []))

    missing_active = sorted(_A011_ACTIVE_TABLES - present)
    assert missing_active == [], (
        f"A-011.5 ACTIVE tables missing from database: {', '.join(missing_active)}"
    )


def test_personnel_orders_canonical_table_name() -> None:
    """Regression: A-011.4 found a duplicate key in ENTITY_CONFIGS where
    'personnel_orders' was declared twice — first pointing to
    university_personnel_orders (line 875, shadowed) and then to
    personnel_orders (line 1223, canonical).  The canonical entry must win;
    the shadow table name must NOT appear in the runtime config.
    """
    configs = university_shared.ENTITY_CONFIGS
    assert "personnel_orders" in configs, "ENTITY_CONFIGS must contain 'personnel_orders' key"
    canonical_table = configs["personnel_orders"].table
    assert canonical_table == "personnel_orders", (
        f"ENTITY_CONFIGS['personnel_orders'].table must be 'personnel_orders', got '{canonical_table}'. "
        "Duplicate key was resolved incorrectly — check shared.py for the XXXV.1 vs XLVIII entries."
    )
    # The shadowed alias must not appear as the canonical table for any key
    table_names = {cfg.table for cfg in configs.values()}
    assert "university_personnel_orders" not in table_names, (
        "university_personnel_orders appeared as a canonical table name in ENTITY_CONFIGS. "
        "This means the XXXV.1 shadow entry at ~line 875 is no longer being overridden. "
        "Remove the outdated entry or restore the correct ordering in shared.py."
    )
