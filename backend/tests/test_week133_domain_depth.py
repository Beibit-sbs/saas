"""W133: Domain-depth tests for transport module.

Tests:
- _BOOKABLE_ROUTE_STATUSES constants
- _check_route_is_bookable guard signature & failures
- Fail-closed behaviour on infra errors
- create_transport_booking integration path
- Business invariants (tenant isolation, case-insensitive, whitespace)
- Router structure (DomainValidationError wired in both POST endpoints)
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.transport.service as _svc
import app.modules.transport.router as _router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TENANT = 66
_ROUTE_CODE = "RT-001"


def _route(status: str, route_code: str = _ROUTE_CODE) -> dict:
    return {"id": 1, "route_code": route_code, "status": status, "vehicle_type": "bus"}


def _booking_payload(**kwargs) -> dict:
    base = {
        "booking_code": "BK-001",
        "route_code": _ROUTE_CODE,
        "student_id": "stu-001",
        "booking_status": "confirmed",
        "seat_number": "12A",
        "notes": None,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------
class TestW133Constants:
    def test_sentinel_exists(self):
        assert hasattr(_svc, "_BOOKABLE_ROUTE_STATUSES")

    def test_sentinel_is_frozenset(self):
        assert isinstance(_svc._BOOKABLE_ROUTE_STATUSES, frozenset)

    def test_active_in_sentinel(self):
        assert "active" in _svc._BOOKABLE_ROUTE_STATUSES

    def test_scheduled_in_sentinel(self):
        assert "scheduled" in _svc._BOOKABLE_ROUTE_STATUSES

    def test_disrupted_not_in_sentinel(self):
        assert "disrupted" not in _svc._BOOKABLE_ROUTE_STATUSES

    def test_cancelled_not_in_sentinel(self):
        assert "cancelled" not in _svc._BOOKABLE_ROUTE_STATUSES

    def test_suspended_not_in_sentinel(self):
        assert "suspended" not in _svc._BOOKABLE_ROUTE_STATUSES

    def test_sentinel_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._BOOKABLE_ROUTE_STATUSES.add("hacked")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Guard signature
# ---------------------------------------------------------------------------
class TestW133GuardSignature:
    def test_callable(self):
        assert callable(_svc._check_route_is_bookable)

    def test_requires_tenant_id(self):
        sig = inspect.signature(_svc._check_route_is_bookable)
        assert "tenant_id" in sig.parameters

    def test_requires_route_code(self):
        sig = inspect.signature(_svc._check_route_is_bookable)
        assert "route_code" in sig.parameters

    def test_all_kwargs(self):
        sig = inspect.signature(_svc._check_route_is_bookable)
        for name, param in sig.parameters.items():
            assert param.kind == inspect.Parameter.KEYWORD_ONLY, f"{name} must be keyword-only"

    def test_returns_none_on_success_active(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("active")]):
            result = _svc._check_route_is_bookable(
                tenant_id=_TENANT, route_code=_ROUTE_CODE
            )
        assert result is None

    def test_returns_none_on_success_scheduled(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("scheduled")]):
            result = _svc._check_route_is_bookable(
                tenant_id=_TENANT, route_code=_ROUTE_CODE
            )
        assert result is None


# ---------------------------------------------------------------------------
# 3. Guard failures
# ---------------------------------------------------------------------------
class TestW133GuardFailures:
    def test_route_not_found_raises(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="route not found"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_wrong_route_code_raises(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("active", route_code="OTHER-999")]):
            with pytest.raises(DomainValidationError, match="route not found"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_disrupted_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("disrupted")]):
            with pytest.raises(DomainValidationError, match="not bookable"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_cancelled_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("cancelled")]):
            with pytest.raises(DomainValidationError, match="not bookable"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_suspended_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("suspended")]):
            with pytest.raises(DomainValidationError, match="not bookable"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_error_message_contains_route_code(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("disrupted")]):
            with pytest.raises(DomainValidationError, match=_ROUTE_CODE):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_error_message_contains_actual_status(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("cancelled")]):
            with pytest.raises(DomainValidationError, match="cancelled"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------
class TestW133FailClosed:
    def test_runtime_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=RuntimeError("DB down")):
            with pytest.raises(DomainValidationError, match="route lookup failed"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_connection_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ConnectionError("timeout")):
            with pytest.raises(DomainValidationError, match="route lookup failed"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_os_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=OSError("io error")):
            with pytest.raises(DomainValidationError):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_value_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ValueError("parse error")):
            with pytest.raises(DomainValidationError):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)

    def test_chained_exception_preserved(self):
        original = RuntimeError("DB down")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=original):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# 5. create_transport_booking integration
# ---------------------------------------------------------------------------
class TestW133CreatePath:
    def _setup_mocks(self, route_status: str = "active"):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "transport_routes":
                return [_route(route_status)]
            return []

        mock_list = MagicMock(side_effect=_list)
        mock_create = MagicMock(side_effect=lambda et, data, tid: {**data, "id": 1, "tenant_id": str(tid)})
        return mock_list, mock_create

    def test_guard_fires_before_persist(self):
        """Guard calls list_entities_for_tenant(transport_routes) before create."""
        call_order = []

        def _list(entity_type, tenant_id):
            call_order.append(entity_type)
            if entity_type == "transport_routes":
                raise DomainValidationError("blocked")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_transport_booking(_booking_payload(), _TENANT)

        assert "transport_routes" in call_order

    def test_non_existent_route_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="route not found"):
                _svc.create_transport_booking(_booking_payload(), _TENANT)

    def test_disrupted_route_blocks(self):
        def _list(entity_type, tenant_id):
            if entity_type == "transport_routes":
                return [_route("disrupted")]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError, match="not bookable"):
                _svc.create_transport_booking(_booking_payload(), _TENANT)

    def test_active_route_booking_succeeds(self):
        mock_list, mock_create = self._setup_mocks("active")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_transport_booking(_booking_payload(), _TENANT)
        assert result is not None
        mock_create.assert_called_once()

    def test_scheduled_route_booking_succeeds(self):
        mock_list, mock_create = self._setup_mocks("scheduled")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_transport_booking(_booking_payload(), _TENANT)
        assert result is not None

    def test_infra_failure_blocks(self):
        """RuntimeError on transport_routes lookup → DomainValidationError."""
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "transport_routes":
                raise RuntimeError("DB down")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_transport_booking(_booking_payload(), _TENANT)


# ---------------------------------------------------------------------------
# 6. Business invariants
# ---------------------------------------------------------------------------
class TestW133BusinessInvariants:
    def test_tenant_isolation(self):
        seen_tenant_ids = []

        def _list(entity_type, tenant_id):
            if entity_type == "transport_routes":
                seen_tenant_ids.append(tenant_id)
                return []
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc._check_route_is_bookable(tenant_id=99, route_code=_ROUTE_CODE)
        assert seen_tenant_ids == [99]

    def test_route_code_case_insensitive(self):
        """route_code matching is case-insensitive."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("active", route_code="rt-001")]):
            result = _svc._check_route_is_bookable(
                tenant_id=_TENANT, route_code="RT-001"
            )
        assert result is None

    def test_route_code_whitespace_stripped(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("active", route_code="  RT-001  ")]):
            result = _svc._check_route_is_bookable(
                tenant_id=_TENANT, route_code="RT-001"
            )
        assert result is None

    def test_status_case_insensitive(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("ACTIVE")]):
            result = _svc._check_route_is_bookable(
                tenant_id=_TENANT, route_code=_ROUTE_CODE
            )
        assert result is None

    def test_multiple_routes_uses_first_match(self):
        """First matching route_code is used for status check."""
        routes = [
            {"id": 1, "route_code": "OTHER", "status": "disrupted"},
            _route("active"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=routes):
            result = _svc._check_route_is_bookable(
                tenant_id=_TENANT, route_code=_ROUTE_CODE
            )
        assert result is None

    def test_empty_route_code_not_found(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("active")]):
            with pytest.raises(DomainValidationError, match="route not found"):
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code="")

    def test_cancelled_error_lists_bookable_statuses(self):
        """Error message for non-bookable status mentions acceptable statuses."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_route("cancelled")]):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_route_is_bookable(tenant_id=_TENANT, route_code=_ROUTE_CODE)
        msg = str(exc_info.value)
        assert "active" in msg or "scheduled" in msg


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------
class TestW133RouterStructure:
    def test_routes_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/transport/routes" in routes

    def test_bookings_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/transport/bookings" in routes

    def test_domain_validation_error_imported_in_router(self):
        assert hasattr(_router, "DomainValidationError")

    def test_create_route_endpoint_exists(self):
        assert callable(getattr(_router, "create_route_endpoint", None))

    def test_create_booking_endpoint_exists(self):
        assert callable(getattr(_router, "create_booking_endpoint", None))

    def test_brain_context_endpoint_exists(self):
        assert callable(getattr(_router, "brain_context_endpoint", None))
