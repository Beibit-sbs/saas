"""W148 — asset_inventory: Deep Domain Test Pack.

HARDENING RULES APPLIED (from SBS UB FULL SYSTEM HARDENING.md):
- Tests prove behaviour, NOT structure
- validate BEFORE persist
- fail-closed on lookup failures
- cross-entity guard: depreciation × asset_inventory_items

Guards tested:
- W114: create_depreciation_record blocked if asset status == decommissioned
- W114: create_depreciation_record blocked if asset condition == condemned
- W114: blocked if asset not found (fail-closed)
- W114: blocked if lookup fails (fail-closed)
- W56: create_asset_item condemned cap per category
- Method cap: _METHOD_MAX_ACTIVE_DEPR
- Tenant isolation
- Router _svc pattern
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

import app.modules.asset_inventory.service as svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.asset_inventory.schemas import (
    AssetItemCreateSchema,
    DepreciationRecordCreateSchema,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_asset(
    asset_code: str = "ASSET-001",
    status: str = "active",
    condition: str = "good",
    category: str = "it_hardware",
    asset_id: int = 1,
) -> dict:
    return {
        "id": asset_id,
        "asset_code": asset_code,
        "name": "Test Asset",
        "category": category,
        "location": "Building A",
        "condition": condition,
        "purchase_year": 2020,
        "vendor": "Vendor X",
        "status": status,
    }


def _make_depreciation_payload(**overrides) -> DepreciationRecordCreateSchema:
    defaults = {
        "record_code": "DEP-001",
        "asset_code": "ASSET-001",
        "depreciation_method": "straight_line",
        "period_start": "2026-01-01",
        "period_end": "2026-12-31",
        "depreciation_amount": 1000.0,
        "original_value": 10000.0,
        "current_value": 9000.0,
        "depreciation_rate": 0.1,
        "status": "active",
    }
    defaults.update(overrides)
    return DepreciationRecordCreateSchema(**defaults)


def _make_asset_payload(**overrides) -> AssetItemCreateSchema:
    defaults = {
        "asset_code": "ASSET-NEW",
        "name": "New Asset",
        "category": "it_hardware",
        "location": "Room 101",
        "condition": "good",
        "purchase_year": 2024,
        "vendor": "Vendor Y",
        "status": "active",
    }
    defaults.update(overrides)
    return AssetItemCreateSchema(**defaults)


def _make_depr_row(method: str = "straight_line", status: str = "active", rec_id: int = 1) -> dict:
    return {
        "id": rec_id,
        "record_code": f"DEP-{rec_id:03d}",
        "asset_code": "ASSET-001",
        "depreciation_method": method,
        "period_start": "2026-01-01",
        "period_end": "2026-12-31",
        "depreciation_amount": 1000.0,
        "original_value": 10000.0,
        "current_value": 9000.0,
        "depreciation_rate": 0.1,
        "status": status,
    }


# ===========================================================================
# 1. CONSTANTS
# ===========================================================================

class TestConstants:
    def test_depreciable_statuses_contains_active(self):
        assert "active" in svc._DEPRECIABLE_ASSET_STATUSES

    def test_depreciable_statuses_contains_in_maintenance(self):
        assert "in_maintenance" in svc._DEPRECIABLE_ASSET_STATUSES

    def test_depreciable_statuses_excludes_decommissioned(self):
        assert "decommissioned" not in svc._DEPRECIABLE_ASSET_STATUSES

    def test_non_depreciable_conditions_contains_condemned(self):
        assert "condemned" in svc._NON_DEPRECIABLE_ASSET_CONDITIONS

    def test_method_cap_straight_line(self):
        assert svc._METHOD_MAX_ACTIVE_DEPR["straight_line"] == 10

    def test_method_cap_declining_balance(self):
        assert svc._METHOD_MAX_ACTIVE_DEPR["declining_balance"] == 5

    def test_active_statuses_depr_contains_active(self):
        assert "active" in svc._ACTIVE_STATUSES_DEPR

    def test_condemned_cap_it_hardware(self):
        assert svc._ASSET_CATEGORY_MAX_CONDEMNED["it_hardware"] == 10

    def test_condemned_cap_vehicle(self):
        assert svc._ASSET_CATEGORY_MAX_CONDEMNED["vehicle"] == 5


# ===========================================================================
# 2. W114 GUARD — blocked by asset status = decommissioned
# ===========================================================================

class TestW114StatusGuard:
    """Depreciation blocked when asset is decommissioned (phantom financial entry prevention)."""

    def test_decommissioned_asset_blocks_depreciation(self):
        asset = _make_asset(status="decommissioned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")
            assert "decommissioned" in str(exc_info.value).lower() or "not eligible" in str(exc_info.value).lower()

    def test_decommissioned_error_mentions_asset_code(self):
        asset = _make_asset(status="decommissioned", asset_code="ASSET-XYZ")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-XYZ")
            assert "ASSET-XYZ" in str(exc_info.value)

    def test_active_asset_passes_guard(self):
        asset = _make_asset(status="active", condition="good")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            # Should not raise
            svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")

    def test_in_maintenance_asset_passes_guard(self):
        asset = _make_asset(status="in_maintenance", condition="good")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")

    def test_retired_status_blocks_depreciation(self):
        """Any status not in _DEPRECIABLE_ASSET_STATUSES must block."""
        asset = _make_asset(status="retired")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError):
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")

    def test_status_check_is_case_insensitive(self):
        """Guard must normalize status case."""
        asset = _make_asset(status="Decommissioned")  # mixed case from DB
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError):
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")


# ===========================================================================
# 3. W114 GUARD — blocked by asset condition = condemned
# ===========================================================================

class TestW114ConditionGuard:
    """Depreciation blocked when asset condition is condemned (write-off conflict prevention)."""

    def test_condemned_condition_blocks_depreciation(self):
        asset = _make_asset(status="active", condition="condemned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")
            assert "condemned" in str(exc_info.value).lower()

    def test_condemned_error_mentions_write_off_conflict(self):
        asset = _make_asset(status="active", condition="condemned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")
            msg = str(exc_info.value).lower()
            assert "condemned" in msg or "write-off" in msg or "disposal" in msg

    def test_good_condition_passes_guard(self):
        asset = _make_asset(status="active", condition="good")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")

    def test_fair_condition_passes_guard(self):
        asset = _make_asset(status="active", condition="fair")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")

    def test_decommissioned_status_plus_condemned_condition_blocks(self):
        """Double block: both status and condition are bad — error must be raised."""
        asset = _make_asset(status="decommissioned", condition="condemned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            with pytest.raises(DomainValidationError):
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")


# ===========================================================================
# 4. W114 GUARD — fail-closed scenarios
# ===========================================================================

class TestW114FailClosed:
    """Guard must block (fail-closed) when asset cannot be verified."""

    def test_asset_not_found_blocks_depreciation(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[]):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=1, asset_code="NONEXISTENT")
            assert "not found" in str(exc_info.value).lower()

    def test_lookup_exception_blocks_depreciation(self):
        """If asset lookup raises an exception, depreciation MUST be blocked."""
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   side_effect=Exception("DB connection lost")):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=1, asset_code="ASSET-001")
            assert "lookup failed" in str(exc_info.value).lower() or "blocked" in str(exc_info.value).lower()

    def test_guard_uses_case_insensitive_asset_code_matching(self):
        """asset_code='asset-001' should match DB row 'ASSET-001'."""
        asset = _make_asset(asset_code="ASSET-001", status="active", condition="good")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            # Should not raise — lowercase matches ASSET-001
            svc._check_asset_depreciable(tenant_id=1, asset_code="asset-001")

    def test_guard_blocks_wrong_tenant_isolation(self):
        """Asset from tenant 1 must not be found when querying tenant 2."""
        asset = _make_asset(status="active", condition="good")
        call_log: list[int] = []

        def mock_list(entity: str, tenant_id: int) -> list:
            call_log.append(tenant_id)
            if tenant_id == 2:
                return []  # tenant 2 has no assets
            return [asset]

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=mock_list):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_asset_depreciable(tenant_id=2, asset_code="ASSET-001")
            assert "not found" in str(exc_info.value).lower()


# ===========================================================================
# 5. CREATE DEPRECIATION — end-to-end via service
# ===========================================================================

class TestCreateDepreciationRecord:
    def test_decommissioned_asset_blocks_create(self):
        asset = _make_asset(status="decommissioned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            payload = _make_depreciation_payload()
            with pytest.raises(DomainValidationError):
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")

    def test_condemned_condition_blocks_create(self):
        asset = _make_asset(status="active", condition="condemned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]):
            payload = _make_depreciation_payload()
            with pytest.raises(DomainValidationError):
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")

    def test_active_asset_allows_create(self):
        asset = _make_asset(status="active", condition="good")
        depr_row = _make_depr_row()
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant", return_value=depr_row), \
             patch("app.modules.asset_inventory.service.log_admin_action"):
            # 3 calls: (1) _check_asset_depreciable, (2) asset existence re-check, (3) method cap
            mock_list.side_effect = [
                [asset],   # _check_asset_depreciable
                [asset],   # asset exists re-check
                [],        # existing depreciation records (method cap)
            ]
            payload = _make_depreciation_payload()
            result = svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_in_maintenance_asset_allows_create(self):
        asset = _make_asset(status="in_maintenance", condition="good")
        depr_row = _make_depr_row()
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant", return_value=depr_row), \
             patch("app.modules.asset_inventory.service.log_admin_action"):
            mock_list.side_effect = [[asset], [asset], []]
            payload = _make_depreciation_payload()
            result = svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_nonexistent_asset_blocks_create(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[]):
            payload = _make_depreciation_payload(asset_code="GHOST-ASSET")
            with pytest.raises(DomainValidationError) as exc_info:
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            assert "not found" in str(exc_info.value).lower()


# ===========================================================================
# 6. METHOD CAP
# ===========================================================================

class TestMethodCap:
    def test_straight_line_cap_at_10_blocks(self):
        asset = _make_asset(status="active", condition="good")
        existing_depr = [_make_depr_row(method="straight_line", status="active", rec_id=i) for i in range(1, 11)]
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = [[asset], [asset], existing_depr]
            payload = _make_depreciation_payload(depreciation_method="straight_line")
            with pytest.raises(ValueError) as exc_info:
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            assert "cap" in str(exc_info.value).lower() or "limit" in str(exc_info.value).lower() or "straight_line" in str(exc_info.value).lower()

    def test_declining_balance_cap_at_5_blocks(self):
        asset = _make_asset(status="active", condition="good")
        existing_depr = [_make_depr_row(method="declining_balance", status="active", rec_id=i) for i in range(1, 6)]
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = [[asset], [asset], existing_depr]
            payload = _make_depreciation_payload(depreciation_method="declining_balance")
            with pytest.raises(ValueError):
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")

    def test_method_cap_at_9_allows(self):
        asset = _make_asset(status="active", condition="good")
        existing_depr = [_make_depr_row(method="straight_line", status="active", rec_id=i) for i in range(1, 10)]
        depr_row = _make_depr_row(rec_id=10)
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant", return_value=depr_row), \
             patch("app.modules.asset_inventory.service.log_admin_action"):
            mock_list.side_effect = [[asset], [asset], existing_depr]
            payload = _make_depreciation_payload(depreciation_method="straight_line")
            result = svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            assert result is not None


# ===========================================================================
# 7. W56 — CONDEMNED CAP
# ===========================================================================

class TestW56CondemnedCap:
    def test_it_hardware_condemned_cap_at_10_blocks(self):
        existing_assets = [
            _make_asset(category="it_hardware", condition="condemned", asset_id=i)
            for i in range(1, 11)
        ]
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=existing_assets):
            payload = _make_asset_payload(category="it_hardware", condition="condemned")
            with pytest.raises(ValueError) as exc_info:
                svc.create_asset_item(tenant_id=1, request=payload, actor="admin")
            assert "cap" in str(exc_info.value).lower() or "condemned" in str(exc_info.value).lower()

    def test_vehicle_condemned_cap_at_5_blocks(self):
        existing_assets = [
            _make_asset(category="vehicle", condition="condemned", asset_id=i)
            for i in range(1, 6)
        ]
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=existing_assets):
            payload = _make_asset_payload(category="vehicle", condition="condemned")
            with pytest.raises(ValueError):
                svc.create_asset_item(tenant_id=1, request=payload, actor="admin")

    def test_good_condition_not_affected_by_condemned_cap(self):
        asset_row = _make_asset(status="active", condition="good")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[]), \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant",
                   return_value={**asset_row, "id": 99}), \
             patch("app.modules.asset_inventory.service.log_admin_action"):
            payload = _make_asset_payload(condition="good")
            result = svc.create_asset_item(tenant_id=1, request=payload, actor="admin")
            assert result is not None


# ===========================================================================
# 8. TENANT ISOLATION
# ===========================================================================

class TestTenantIsolation:
    def test_list_asset_items_scoped_by_tenant(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            svc.list_asset_items(tenant_id=55)
            mock_list.assert_called_once_with("asset_inventory_items", 55)

    def test_list_depreciation_records_scoped_by_tenant(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            svc.list_depreciation_records(tenant_id=77)
            mock_list.assert_called_once_with("asset_depreciation_records", 77)

    def test_get_asset_item_scoped_by_tenant(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            result = svc.get_asset_item(tenant_id=33, asset_id=1)
            assert result is None
            mock_list.assert_called_once_with("asset_inventory_items", 33)

    def test_w114_guard_passes_correct_tenant_id(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            try:
                svc._check_asset_depreciable(tenant_id=42, asset_code="ASSET-X")
            except DomainValidationError:
                pass
            mock_list.assert_called_with("asset_inventory_items", 42)


# ===========================================================================
# 9. ROUTER STRUCTURE
# ===========================================================================

class TestRouterStructure:
    def test_router_imports_service_as_svc(self):
        import app.modules.asset_inventory.router as router_mod
        assert hasattr(router_mod, "_svc"), "Router must import service as _svc"

    def test_svc_is_service_module(self):
        import app.modules.asset_inventory.router as router_mod
        assert router_mod._svc is svc

    def test_router_no_direct_function_imports(self):
        import app.modules.asset_inventory.router as router_mod
        assert not hasattr(router_mod, "create_depreciation_record")
        assert not hasattr(router_mod, "create_asset_item")
        assert not hasattr(router_mod, "list_asset_items")

    def test_router_has_domain_validation_error_import(self):
        import app.modules.asset_inventory.router as router_mod
        assert hasattr(router_mod, "DomainValidationError")

    def test_router_has_items_route(self):
        import app.modules.asset_inventory.router as router_mod
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/asset-inventory/items" in paths

    def test_router_has_depreciation_route(self):
        import app.modules.asset_inventory.router as router_mod
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/asset-inventory/depreciation" in paths

    def test_create_depreciation_endpoint_catches_domain_error(self):
        import inspect
        import app.modules.asset_inventory.router as router_mod
        source = inspect.getsource(router_mod.create_depreciation_record_endpoint)
        assert "DomainValidationError" in source
        assert "422" in source

    def test_create_asset_endpoint_catches_domain_error(self):
        import inspect
        import app.modules.asset_inventory.router as router_mod
        source = inspect.getsource(router_mod.create_asset_item_endpoint)
        assert "422" in source


# ===========================================================================
# 10. VALIDATE BEFORE PERSIST RULE
# ===========================================================================

class TestValidateBeforePersist:
    """Guard must fire BEFORE create_entity_for_tenant is called."""

    def test_w114_guard_fires_before_persist(self):
        """If asset is decommissioned, create_entity_for_tenant must NEVER be called."""
        asset = _make_asset(status="decommissioned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]), \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant") as mock_create:
            payload = _make_depreciation_payload()
            with pytest.raises(DomainValidationError):
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            mock_create.assert_not_called()

    def test_condemned_condition_guard_fires_before_persist(self):
        """If asset is condemned, create_entity_for_tenant must NEVER be called."""
        asset = _make_asset(status="active", condition="condemned")
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[asset]), \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant") as mock_create:
            payload = _make_depreciation_payload()
            with pytest.raises(DomainValidationError):
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            mock_create.assert_not_called()

    def test_nonexistent_asset_guard_fires_before_persist(self):
        with patch("app.modules.asset_inventory.service.list_entities_for_tenant",
                   return_value=[]), \
             patch("app.modules.asset_inventory.service.create_entity_for_tenant") as mock_create:
            payload = _make_depreciation_payload(asset_code="GHOST")
            with pytest.raises(DomainValidationError):
                svc.create_depreciation_record(tenant_id=1, request=payload, actor="admin")
            mock_create.assert_not_called()
