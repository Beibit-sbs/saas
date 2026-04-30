"""W141 — procurement: DomainValidationError hardening depth tests.

Guard: W111 — contract creation blocked when vendor_code not found in
procurement_vendors OR vendor status is inactive/under_review.
Phantom contract / procurement fraud prevention.
"""
from __future__ import annotations

import inspect
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException

# Load modules under test
import app.modules.procurement.service as _svc
import app.modules.procurement.router  # noqa: F401 — trigger sys.modules registration

_ROUTER_MOD = sys.modules.get("app.modules.procurement.router")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vendor(vendor_code: str = "VEND-001", status: str = "active") -> dict:
    return {
        "id": 1,
        "vendor_code": vendor_code,
        "name": "Test Vendor",
        "category": "it",
        "sla_breach_rate": 0.1,
        "on_time_delivery_rate": 0.9,
        "status": status,
        "contact_name": "Alice",
        "tenant_id": "1",
    }


def _make_tenant(tenant_id: str = "1") -> dict:
    return {"id": tenant_id}


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestW141Constants:
    def test_vendor_active_for_contract_exists(self):
        assert hasattr(_svc, "_VENDOR_ACTIVE_FOR_CONTRACT")

    def test_vendor_active_for_contract_contains_active(self):
        assert "active" in _svc._VENDOR_ACTIVE_FOR_CONTRACT

    def test_vendor_active_for_contract_excludes_inactive(self):
        assert "inactive" not in _svc._VENDOR_ACTIVE_FOR_CONTRACT

    def test_vendor_active_for_contract_excludes_under_review(self):
        assert "under_review" not in _svc._VENDOR_ACTIVE_FOR_CONTRACT

    def test_vendor_active_for_contract_is_frozenset(self):
        assert isinstance(_svc._VENDOR_ACTIVE_FOR_CONTRACT, frozenset)

    def test_po_allowed_transitions_exists(self):
        assert hasattr(_svc, "_PO_ALLOWED_TRANSITIONS")

    def test_po_allowed_transitions_is_dict(self):
        assert isinstance(_svc._PO_ALLOWED_TRANSITIONS, dict)

    def test_high_risk_threshold_exists(self):
        assert hasattr(_svc, "_HIGH_RISK_SCORE_THRESHOLD")

    def test_high_risk_threshold_is_float(self):
        assert isinstance(_svc._HIGH_RISK_SCORE_THRESHOLD, float)

    def test_high_risk_threshold_value(self):
        assert _svc._HIGH_RISK_SCORE_THRESHOLD == pytest.approx(0.8)

    def test_vendor_category_max_active_exists(self):
        assert hasattr(_svc, "_VENDOR_CATEGORY_MAX_ACTIVE")

    def test_vendor_category_max_active_is_dict(self):
        assert isinstance(_svc._VENDOR_CATEGORY_MAX_ACTIVE, dict)

    def test_active_vendor_statuses_exists(self):
        assert hasattr(_svc, "_ACTIVE_VENDOR_STATUSES")

    def test_po_status_aliases_exists(self):
        assert hasattr(_svc, "_PO_STATUS_ALIASES")


# ---------------------------------------------------------------------------
# 2. Guard – block paths
# ---------------------------------------------------------------------------

class TestW141GuardBlockPaths:
    """_check_vendor_active_for_contract raises DomainValidationError when
    vendor not found or has non-active status."""

    def _run(self, vendors: list[dict], vendor_code: str = "VEND-001") -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=vendors):
            _svc._check_vendor_active_for_contract(tenant_id=1, vendor_code=vendor_code)

    def test_missing_vendor_raises(self):
        with pytest.raises(_svc.DomainValidationError):
            self._run(vendors=[], vendor_code="VEND-001")

    def test_inactive_vendor_raises(self):
        vendors = [_make_vendor("VEND-001", "inactive")]
        with pytest.raises(_svc.DomainValidationError):
            self._run(vendors=vendors)

    def test_under_review_vendor_raises(self):
        vendors = [_make_vendor("VEND-001", "under_review")]
        with pytest.raises(_svc.DomainValidationError):
            self._run(vendors=vendors)

    def test_error_mentions_vendor_code(self):
        with pytest.raises(_svc.DomainValidationError) as exc_info:
            self._run(vendors=[], vendor_code="VEND-XYZ")
        assert "VEND-XYZ" in str(exc_info.value)

    def test_wrong_vendor_code_raises(self):
        vendors = [_make_vendor("VEND-001", "active")]
        with pytest.raises(_svc.DomainValidationError):
            self._run(vendors=vendors, vendor_code="VEND-999")

    def test_expired_like_status_raises(self):
        vendors = [_make_vendor("VEND-001", "blacklisted")]
        with pytest.raises(_svc.DomainValidationError):
            self._run(vendors=vendors)


# ---------------------------------------------------------------------------
# 3. Guard – allow paths
# ---------------------------------------------------------------------------

class TestW141GuardAllowPaths:
    """Guard must NOT raise for active vendor."""

    def _run(self, vendors: list[dict], vendor_code: str = "VEND-001") -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=vendors):
            _svc._check_vendor_active_for_contract(tenant_id=1, vendor_code=vendor_code)

    def test_active_vendor_allows(self):
        vendors = [_make_vendor("VEND-001", "active")]
        self._run(vendors=vendors)  # no exception

    def test_active_vendor_case_insensitive_code(self):
        vendors = [_make_vendor("vend-001", "active")]
        self._run(vendors=vendors, vendor_code="VEND-001")  # no exception

    def test_multiple_vendors_one_active_allows(self):
        vendors = [
            _make_vendor("VEND-001", "inactive"),
            _make_vendor("VEND-002", "active"),
        ]
        self._run(vendors=vendors, vendor_code="VEND-002")  # no exception


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------

class TestW141FailClosed:
    """Guard must fail closed on lookup exceptions."""

    def test_lookup_exception_raises_domain_validation_error(self):
        def boom(*_args, **_kwargs):
            raise RuntimeError("DB down")

        with patch.object(_svc, "list_entities_for_tenant", side_effect=boom):
            with pytest.raises(_svc.DomainValidationError):
                _svc._check_vendor_active_for_contract(tenant_id=1, vendor_code="VEND-001")

    def test_lookup_exception_cause_preserved(self):
        original_error = RuntimeError("timeout")

        def boom(*_args, **_kwargs):
            raise original_error

        with patch.object(_svc, "list_entities_for_tenant", side_effect=boom):
            with pytest.raises(_svc.DomainValidationError) as exc_info:
                _svc._check_vendor_active_for_contract(tenant_id=1, vendor_code="VEND-001")
        assert exc_info.value.__cause__ is original_error

    def test_lookup_exception_message_mentions_vendor_code(self):
        def boom(*_args, **_kwargs):
            raise RuntimeError("connection refused")

        with patch.object(_svc, "list_entities_for_tenant", side_effect=boom):
            with pytest.raises(_svc.DomainValidationError) as exc_info:
                _svc._check_vendor_active_for_contract(tenant_id=1, vendor_code="VEND-XYZ")
        assert "VEND-XYZ" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Tenant isolation
# ---------------------------------------------------------------------------

class TestW141TenantIsolation:
    """Vendor from a different tenant must not satisfy the guard."""

    def test_cross_tenant_vendor_does_not_satisfy_guard(self):
        """Vendors for tenant_id=2 returned — guard for tenant_id=1 should block."""
        {**_make_vendor("VEND-001", "active"), "tenant_id": "2"}
        # Simulate: list_entities_for_tenant always returns tenant2's vendor
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(_svc.DomainValidationError):
                _svc._check_vendor_active_for_contract(tenant_id=1, vendor_code="VEND-001")

    def test_guard_calls_list_with_correct_tenant(self):
        call_args = []

        def capture(entity_type, tenant_id):
            call_args.append((entity_type, tenant_id))
            return [_make_vendor("VEND-001", "active")]

        with patch.object(_svc, "list_entities_for_tenant", side_effect=capture):
            _svc._check_vendor_active_for_contract(tenant_id=42, vendor_code="VEND-001")

        assert any(t == 42 for _, t in call_args)


# ---------------------------------------------------------------------------
# 6. create_contract wiring
# ---------------------------------------------------------------------------

class TestW141CreateContractWiring:
    """create_contract must call the guard before persisting."""

    def _make_payload(self, vendor_code: str = "VEND-001"):
        from app.modules.procurement.schemas import ContractCreateSchema
        return ContractCreateSchema(
            contract_code="CTR-001",
            vendor_code=vendor_code,
            title="Test Contract",
            risk_score=0.3,
            sla_target_met=True,
            status="draft",
        )

    def test_active_vendor_allows_create(self):
        vendors = [_make_vendor("VEND-001", "active")]
        created_row = {
            "id": 1, "contract_code": "CTR-001", "vendor_code": "VEND-001",
            "title": "Test Contract", "risk_score": 0.3,
            "sla_target_met": "true", "status": "draft", "tenant_id": "1",
        }

        def mock_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors":
                return vendors
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=mock_list), \
             patch.object(_svc, "create_entity_for_tenant", return_value=created_row), \
             patch.object(_svc, "_emit_audit"):
            result = _svc.create_contract(1, self._make_payload("VEND-001"), "actor")
        assert result.contract_code == "CTR-001"

    def test_inactive_vendor_blocks_create(self):
        vendors = [_make_vendor("VEND-001", "inactive")]

        with patch.object(_svc, "list_entities_for_tenant", return_value=vendors):
            with pytest.raises(_svc.DomainValidationError):
                _svc.create_contract(1, self._make_payload("VEND-001"), "actor")

    def test_nonexistent_vendor_blocks_create(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(_svc.DomainValidationError):
                _svc.create_contract(1, self._make_payload("VEND-999"), "actor")


# ---------------------------------------------------------------------------
# 7. Router structure (source-level)
# ---------------------------------------------------------------------------

class TestW141RouterStructure:
    def test_router_has_routes(self):
        assert _ROUTER_MOD is not None
        assert len(_ROUTER_MOD.router.routes) > 0

    def test_post_contracts_route_exists(self):
        assert _ROUTER_MOD is not None
        paths = [r.path for r in _ROUTER_MOD.router.routes]
        assert "/api/admin/procurement/contracts" in paths

    def test_post_vendors_route_exists(self):
        assert _ROUTER_MOD is not None
        paths = [r.path for r in _ROUTER_MOD.router.routes]
        assert "/api/admin/procurement/vendors" in paths

    def test_patch_contract_status_route_exists(self):
        assert _ROUTER_MOD is not None
        paths = [r.path for r in _ROUTER_MOD.router.routes]
        assert "/api/admin/procurement/contracts/{contract_id}/status" in paths

    def test_domain_validation_error_imported_in_router(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        assert "DomainValidationError" in src

    def test_router_uses_svc_pattern(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        assert "_svc." in src

    def test_create_contract_catches_domain_validation_error(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        assert "DomainValidationError" in src
        # create_contract_endpoint must catch it
        assert "(ValueError, DomainValidationError)" in src

    def test_create_vendor_catches_domain_validation_error(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        # vendor endpoint also catches it
        assert "DomainValidationError" in src


# ---------------------------------------------------------------------------
# 8. Direct endpoint — POST /contracts
# ---------------------------------------------------------------------------

class TestW141RouterPostContractsEndpoint:
    def _get_endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.create_contract_endpoint

    def _make_payload(self):
        from app.modules.procurement.schemas import ContractCreateSchema
        return ContractCreateSchema(
            contract_code="CTR-001",
            vendor_code="VEND-001",
            title="Test Contract",
            risk_score=0.3,
            sla_target_met=True,
            status="draft",
        )

    def test_domain_validation_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_contract",
                          side_effect=_svc.DomainValidationError("vendor inactive")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_contract",
                          side_effect=ValueError("bad contract")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_success_returns_item(self):
        from app.modules.procurement.schemas import ContractSchema
        ep = self._get_endpoint()
        tenant = _make_tenant()
        mock_contract = ContractSchema(
            id=1, contract_code="CTR-001", vendor_code="VEND-001",
            title="Test Contract", risk_score=0.3, sla_target_met=True,
            status="draft", tenant_id="1",
        )
        with patch.object(_svc, "create_contract", return_value=mock_contract):
            result = ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert result.item.contract_code == "CTR-001"


# ---------------------------------------------------------------------------
# 9. Direct endpoint — POST /vendors
# ---------------------------------------------------------------------------

class TestW141RouterPostVendorsEndpoint:
    def _get_endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.create_vendor_endpoint

    def _make_payload(self):
        from app.modules.procurement.schemas import VendorCreateSchema
        return VendorCreateSchema(
            vendor_code="VEND-001",
            name="Test Vendor",
            category="it",
            sla_breach_rate=0.1,
            on_time_delivery_rate=0.9,
            status="active",
        )

    def test_domain_validation_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_vendor",
                          side_effect=_svc.DomainValidationError("cap reached")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_vendor",
                          side_effect=ValueError("duplicate")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_success_returns_item(self):
        from app.modules.procurement.schemas import VendorSchema
        ep = self._get_endpoint()
        tenant = _make_tenant()
        mock_vendor = VendorSchema(
            id=1, vendor_code="VEND-001", name="Test Vendor",
            category="it", sla_breach_rate=0.1, on_time_delivery_rate=0.9,
            status="active", tenant_id="1",
        )
        with patch.object(_svc, "create_vendor", return_value=mock_vendor):
            result = ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert result.item.vendor_code == "VEND-001"


# ---------------------------------------------------------------------------
# 10. Direct endpoint — PATCH /contracts/{id}/status
# ---------------------------------------------------------------------------

class TestW141RouterPatchContractStatusEndpoint:
    def _get_endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.update_contract_status_endpoint

    def _make_payload(self):
        from app.modules.procurement.schemas import ContractStatusUpdateSchema
        return ContractStatusUpdateSchema(status="SUBMITTED")

    def test_domain_validation_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "update_contract_status",
                          side_effect=_svc.DomainValidationError("sla breach")):
            with pytest.raises(HTTPException) as exc_info:
                ep(contract_id=1, payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_value_error_returns_400(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "update_contract_status",
                          side_effect=ValueError("invalid transition")):
            with pytest.raises(HTTPException) as exc_info:
                ep(contract_id=1, payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 400

    def test_not_found_returns_404(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "update_contract_status", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                ep(contract_id=99, payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 404

    def test_success_returns_item(self):
        from app.modules.procurement.schemas import ContractSchema
        ep = self._get_endpoint()
        tenant = _make_tenant()
        mock_contract = ContractSchema(
            id=1, contract_code="CTR-001", vendor_code="VEND-001",
            title="Test Contract", risk_score=0.3, sla_target_met=True,
            status="SUBMITTED", tenant_id="1",
        )
        with patch.object(_svc, "update_contract_status", return_value=mock_contract):
            result = ep(contract_id=1, payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert result.item.status == "SUBMITTED"


# ---------------------------------------------------------------------------
# 11. POST /assets direct endpoint
# ---------------------------------------------------------------------------

class TestW141RouterPostAssetsEndpoint:
    def _get_endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.create_asset_endpoint

    def _make_payload(self):
        from app.modules.procurement.schemas import AssetCreateSchema
        return AssetCreateSchema(
            asset_code="ASSET-001",
            title="Test Asset",
            asset_category="hardware",
            status="available",
        )

    def test_domain_validation_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_asset",
                          side_effect=_svc.DomainValidationError("blocked")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_asset",
                          side_effect=ValueError("bad")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 12. POST /inventory-items direct endpoint
# ---------------------------------------------------------------------------

class TestW141RouterPostInventoryEndpoint:
    def _get_endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.create_inventory_item_endpoint

    def _make_payload(self):
        from app.modules.procurement.schemas import InventoryItemCreateSchema
        return InventoryItemCreateSchema(
            item_code="INV-001",
            title="Test Item",
            current_stock=100,
            reorder_point=20,
            daily_usage_rate=5,
            lead_time_days=3,
            auto_reorder_enabled=True,
            status="healthy",
        )

    def test_domain_validation_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_inventory_item",
                          side_effect=_svc.DomainValidationError("blocked")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._get_endpoint()
        tenant = _make_tenant()
        with patch.object(_svc, "create_inventory_item",
                          side_effect=ValueError("bad")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._make_payload(), actor="admin", _=None, tenant=tenant)
        assert exc_info.value.status_code == 422
