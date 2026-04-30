"""W111 — Procurement Contract × Vendor cross-entity guard.

Business invariant: A procurement contract may only be created when the
referenced vendor_code exists in procurement_vendors AND the vendor has
status 'active'. Contracting with non-existent or inactive vendors creates
financial obligations without a valid counterparty, enables procurement
fraud, and corrupts Brain Core vendor risk analytics.

Guard: _check_vendor_active_for_contract() — BEFORE create_entity_for_tenant()
Fail-closed: if vendor lookup raises any exception → DomainValidationError.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError

MODULE_PATH = "app.modules.procurement.service"

VENDOR_CODE = "VND-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vendor(vendor_code: str, status: str, vid: int = 1) -> dict:
    return {
        "id": vid,
        "vendor_code": vendor_code,
        "name": f"Vendor {vid}",
        "category": "it",
        "sla_breach_rate": 0.05,
        "on_time_delivery_rate": 0.95,
        "status": status,
        "contact_name": "John Doe",
    }


def _make_contract_payload(vendor_code: str = VENDOR_CODE, risk_score: float = 0.1):
    from app.modules.procurement.schemas import ContractCreateSchema
    return ContractCreateSchema(
        contract_code="CTR-001",
        vendor_code=vendor_code,
        title="IT Services Contract",
        risk_score=risk_score,
        sla_target_met=True,
        status="draft",
    )


def _fake_create_entity(entity_type, data, tenant_id):
    return {"id": 99, **data}


# ===========================================================================
# GROUP 1 — Constant correctness
# ===========================================================================

class TestVendorActiveForContractConstant:
    def test_constant_exists(self):
        import app.modules.procurement.service as svc
        assert hasattr(svc, "_VENDOR_ACTIVE_FOR_CONTRACT")

    def test_constant_is_frozenset(self):
        import app.modules.procurement.service as svc
        assert isinstance(svc._VENDOR_ACTIVE_FOR_CONTRACT, frozenset)

    def test_active_in_constant(self):
        import app.modules.procurement.service as svc
        assert "active" in svc._VENDOR_ACTIVE_FOR_CONTRACT

    def test_inactive_not_in_constant(self):
        import app.modules.procurement.service as svc
        assert "inactive" not in svc._VENDOR_ACTIVE_FOR_CONTRACT

    def test_under_review_not_in_constant(self):
        import app.modules.procurement.service as svc
        assert "under_review" not in svc._VENDOR_ACTIVE_FOR_CONTRACT

    def test_constant_has_exactly_one_status(self):
        import app.modules.procurement.service as svc
        assert len(svc._VENDOR_ACTIVE_FOR_CONTRACT) == 1


# ===========================================================================
# GROUP 2 — Guard function exists and is wired before persist
# ===========================================================================

class TestGuardFunctionExists:
    def test_check_function_exists(self):
        import app.modules.procurement.service as svc
        assert hasattr(svc, "_check_vendor_active_for_contract")

    def test_check_function_is_callable(self):
        import app.modules.procurement.service as svc
        assert callable(svc._check_vendor_active_for_contract)

    def test_guard_fires_before_persist(self):
        """Guard must call before create_entity_for_tenant."""
        import app.modules.procurement.service as svc_mod
        call_order: list[str] = []

        def fake_guard(*, tenant_id, vendor_code):
            call_order.append("guard")

        def fake_create(entity_type, data, tenant_id):
            call_order.append("persist")
            return {"id": 1, **data}

        def fake_list(entity_type, tenant_id):
            return []

        with (
            patch.object(svc_mod, "_check_vendor_active_for_contract", fake_guard),
            patch("app.modules.procurement.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.procurement.service.log_admin_action"),
        ):
            svc_mod.create_contract(1, _make_contract_payload(), "actor")

        assert call_order[0] == "guard", f"Guard must be first; got: {call_order}"
        assert "persist" in call_order


# ===========================================================================
# GROUP 3 — Guard blocks: vendor not found
# ===========================================================================

class TestGuardBlocksVendorNotFound:
    def _run_guard(self, vendors: list[dict], vendor_code: str = VENDOR_CODE):
        import app.modules.procurement.service as svc_mod
        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=vendors,
        ):
            svc_mod._check_vendor_active_for_contract(
                tenant_id=1,
                vendor_code=vendor_code,
            )

    def test_no_vendors_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])

    def test_vendor_not_found_blocked(self):
        vendors = [_make_vendor("VND-OTHER", "active")]
        with pytest.raises(DomainValidationError):
            self._run_guard(vendors)

    def test_error_message_contains_vendor_code(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        assert VENDOR_CODE in str(exc_info.value)

    def test_error_message_mentions_not_found(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        msg = str(exc_info.value).lower()
        assert "not found" in msg or "unknown" in msg


# ===========================================================================
# GROUP 4 — Guard blocks: vendor found but wrong status
# ===========================================================================

class TestGuardBlocksInactiveVendor:
    def _run_guard(self, vendors: list[dict], vendor_code: str = VENDOR_CODE):
        import app.modules.procurement.service as svc_mod
        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=vendors,
        ):
            svc_mod._check_vendor_active_for_contract(
                tenant_id=1,
                vendor_code=vendor_code,
            )

    def test_inactive_vendor_blocked(self):
        vendors = [_make_vendor(VENDOR_CODE, "inactive")]
        with pytest.raises(DomainValidationError):
            self._run_guard(vendors)

    def test_under_review_vendor_blocked(self):
        vendors = [_make_vendor(VENDOR_CODE, "under_review")]
        with pytest.raises(DomainValidationError):
            self._run_guard(vendors)

    def test_unknown_status_blocked(self):
        vendors = [_make_vendor(VENDOR_CODE, "suspended")]
        with pytest.raises(DomainValidationError):
            self._run_guard(vendors)

    def test_error_message_contains_vendor_status(self):
        vendors = [_make_vendor(VENDOR_CODE, "inactive")]
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard(vendors)
        assert "inactive" in str(exc_info.value)

    def test_error_message_contains_vendor_code(self):
        vendors = [_make_vendor(VENDOR_CODE, "inactive")]
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard(vendors)
        assert VENDOR_CODE in str(exc_info.value)

    def test_error_message_mentions_active(self):
        vendors = [_make_vendor(VENDOR_CODE, "under_review")]
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard(vendors)
        assert "active" in str(exc_info.value).lower()


# ===========================================================================
# GROUP 5 — Guard allows: vendor active
# ===========================================================================

class TestGuardAllows:
    def _run_guard(self, vendors: list[dict], vendor_code: str = VENDOR_CODE):
        import app.modules.procurement.service as svc_mod
        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=vendors,
        ):
            svc_mod._check_vendor_active_for_contract(
                tenant_id=1,
                vendor_code=vendor_code,
            )

    def test_active_vendor_allowed(self):
        vendors = [_make_vendor(VENDOR_CODE, "active")]
        self._run_guard(vendors)  # must not raise

    def test_active_among_many_vendors_allowed(self):
        vendors = [
            _make_vendor("VND-OTHER-1", "inactive", _gid := 1),
            _make_vendor(VENDOR_CODE, "active", 2),
            _make_vendor("VND-OTHER-2", "under_review", 3),
        ]
        self._run_guard(vendors)

    def test_different_vendor_does_not_help(self):
        """Active status for another vendor must NOT unblock this vendor_code."""
        vendors = [_make_vendor("VND-OTHER", "active")]
        with pytest.raises(DomainValidationError):
            self._run_guard(vendors)


# ===========================================================================
# GROUP 6 — Case-insensitive vendor_code matching
# ===========================================================================

class TestCaseInsensitiveMatching:
    def _run_guard(self, vendors: list[dict], vendor_code: str = VENDOR_CODE):
        import app.modules.procurement.service as svc_mod
        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=vendors,
        ):
            svc_mod._check_vendor_active_for_contract(
                tenant_id=1,
                vendor_code=vendor_code,
            )

    def test_vendor_code_uppercase_in_db_matched(self):
        vendors = [_make_vendor(VENDOR_CODE.upper(), "active")]
        self._run_guard(vendors)

    def test_vendor_code_request_uppercase_matched(self):
        vendors = [_make_vendor(VENDOR_CODE, "active")]
        self._run_guard(vendors, vendor_code=VENDOR_CODE.upper())

    def test_vendor_status_uppercase_active_allowed(self):
        vendor = _make_vendor(VENDOR_CODE, "active")
        vendor["status"] = "ACTIVE"
        self._run_guard([vendor])

    def test_vendor_status_mixed_case_allowed(self):
        vendor = _make_vendor(VENDOR_CODE, "active")
        vendor["status"] = "Active"
        self._run_guard([vendor])


# ===========================================================================
# GROUP 7 — Fail-closed: lookup exception → DomainValidationError
# ===========================================================================

class TestFailClosed:
    def test_lookup_exception_raises_domain_error(self):
        import app.modules.procurement.service as svc_mod
        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB timeout"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc_mod._check_vendor_active_for_contract(
                    tenant_id=1,
                    vendor_code=VENDOR_CODE,
                )
        msg = str(exc_info.value).lower()
        assert "cannot verify" in msg or "lookup failed" in msg

    def test_lookup_failure_blocks_contract_persist(self):
        """On lookup failure, create_entity_for_tenant must NOT be called."""
        import app.modules.procurement.service as svc_mod
        persisted: list = []

        def fake_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors":
                raise RuntimeError("network error")
            return []

        def fake_create(entity_type, data, tenant_id):
            persisted.append(data)
            return {"id": 1, **data}

        with (
            patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.procurement.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.procurement.service.log_admin_action"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(1, _make_contract_payload(), "actor")

        assert persisted == [], "persist must NOT be called when guard raises"

    def test_timeout_exception_fail_closed(self):
        import app.modules.procurement.service as svc_mod
        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            side_effect=TimeoutError("vendor lookup timed out"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_vendor_active_for_contract(
                    tenant_id=1,
                    vendor_code=VENDOR_CODE,
                )


# ===========================================================================
# GROUP 8 — Integration: create_contract end-to-end
# ===========================================================================

class TestCreateContractIntegration:
    def test_creation_allowed_with_active_vendor(self):
        import app.modules.procurement.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors":
                return [_make_vendor(VENDOR_CODE, "active")]
            return []

        with (
            patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.procurement.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.procurement.service.log_admin_action"),
        ):
            result = svc_mod.create_contract(1, _make_contract_payload(), "actor")

        assert result.vendor_code == VENDOR_CODE

    def test_creation_blocked_vendor_not_found(self):
        import app.modules.procurement.service as svc_mod

        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(1, _make_contract_payload(), "actor")

    def test_creation_blocked_inactive_vendor(self):
        import app.modules.procurement.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors":
                return [_make_vendor(VENDOR_CODE, "inactive")]
            return []

        with patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(1, _make_contract_payload(), "actor")

    def test_creation_blocked_under_review_vendor(self):
        import app.modules.procurement.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors":
                return [_make_vendor(VENDOR_CODE, "under_review")]
            return []

        with patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(1, _make_contract_payload(), "actor")

    def test_error_is_domain_validation_not_value_error(self):
        """Guard must raise DomainValidationError, not ValueError."""
        import app.modules.procurement.service as svc_mod

        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(1, _make_contract_payload(), "actor")

    def test_high_risk_contract_still_requires_vendor(self):
        """High risk_score contract must still be blocked without active vendor."""
        import app.modules.procurement.service as svc_mod

        with patch(
            "app.modules.procurement.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(
                    1, _make_contract_payload(risk_score=0.95), "actor"
                )

    def test_tenant_isolation(self):
        """Guard only sees vendors for the correct tenant_id."""
        import app.modules.procurement.service as svc_mod

        # tenant 2 has active vendor; tenant 1 has none
        def fake_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors" and tenant_id == 2:
                return [_make_vendor(VENDOR_CODE, "active")]
            return []

        with patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list):
            # tenant 1 — blocked
            with pytest.raises(DomainValidationError):
                svc_mod.create_contract(1, _make_contract_payload(), "actor")

    def test_contract_created_with_correct_vendor_code(self):
        """After guard passes, contract is persisted with correct vendor_code."""
        import app.modules.procurement.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "procurement_vendors":
                return [_make_vendor(VENDOR_CODE, "active")]
            return []

        with (
            patch("app.modules.procurement.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.procurement.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.procurement.service.log_admin_action"),
        ):
            result = svc_mod.create_contract(1, _make_contract_payload(), "actor")

        assert result.id == 99
        assert result.vendor_code == VENDOR_CODE
