"""W135: Domain-depth tests for dining module.

Tests:
- _ORDERABLE_MENU_STATUSES constant
- _check_menu_is_orderable guard signature & failures
- Fail-closed behaviour on infra errors
- create_dining_order integration path
- Business invariants (tenant isolation, case-insensitive, empty menu_code bypass)
- Router structure (DomainValidationError wired in POST endpoints)
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.dining.service as _svc
import app.modules.dining.router as _router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TENANT = 55
_MENU_CODE = "MENU-LUNCH-01"


def _menu(menu_code: str = _MENU_CODE, status: str = "active") -> dict:
    return {
        "id": 1,
        "menu_code": menu_code,
        "meal_type": "lunch",
        "status": status,
        "facility_code": "CAFT-A",
        "available_capacity": 50,
    }


def _order_payload(menu_code: str = _MENU_CODE) -> dict:
    return {
        "menu_code": menu_code,
        "student_id": "STU-001",
        "items": ["pizza", "salad"],
    }


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------
class TestW135Constants:
    def test_orderable_menu_statuses_exists(self):
        assert hasattr(_svc, "_ORDERABLE_MENU_STATUSES")

    def test_orderable_menu_statuses_is_frozenset(self):
        assert isinstance(_svc._ORDERABLE_MENU_STATUSES, frozenset)

    def test_active_in_orderable_statuses(self):
        assert "active" in _svc._ORDERABLE_MENU_STATUSES

    def test_published_in_orderable_statuses(self):
        assert "published" in _svc._ORDERABLE_MENU_STATUSES

    def test_draft_not_in_orderable_statuses(self):
        assert "draft" not in _svc._ORDERABLE_MENU_STATUSES

    def test_archived_not_in_orderable_statuses(self):
        assert "archived" not in _svc._ORDERABLE_MENU_STATUSES

    def test_closed_not_in_orderable_statuses(self):
        assert "closed" not in _svc._ORDERABLE_MENU_STATUSES

    def test_orderable_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._ORDERABLE_MENU_STATUSES.add("hacked")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Guard signature
# ---------------------------------------------------------------------------
class TestW135GuardSignature:
    def test_callable(self):
        assert callable(_svc._check_menu_is_orderable)

    def test_requires_tenant_id(self):
        sig = inspect.signature(_svc._check_menu_is_orderable)
        assert "tenant_id" in sig.parameters

    def test_requires_menu_code(self):
        sig = inspect.signature(_svc._check_menu_is_orderable)
        assert "menu_code" in sig.parameters

    def test_returns_none_when_menu_active(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_menu(status="active")]):
            result = _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)
        assert result is None

    def test_returns_none_when_menu_published(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_menu(status="published")]):
            result = _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)
        assert result is None


# ---------------------------------------------------------------------------
# 3. Guard failures
# ---------------------------------------------------------------------------
class TestW135GuardFailures:
    def test_missing_menu_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="not found"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_draft_menu_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_menu(status="draft")]):
            with pytest.raises(DomainValidationError, match="draft"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_archived_menu_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_menu(status="archived")]):
            with pytest.raises(DomainValidationError, match="archived"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_closed_menu_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_menu(status="closed")]):
            with pytest.raises(DomainValidationError, match="closed"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_error_message_contains_menu_code(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match=_MENU_CODE):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_suspended_menu_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_menu(status="suspended")]):
            with pytest.raises(DomainValidationError):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------
class TestW135FailClosed:
    def test_runtime_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=RuntimeError("DB down")):
            with pytest.raises(DomainValidationError, match="menu lookup failed"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_connection_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=ConnectionError("timeout")):
            with pytest.raises(DomainValidationError, match="menu lookup failed"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_os_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=OSError("io error")):
            with pytest.raises(DomainValidationError):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_value_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=ValueError("parse error")):
            with pytest.raises(DomainValidationError):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_chained_exception_preserved(self):
        original = RuntimeError("storage failure")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=original):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# 5. create_dining_order integration
# ---------------------------------------------------------------------------
class TestW135CreateOrderPath:
    def _mk_list(self, menus: list[dict]):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "dining_menus":
                return menus
            return []
        return MagicMock(side_effect=_list)

    def _mk_create(self):
        return MagicMock(side_effect=lambda et, data, tid: {**data, "id": 1, "tenant_id": str(tid)})

    def test_active_menu_allows_order(self):
        mock_list = self._mk_list([_menu(status="active")])
        mock_create = self._mk_create()
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_dining_order(_order_payload(), _TENANT)
        assert result is not None
        mock_create.assert_called_once()

    def test_published_menu_allows_order(self):
        mock_list = self._mk_list([_menu(status="published")])
        mock_create = self._mk_create()
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_dining_order(_order_payload(), _TENANT)
        assert result is not None

    def test_missing_menu_blocks_order(self):
        mock_list = self._mk_list([])
        with patch.object(_svc, "list_entities_for_tenant", mock_list):
            with pytest.raises(DomainValidationError):
                _svc.create_dining_order(_order_payload(), _TENANT)

    def test_draft_menu_blocks_order(self):
        mock_list = self._mk_list([_menu(status="draft")])
        with patch.object(_svc, "list_entities_for_tenant", mock_list):
            with pytest.raises(DomainValidationError):
                _svc.create_dining_order(_order_payload(), _TENANT)

    def test_empty_menu_code_bypasses_guard(self):
        """Empty menu_code skips the guard."""
        mock_create = self._mk_create()
        with patch.object(_svc, "create_entity_for_tenant", mock_create):
            payload = _order_payload(menu_code="")
            result = _svc.create_dining_order(payload, _TENANT)
        assert result is not None
        mock_create.assert_called_once()

    def test_infra_failure_blocks_order(self):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "dining_menus":
                raise RuntimeError("DB down")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_dining_order(_order_payload(), _TENANT)


# ---------------------------------------------------------------------------
# 6. Business invariants
# ---------------------------------------------------------------------------
class TestW135BusinessInvariants:
    def test_tenant_isolation(self):
        seen_tenant_ids = []

        def _list(entity_type, tenant_id):
            if entity_type == "dining_menus":
                seen_tenant_ids.append(tenant_id)
                return []
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc._check_menu_is_orderable(tenant_id=99, menu_code=_MENU_CODE)
        assert seen_tenant_ids == [99]

    def test_menu_code_case_insensitive(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_menu(menu_code="menu-lunch-01", status="active")]):
            result = _svc._check_menu_is_orderable(
                tenant_id=_TENANT, menu_code="MENU-LUNCH-01"
            )
        assert result is None

    def test_different_menu_code_not_matched(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_menu(menu_code="MENU-DINNER-99", status="active")]):
            with pytest.raises(DomainValidationError, match="not found"):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_multiple_menus_picks_correct_one(self):
        """Guard only checks the menu matching the code, not others."""
        menus = [
            _menu(menu_code="MENU-OTHER", status="draft"),
            _menu(menu_code=_MENU_CODE, status="active"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=menus):
            result = _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)
        assert result is None

    def test_multiple_menus_picks_correct_one_blocks(self):
        """Guard blocks on matching menu even if other menus are active."""
        menus = [
            _menu(menu_code="MENU-ACTIVE", status="active"),
            _menu(menu_code=_MENU_CODE, status="closed"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=menus):
            with pytest.raises(DomainValidationError):
                _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)

    def test_guard_fires_before_create(self):
        """Guard fires FIRST — create_entity must NOT be called when guard blocks."""
        mock_list = MagicMock(return_value=[_menu(status="closed")])
        mock_create = MagicMock()
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            with pytest.raises(DomainValidationError):
                _svc.create_dining_order(_order_payload(), _TENANT)
        mock_create.assert_not_called()

    def test_status_whitespace_trimmed(self):
        """Menu status with surrounding spaces is trimmed before comparison."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_menu(status="  active  ")]):
            result = _svc._check_menu_is_orderable(tenant_id=_TENANT, menu_code=_MENU_CODE)
        assert result is None


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------
class TestW135RouterStructure:
    def test_menus_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/dining/menus" in routes

    def test_orders_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/dining/orders" in routes

    def test_domain_validation_error_imported_in_router(self):
        assert hasattr(_router, "DomainValidationError")

    def test_create_order_endpoint_callable(self):
        assert callable(getattr(_router, "create_order_endpoint", None))

    def test_create_menu_endpoint_callable(self):
        assert callable(getattr(_router, "create_menu_endpoint", None))
