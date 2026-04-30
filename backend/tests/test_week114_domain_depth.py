"""W114 — Asset Inventory × Asset Status guard (Depreciable Asset Eligibility).

Business invariant: A depreciation record may ONLY be created when the referenced
asset_code maps to an asset with:
  1. status in {"active", "in_maintenance"} — NOT "decommissioned"
  2. condition NOT in {"condemned"}

Depreciation on decommissioned or condemned assets creates phantom P&L entries,
distorts book value, and conflicts with write-off accounting processes.

Guard: _check_asset_depreciable() — BEFORE create_entity_for_tenant()
Fail-closed: asset lookup exception → DomainValidationError.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError

ASSET_CODE = "ASSET-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_asset(
    asset_code: str = ASSET_CODE,
    status: str = "active",
    condition: str = "good",
    aid: int = 1,
) -> dict:
    return {
        "id": aid,
        "asset_code": asset_code,
        "name": "Test Asset",
        "category": "equipment",
        "location": "Building A",
        "condition": condition,
        "purchase_year": 2022,
        "vendor": "ACME Corp",
        "status": status,
    }


def _make_depreciation_request(
    asset_code: str = ASSET_CODE,
    method: str = "straight_line",
    original_value: float = 10_000.0,
    current_value: float = 8_000.0,
):
    from app.modules.asset_inventory.schemas import DepreciationRecordCreateSchema
    return DepreciationRecordCreateSchema(
        asset_code=asset_code,
        depreciation_method=method,
        original_value=original_value,
        current_value=current_value,
        depreciation_rate=0.2,
        status="active",
    )


def _fake_create_entity(entity_type, data, tenant_id):
    return {"id": 55, **data}


# ===========================================================================
# GROUP 1 — Guard constants correctness
# ===========================================================================

class TestDepreciableConstants:
    def test_depreciable_statuses_constant_exists(self):
        import app.modules.asset_inventory.service as svc
        assert hasattr(svc, "_DEPRECIABLE_ASSET_STATUSES")

    def test_depreciable_statuses_is_frozenset(self):
        import app.modules.asset_inventory.service as svc
        assert isinstance(svc._DEPRECIABLE_ASSET_STATUSES, frozenset)

    def test_active_in_depreciable_statuses(self):
        import app.modules.asset_inventory.service as svc
        assert "active" in svc._DEPRECIABLE_ASSET_STATUSES

    def test_in_maintenance_in_depreciable_statuses(self):
        import app.modules.asset_inventory.service as svc
        assert "in_maintenance" in svc._DEPRECIABLE_ASSET_STATUSES

    def test_decommissioned_not_in_depreciable_statuses(self):
        import app.modules.asset_inventory.service as svc
        assert "decommissioned" not in svc._DEPRECIABLE_ASSET_STATUSES

    def test_non_depreciable_conditions_constant_exists(self):
        import app.modules.asset_inventory.service as svc
        assert hasattr(svc, "_NON_DEPRECIABLE_ASSET_CONDITIONS")

    def test_non_depreciable_conditions_is_frozenset(self):
        import app.modules.asset_inventory.service as svc
        assert isinstance(svc._NON_DEPRECIABLE_ASSET_CONDITIONS, frozenset)

    def test_condemned_in_non_depreciable_conditions(self):
        import app.modules.asset_inventory.service as svc
        assert "condemned" in svc._NON_DEPRECIABLE_ASSET_CONDITIONS

    def test_good_not_in_non_depreciable_conditions(self):
        import app.modules.asset_inventory.service as svc
        assert "good" not in svc._NON_DEPRECIABLE_ASSET_CONDITIONS


# ===========================================================================
# GROUP 2 — Guard function exists and is wired BEFORE persist
# ===========================================================================

class TestGuardFunctionExists:
    def test_guard_function_exists(self):
        import app.modules.asset_inventory.service as svc
        assert hasattr(svc, "_check_asset_depreciable")

    def test_guard_function_is_callable(self):
        import app.modules.asset_inventory.service as svc
        assert callable(svc._check_asset_depreciable)

    def test_guard_fires_before_persist(self):
        """Guard must be the first action — before any create_entity_for_tenant call."""
        import app.modules.asset_inventory.service as svc_mod
        call_order: list[str] = []

        def fake_guard(*, tenant_id, asset_code):
            call_order.append("guard")

        def fake_list(entity_type, tenant_id):
            return [_make_asset()]

        def fake_create(entity_type, data, tenant_id):
            call_order.append("persist")
            return {"id": 1, "status": "active", **data}

        with (
            patch.object(svc_mod, "_check_asset_depreciable", fake_guard),
            patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.asset_inventory.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.asset_inventory.service.log_admin_action"),
        ):
            svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

        assert call_order[0] == "guard", f"Guard must fire first; got: {call_order}"
        assert "persist" in call_order


# ===========================================================================
# GROUP 3 — Guard blocks: asset not found
# ===========================================================================

class TestGuardBlocksAssetNotFound:
    def _run_guard(self, assets: list[dict], asset_code: str = ASSET_CODE):
        import app.modules.asset_inventory.service as svc_mod
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            return_value=assets,
        ):
            svc_mod._check_asset_depreciable(tenant_id=1, asset_code=asset_code)

    def test_no_assets_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])

    def test_different_asset_code_blocked(self):
        assets = [_make_asset(asset_code="ASSET-999", status="active")]
        with pytest.raises(DomainValidationError):
            self._run_guard(assets, asset_code=ASSET_CODE)

    def test_error_contains_asset_code(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        assert ASSET_CODE in str(exc_info.value)

    def test_error_mentions_not_found(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        msg = str(exc_info.value).lower()
        assert "not found" in msg or "non-existent" in msg


# ===========================================================================
# GROUP 4 — Guard blocks: wrong asset status
# ===========================================================================

class TestGuardBlocksDecommissioned:
    def _run_guard(self, status: str):
        import app.modules.asset_inventory.service as svc_mod
        assets = [_make_asset(status=status, condition="good")]
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            return_value=assets,
        ):
            svc_mod._check_asset_depreciable(tenant_id=1, asset_code=ASSET_CODE)

    def test_decommissioned_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard("decommissioned")

    def test_error_contains_decommissioned_status(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("decommissioned")
        assert "decommissioned" in str(exc_info.value)

    def test_error_mentions_active_or_in_maintenance(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("decommissioned")
        msg = str(exc_info.value).lower()
        assert "active" in msg or "in_maintenance" in msg

    def test_error_mentions_book_value_or_amortization(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("decommissioned")
        msg = str(exc_info.value).lower()
        assert "book value" in msg or "amortization" in msg or "decommissioned" in msg


# ===========================================================================
# GROUP 5 — Guard blocks: condemned condition
# ===========================================================================

class TestGuardBlocksCondemnedCondition:
    def _run_guard(self, condition: str):
        import app.modules.asset_inventory.service as svc_mod
        assets = [_make_asset(status="active", condition=condition)]
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            return_value=assets,
        ):
            svc_mod._check_asset_depreciable(tenant_id=1, asset_code=ASSET_CODE)

    def test_condemned_condition_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard("condemned")

    def test_error_contains_condemned_status(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("condemned")
        assert "condemned" in str(exc_info.value)

    def test_error_mentions_disposal_or_writeoff(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("condemned")
        msg = str(exc_info.value).lower()
        assert "disposal" in msg or "write-off" in msg or "write_off" in msg or "condemned" in msg


# ===========================================================================
# GROUP 6 — Guard allows: depreciable asset
# ===========================================================================

class TestGuardAllows:
    def _run_guard(self, assets: list[dict]):
        import app.modules.asset_inventory.service as svc_mod
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            return_value=assets,
        ):
            svc_mod._check_asset_depreciable(tenant_id=1, asset_code=ASSET_CODE)

    def test_active_good_condition_allowed(self):
        assets = [_make_asset(status="active", condition="good")]
        self._run_guard(assets)  # must not raise

    def test_active_new_condition_allowed(self):
        assets = [_make_asset(status="active", condition="new")]
        self._run_guard(assets)

    def test_active_fair_condition_allowed(self):
        assets = [_make_asset(status="active", condition="fair")]
        self._run_guard(assets)

    def test_active_poor_condition_allowed(self):
        assets = [_make_asset(status="active", condition="poor")]
        self._run_guard(assets)

    def test_in_maintenance_allowed(self):
        assets = [_make_asset(status="in_maintenance", condition="good")]
        self._run_guard(assets)

    def test_correct_asset_among_others(self):
        """Guard finds the correct asset even when other assets exist."""
        assets = [
            _make_asset(asset_code="ASSET-OTHER", status="decommissioned", aid=1),
            _make_asset(asset_code=ASSET_CODE, status="active", condition="good", aid=2),
        ]
        self._run_guard(assets)


# ===========================================================================
# GROUP 7 — Case-insensitive asset_code matching
# ===========================================================================

class TestCaseInsensitiveMatching:
    def _run_guard(self, assets: list[dict], asset_code: str):
        import app.modules.asset_inventory.service as svc_mod
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            return_value=assets,
        ):
            svc_mod._check_asset_depreciable(tenant_id=1, asset_code=asset_code)

    def test_uppercase_asset_code_matched(self):
        assets = [_make_asset(asset_code="asset-001", status="active")]
        self._run_guard(assets, "ASSET-001")  # must not raise

    def test_mixed_case_asset_code_matched(self):
        assets = [_make_asset(asset_code="ASSET-001", status="active")]
        self._run_guard(assets, "asset-001")  # must not raise


# ===========================================================================
# GROUP 8 — Fail-closed: lookup exception → DomainValidationError
# ===========================================================================

class TestFailClosed:
    def test_lookup_exception_raises_domain_error(self):
        import app.modules.asset_inventory.service as svc_mod
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB timeout"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc_mod._check_asset_depreciable(tenant_id=1, asset_code=ASSET_CODE)
        msg = str(exc_info.value).lower()
        assert "lookup failed" in msg or "cannot schedule" in msg or "amortization" in msg

    def test_timeout_exception_fail_closed(self):
        import app.modules.asset_inventory.service as svc_mod
        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            side_effect=TimeoutError("network timeout"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_asset_depreciable(tenant_id=1, asset_code=ASSET_CODE)

    def test_lookup_failure_blocks_persist(self):
        """On lookup failure, create_entity_for_tenant must NOT be called."""
        import app.modules.asset_inventory.service as svc_mod
        persisted: list = []

        def fake_list(entity_type, tenant_id):
            if entity_type == "asset_inventory_items":
                raise RuntimeError("connection error")
            return []

        def fake_create(entity_type, data, tenant_id):
            persisted.append(data)
            return {"id": 1, **data}

        with (
            patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.asset_inventory.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.asset_inventory.service.log_admin_action"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

        assert persisted == [], "persist must NOT be called when guard raises"


# ===========================================================================
# GROUP 9 — Integration: create_depreciation_record end-to-end
# ===========================================================================

class TestCreateDepreciationRecordIntegration:
    def test_creation_allowed_for_active_asset(self):
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="active", condition="good")]

        with (
            patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.asset_inventory.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.asset_inventory.service.log_admin_action"),
        ):
            result = svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

        assert result.asset_code == ASSET_CODE

    def test_creation_blocked_decommissioned_asset(self):
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="decommissioned", condition="good")]

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

    def test_creation_blocked_condemned_condition(self):
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="active", condition="condemned")]

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

    def test_creation_blocked_missing_asset(self):
        import app.modules.asset_inventory.service as svc_mod

        with patch(
            "app.modules.asset_inventory.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

    def test_error_is_domain_validation_not_value_error(self):
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="decommissioned")]

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

    def test_decommissioned_plus_condemned_blocked(self):
        """Both decommissioned status AND condemned condition are rejected."""
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="decommissioned", condition="condemned")]

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

    def test_in_maintenance_allowed(self):
        """in_maintenance assets may still be depreciated."""
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="in_maintenance", condition="good")]

        with (
            patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.asset_inventory.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.asset_inventory.service.log_admin_action"),
        ):
            result = svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

        assert result.asset_code == ASSET_CODE

    def test_method_cap_still_enforced_after_guard_passes(self):
        """After guard passes, existing method cap must still fire."""
        import app.modules.asset_inventory.service as svc_mod

        existing_depr = [
            {
                "id": i,
                "asset_code": f"OTHER-{i}",
                "depreciation_method": "straight_line",
                "status": "active",
                "original_value": 1000.0,
                "current_value": 800.0,
                "depreciation_rate": 0.2,
            }
            for i in range(1, 11)  # 10 = cap for straight_line
        ]

        def fake_list(entity_type, tenant_id):
            if entity_type == "asset_inventory_items":
                return [_make_asset(status="active", condition="good")]
            return existing_depr

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(ValueError, match="cap"):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(method="straight_line"), "actor")

    def test_tenant_isolation(self):
        """Guard only looks at assets for the correct tenant_id."""
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "asset_inventory_items" and tenant_id == 2:
                return [_make_asset(status="active", condition="good")]
            return []

        with patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

    def test_record_persisted_with_correct_asset_code(self):
        """After guard passes, record is persisted with correct asset_code."""
        import app.modules.asset_inventory.service as svc_mod

        def fake_list(entity_type, tenant_id):
            return [_make_asset(status="active", condition="good")]

        with (
            patch("app.modules.asset_inventory.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.asset_inventory.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.asset_inventory.service.log_admin_action"),
        ):
            result = svc_mod.create_depreciation_record(1, _make_depreciation_request(), "actor")

        assert result.id == 55
        assert result.asset_code == ASSET_CODE
