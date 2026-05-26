from __future__ import annotations

from pathlib import Path

from app.modules.finance_procurement_asset import models, permissions


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "fpa40a2rt01_a0402_finance_procurement_asset_tables.py"


EXPECTED_TABLES = {
    "fpa_readiness_profiles",
    "fpa_dashboard_snapshots",
    "fpa_billing_visibility_records",
    "fpa_receivables_metadata",
    "fpa_budget_plan_metadata",
    "fpa_budget_control_records",
    "fpa_procurement_request_metadata",
    "fpa_procurement_review_records",
    "fpa_vendor_metadata",
    "fpa_contract_evidence",
    "fpa_purchase_request_metadata",
    "fpa_purchase_order_metadata",
    "fpa_asset_visibility_records",
    "fpa_asset_lifecycle_records",
    "fpa_inventory_movement_metadata",
    "fpa_payment_readiness_profiles",
    "fpa_erp_readiness_profiles",
    "fpa_bank_readiness_profiles",
    "fpa_payment_gateway_readiness_profiles",
    "fpa_provider_readiness_evidence",
    "fpa_finance_bridge_records",
    "fpa_audit_events",
    "fpa_evidence_items",
    "fpa_limitations",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "finance_procurement_asset"
    assert models.API_PREFIX == "/api/admin/finance-procurement-asset"
    assert models.RUNTIME_MODE == "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY"
    assert models.EXPECTED_TABLE_COUNT == 24
    assert models.EXPECTED_ROUTE_COUNT == 53
    assert models.EXPECTED_PERMISSION_COUNT == 48
    assert models.TABLE_PREFIX == "fpa_"


def test_metadata_contains_expected_24_tables() -> None:
    fpa_tables = {name for name in models.Base.metadata.tables if name.startswith("fpa_")}
    assert fpa_tables == EXPECTED_TABLES
    assert models.TABLE_NAMES == EXPECTED_TABLES


def test_permissions_cover_runtime_slice() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 48
    assert permissions.BILLING_EVIDENCE in permissions.ALL_PERMISSIONS
    assert permissions.PROVIDER_READINESS_EVIDENCE in permissions.ALL_PERMISSIONS
    assert permissions.BRIDGES_PROVIDER_READINESS_READ in permissions.ALL_PERMISSIONS


def test_migration_contains_all_foundation_tables() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text
    assert 'revision = "fpa40a2rt01"' in text
    assert 'down_revision = "hr39a2rt01"' in text


def test_migration_create_and_drop_counts_match_24() -> None:
    text = MIGRATION_FILE.read_text()
    assert text.count('op.create_table("fpa_') == 24
    assert text.count('op.drop_table("fpa_') == 24


def test_no_forbidden_table_names_are_present() -> None:
    table_text = "\n".join(sorted(EXPECTED_TABLES))
    for forbidden in ["payment_execution", "bank_transaction", "erp_sync", "auto_approval", "hidden_score"]:
        assert forbidden not in table_text