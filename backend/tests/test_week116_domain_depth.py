"""W116 — expense_controls × cost_centers.active: behavioral depth tests.

Cross-entity guard: create_expense_record() must block BEFORE persisting when
the target cost center is inactive/frozen/closed.

Guard: _check_cost_center_is_active()
Wired: FIRST action in create_expense_record() (after cost_center_id_val > 0 check)
Error: DomainValidationError
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.expense_controls.service import (
    create_expense_record,
    _check_cost_center_is_active,
    _COST_CENTER_REQUIRED_ACTIVE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_PAYLOAD = {
    "cost_center_id": 10,
    "category": "travel",
    "amount": 500.0,
    "description": "Conference travel",
    "status": "pending",
}

TENANT_ID = 42


def _make_cost_center(cc_id: int, active, name: str = "Finance CC", code: str = "FIN-01") -> dict:
    return {"id": cc_id, "name": name, "code": code, "budget_limit": 50000.0, "active": active, "tenant_id": TENANT_ID}


def _cc_list(active, cc_id: int = 10):
    return [_make_cost_center(cc_id, active)]


# ---------------------------------------------------------------------------
# 1. Guard constant / sentinel
# ---------------------------------------------------------------------------

class TestW116GuardSentinel:
    def test_sentinel_constant_exists(self):
        assert _COST_CENTER_REQUIRED_ACTIVE is True

    def test_guard_function_exists(self):
        assert callable(_check_cost_center_is_active)

    def test_guard_function_signature_accepts_kwargs(self):
        """Guard must accept tenant_id and cost_center_id as keyword args."""
        import inspect
        sig = inspect.signature(_check_cost_center_is_active)
        params = set(sig.parameters.keys())
        assert "tenant_id" in params
        assert "cost_center_id" in params


# ---------------------------------------------------------------------------
# 2. Guard blocks on inactive cost_center (bool False)
# ---------------------------------------------------------------------------

class TestW116BlocksInactiveBoolFalse:
    def test_inactive_bool_false_raises_domain_error(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=False),
        ):
            with pytest.raises(DomainValidationError, match="not active"):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)

    def test_inactive_bool_false_error_contains_cost_center_id(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=False),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)
            assert "10" in str(exc_info.value)

    def test_inactive_bool_false_error_mentions_financial_control(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=False),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)
            msg = str(exc_info.value).lower()
            assert "freeze" in msg or "reconciliation" in msg or "frozen" in msg or "inactive" in msg or "active" in msg


# ---------------------------------------------------------------------------
# 3. Guard blocks on inactive variants (int 0, string "false", "inactive", etc.)
# ---------------------------------------------------------------------------

class TestW116BlocksInactiveVariants:
    @pytest.mark.parametrize("active_val", [
        0,
        "false",
        "0",
        "inactive",
        "no",
        "closed",
        "frozen",
        "disabled",
    ])
    def test_inactive_variant_raises(self, active_val):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=active_val),
        ):
            with pytest.raises(DomainValidationError):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)

    def test_none_active_field_raises(self):
        """active=None means unknown/not-set → must treat as inactive (fail-closed)."""
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=None),
        ):
            with pytest.raises(DomainValidationError):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)


# ---------------------------------------------------------------------------
# 4. Guard passes on active cost_center (bool True)
# ---------------------------------------------------------------------------

class TestW116PassesActiveCostCenter:
    @pytest.mark.parametrize("active_val", [
        True,
        1,
        "true",
        "True",
        "yes",
        "active",
        "enabled",
        "open",
    ])
    def test_active_variant_passes(self, active_val):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=active_val),
        ):
            # Should not raise
            _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)


# ---------------------------------------------------------------------------
# 5. Guard blocks when cost_center_id not found
# ---------------------------------------------------------------------------

class TestW116BlocksMissingCostCenter:
    def test_missing_cost_center_raises_domain_error(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError, match="not found"):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)

    def test_different_cc_id_in_list_still_raises(self):
        """CC id=99 in list; checking id=10 → not found → DomainValidationError."""
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=[_make_cost_center(99, True)],
        ):
            with pytest.raises(DomainValidationError, match="not found"):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)


# ---------------------------------------------------------------------------
# 6. Fail-closed: lookup exception → DomainValidationError
# ---------------------------------------------------------------------------

class TestW116FailClosed:
    def test_lookup_exception_raises_domain_error(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB connection timeout"),
        ):
            with pytest.raises(DomainValidationError, match="lookup failed"):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)

    def test_lookup_exception_chained(self):
        """Original exception must be chained (not swallowed)."""
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            side_effect=RuntimeError("network error"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)
            assert exc_info.value.__cause__ is not None

    def test_lookup_exception_mentions_cost_center_id(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            side_effect=ConnectionError("timeout"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)
            assert "10" in str(exc_info.value)

    def test_lookup_exception_any_error_type_blocked(self):
        for exc_cls in [ValueError, KeyError, AttributeError, OSError]:
            with patch(
                "app.modules.expense_controls.service.list_entities_for_tenant",
                side_effect=exc_cls("error"),
            ):
                with pytest.raises(DomainValidationError):
                    _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)


# ---------------------------------------------------------------------------
# 7. Guard fires BEFORE persist (create_expense_record integration)
# ---------------------------------------------------------------------------

class TestW116GuardFiresBeforePersist:
    def test_inactive_cc_blocks_before_create_entity(self):
        """create_entity_for_tenant must NOT be called when guard fires."""
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=False),
        ), \
             patch(
            "app.modules.expense_controls.service.create_entity_for_tenant",
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                create_expense_record(_BASE_PAYLOAD.copy(), TENANT_ID)
            mock_create.assert_not_called()

    def test_lookup_failure_blocks_before_create_entity(self):
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB down"),
        ), patch(
            "app.modules.expense_controls.service.create_entity_for_tenant",
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                create_expense_record(_BASE_PAYLOAD.copy(), TENANT_ID)
            mock_create.assert_not_called()

    def test_active_cc_allows_through_to_persist(self):
        """Active cost center: guard passes, create_entity_for_tenant is called."""
        created_row = {**_BASE_PAYLOAD, "id": 999, "cost_center_id": 10, "active": True}
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=True),
        ), patch(
            "app.modules.expense_controls.service.create_entity_for_tenant",
            return_value=created_row,
        ) as mock_create, patch(
            "app.modules.expense_controls.service.EventPublisher",
        ):
            result = create_expense_record(_BASE_PAYLOAD.copy(), TENANT_ID)
        mock_create.assert_called_once()
        assert result["id"] == 999

    def test_frozen_cc_error_is_domain_validation_not_value_error(self):
        """The guard raises DomainValidationError, not ValueError."""
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active="frozen"),
        ):
            with pytest.raises(DomainValidationError):
                create_expense_record(_BASE_PAYLOAD.copy(), TENANT_ID)


# ---------------------------------------------------------------------------
# 8. Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestW116MultiTenantIsolation:
    def test_cc_from_different_tenant_not_found(self):
        """Guard must query by tenant_id — CC for tenant 99 not found for tenant 42."""
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=[],  # empty for this tenant
        ):
            with pytest.raises(DomainValidationError, match="not found"):
                _check_cost_center_is_active(tenant_id=TENANT_ID, cost_center_id=10)

    def test_guard_passes_correct_tenant_id_to_lookup(self):
        calls = []
        def capture_call(entity_type, tenant_id):
            calls.append((entity_type, tenant_id))
            return _cc_list(active=True)

        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            side_effect=capture_call,
        ):
            _check_cost_center_is_active(tenant_id=77, cost_center_id=10)

        assert any(t == 77 for _, t in calls)

    def test_different_tenants_independently_evaluated(self):
        """Two tenants — tenant 1 has active CC, tenant 2 has inactive CC."""
        def side_effect(entity_type, tenant_id):
            if tenant_id == 1:
                return _cc_list(active=True, cc_id=10)
            return _cc_list(active=False, cc_id=10)

        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            side_effect=side_effect,
        ):
            # Tenant 1: passes
            _check_cost_center_is_active(tenant_id=1, cost_center_id=10)
            # Tenant 2: blocked
            with pytest.raises(DomainValidationError):
                _check_cost_center_is_active(tenant_id=2, cost_center_id=10)


# ---------------------------------------------------------------------------
# 9. Edge cases — amount / category still validated even with active CC
# ---------------------------------------------------------------------------

class TestW116EdgeCasesValidation:
    def test_zero_amount_raises_value_error_not_domain_error(self):
        """amount=0 should raise ValueError (basic validation)."""
        payload = {**_BASE_PAYLOAD, "amount": 0}
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=True),
        ):
            with pytest.raises(ValueError, match="amount"):
                create_expense_record(payload, TENANT_ID)

    def test_invalid_cost_center_id_zero_raises_value_error(self):
        """cost_center_id=0 → ValueError before guard fires."""
        payload = {**_BASE_PAYLOAD, "cost_center_id": 0}
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=True),
        ):
            with pytest.raises(ValueError, match="cost_center_id"):
                create_expense_record(payload, TENANT_ID)

    def test_negative_cost_center_id_raises_value_error(self):
        payload = {**_BASE_PAYLOAD, "cost_center_id": -5}
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=True),
        ):
            with pytest.raises(ValueError, match="cost_center_id"):
                create_expense_record(payload, TENANT_ID)

    def test_inactive_cc_blocks_even_for_large_amount(self):
        """Even a large amount doesn't bypass the active check."""
        payload = {**_BASE_PAYLOAD, "amount": 9_999_999.99}
        with patch(
            "app.modules.expense_controls.service.list_entities_for_tenant",
            return_value=_cc_list(active=False),
        ):
            with pytest.raises(DomainValidationError):
                create_expense_record(payload, TENANT_ID)

    def test_inactive_cc_blocks_all_categories(self):
        """Inactive CC blocks expenses for every expense category."""
        categories = ["travel", "software", "equipment", "general"]
        for cat in categories:
            payload = {**_BASE_PAYLOAD, "category": cat}
            with patch(
                "app.modules.expense_controls.service.list_entities_for_tenant",
                return_value=_cc_list(active=False),
            ):
                with pytest.raises(DomainValidationError):
                    create_expense_record(payload, TENANT_ID)


# ---------------------------------------------------------------------------
# 10. Regression: prior guard functions / module imports intact
# ---------------------------------------------------------------------------

class TestW116ModuleIntegrity:
    def test_domain_validation_error_importable(self):
        from app.core.module_helpers.service_validation import DomainValidationError as DVE
        assert DVE is not None

    def test_create_expense_record_importable(self):
        from app.modules.expense_controls.service import create_expense_record as cer
        assert callable(cer)

    def test_list_expense_records_still_importable(self):
        from app.modules.expense_controls.service import list_expense_records
        assert callable(list_expense_records)

    def test_check_cost_center_is_active_importable(self):
        from app.modules.expense_controls.service import _check_cost_center_is_active as g
        assert callable(g)

    def test_expense_category_max_active_dict_intact(self):
        from app.modules.expense_controls.service import _EXPENSE_CATEGORY_MAX_ACTIVE
        assert isinstance(_EXPENSE_CATEGORY_MAX_ACTIVE, dict)
        assert "travel" in _EXPENSE_CATEGORY_MAX_ACTIVE

    def test_budget_risk_statuses_still_defined(self):
        from app.modules.expense_controls.service import _BUDGET_RISK_STATUSES
        assert isinstance(_BUDGET_RISK_STATUSES, frozenset)
