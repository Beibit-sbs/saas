"""W147 — facilities_work_orders: Deep Domain Test Pack.

Guards tested:
- W122: create_work_order blocked when facility has active high-severity security incident
- SLA open-cap: _PRIORITY_MAX_OPEN per priority
- Delay queue cap: _WORK_ORDER_QUEUE_MAX_DELAYED per priority
- Closure guard: _check_no_blocking_security_incidents blocks completion under active incidents
- Tenant isolation: all lookups scoped by tenant_id
- facility_code validation: empty/None/whitespace → DomainValidationError
- Router structure: _svc pattern, DomainValidationError import
- Constants integrity
"""
from __future__ import annotations

import inspect
import pytest
from unittest.mock import patch

import app.modules.facilities_work_orders.service as svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.facilities_work_orders.schemas import (
    WorkOrderCreateSchema,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_work_order_payload(**overrides) -> WorkOrderCreateSchema:
    defaults = {
        "order_code": "WO-001",
        "facility_code": "FAC-A",
        "title": "Fix HVAC",
        "work_type": "maintenance",
        "priority": "high",
        "assigned_to": None,
        "status": "open",
    }
    defaults.update(overrides)
    return WorkOrderCreateSchema(**defaults)


def _make_incident(
    facility_code: str = "FAC-A",
    status: str = "open",
    severity: str = "high",
    incident_code: str = "INC-001",
) -> dict:
    return {
        "id": 1,
        "facility_code": facility_code,
        "status": status,
        "severity": severity,
        "incident_code": incident_code,
    }


def _make_work_order_row(
    priority: str = "high",
    status: str = "open",
    order_id: int = 1,
    facility_code: str = "FAC-A",
) -> dict:
    return {
        "id": order_id,
        "order_code": f"WO-{order_id:03d}",
        "facility_code": facility_code,
        "title": "Test",
        "work_type": "maintenance",
        "priority": priority,
        "status": status,
        "assigned_to": None,
    }


# ===========================================================================
# 1. CONSTANTS
# ===========================================================================

class TestConstants:
    def test_priority_max_open_critical(self):
        assert svc._PRIORITY_MAX_OPEN["critical"] == 3

    def test_priority_max_open_high(self):
        assert svc._PRIORITY_MAX_OPEN["high"] == 10

    def test_priority_max_open_medium(self):
        assert svc._PRIORITY_MAX_OPEN["medium"] == 20

    def test_priority_max_open_low(self):
        assert svc._PRIORITY_MAX_OPEN["low"] == 50

    def test_priority_max_open_is_dict(self):
        assert isinstance(svc._PRIORITY_MAX_OPEN, dict)

    def test_open_statuses_wo_is_frozenset(self):
        assert isinstance(svc._OPEN_STATUSES_WO, frozenset)

    def test_open_statuses_wo_contains_open(self):
        assert "open" in svc._OPEN_STATUSES_WO

    def test_open_statuses_wo_contains_in_progress(self):
        assert "in_progress" in svc._OPEN_STATUSES_WO

    def test_open_statuses_wo_contains_on_hold(self):
        assert "on_hold" in svc._OPEN_STATUSES_WO

    def test_delayed_statuses_is_frozenset(self):
        assert isinstance(svc._DELAYED_WORK_ORDER_STATUSES, frozenset)

    def test_delayed_statuses_contains_on_hold(self):
        assert "on_hold" in svc._DELAYED_WORK_ORDER_STATUSES

    def test_closure_statuses_contains_completed(self):
        assert "completed" in svc._CLOSURE_STATUSES

    def test_closure_statuses_contains_cancelled(self):
        assert "cancelled" in svc._CLOSURE_STATUSES

    def test_blocking_incident_statuses_contains_open(self):
        assert "open" in svc._BLOCKING_SECURITY_INCIDENT_STATUSES

    def test_blocking_incident_statuses_contains_investigating(self):
        assert "investigating" in svc._BLOCKING_SECURITY_INCIDENT_STATUSES

    def test_blocking_incident_severities_contains_high(self):
        assert "high" in svc._BLOCKING_SECURITY_INCIDENT_SEVERITIES

    def test_blocking_incident_severities_contains_critical(self):
        assert "critical" in svc._BLOCKING_SECURITY_INCIDENT_SEVERITIES

    def test_facility_blocking_severities_subset_matches(self):
        # _FACILITY_BLOCKING_SEVERITIES used in W122 guard
        assert "high" in svc._FACILITY_BLOCKING_SEVERITIES
        assert "critical" in svc._FACILITY_BLOCKING_SEVERITIES

    def test_delay_queue_cap_critical(self):
        assert svc._WORK_ORDER_QUEUE_MAX_DELAYED["critical"] == 2

    def test_delay_queue_cap_high(self):
        assert svc._WORK_ORDER_QUEUE_MAX_DELAYED["high"] == 5


# ===========================================================================
# 2. W122 GUARD — create_work_order blocked by security incident
# ===========================================================================

class TestW122Guard:
    """W122: work order creation blocked when facility has active high-severity incident."""

    def test_create_blocked_by_open_high_incident(self):
        incident = _make_incident(status="open", severity="high")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload()
            with pytest.raises(DomainValidationError) as exc_info:
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert "security incident" in str(exc_info.value).lower()

    def test_create_blocked_by_open_critical_incident(self):
        incident = _make_incident(status="open", severity="critical")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload()
            with pytest.raises(DomainValidationError):
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")

    def test_create_blocked_by_investigating_high_incident(self):
        incident = _make_incident(status="investigating", severity="high")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload()
            with pytest.raises(DomainValidationError):
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")

    def test_create_blocked_includes_incident_code_in_message(self):
        incident = _make_incident(status="open", severity="high", incident_code="INC-DANGER")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload()
            with pytest.raises(DomainValidationError) as exc_info:
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert "INC-DANGER" in str(exc_info.value)

    def test_create_allowed_when_resolved_incident(self):
        incident = _make_incident(status="resolved", severity="high")
        wo_row = _make_work_order_row()
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant", return_value={**wo_row, "assigned_to": None}), \
             patch("app.modules.facilities_work_orders.service.log_admin_action"), \
             patch("app.modules.facilities_work_orders.service.EventPublisher"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload()
            result = svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_create_allowed_when_low_severity_incident(self):
        incident = _make_incident(status="open", severity="low")
        wo_row = _make_work_order_row()
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant", return_value={**wo_row, "assigned_to": None}), \
             patch("app.modules.facilities_work_orders.service.log_admin_action"), \
             patch("app.modules.facilities_work_orders.service.EventPublisher"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload()
            result = svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_create_allowed_when_no_incidents(self):
        wo_row = _make_work_order_row()
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant", return_value={**wo_row, "assigned_to": None}), \
             patch("app.modules.facilities_work_orders.service.log_admin_action"), \
             patch("app.modules.facilities_work_orders.service.EventPublisher"):
            mock_list.return_value = []
            payload = _make_work_order_payload()
            result = svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_create_blocked_only_for_matching_facility(self):
        """Incident on different facility should NOT block."""
        incident = _make_incident(facility_code="FAC-Z", status="open", severity="high")
        wo_row = _make_work_order_row(facility_code="FAC-A")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant", return_value={**wo_row, "assigned_to": None}), \
             patch("app.modules.facilities_work_orders.service.log_admin_action"), \
             patch("app.modules.facilities_work_orders.service.EventPublisher"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload(facility_code="FAC-A")
            result = svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_create_blocked_lookup_failure_fail_closed(self):
        """If security_incidents lookup fails, creation must be blocked (fail-closed)."""
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant",
                   side_effect=Exception("DB down")):
            payload = _make_work_order_payload()
            with pytest.raises(DomainValidationError) as exc_info:
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert "fail-closed" in str(exc_info.value).lower() or "cannot" in str(exc_info.value).lower()


# ===========================================================================
# 3. facility_code VALIDATION
# ===========================================================================

class TestFacilityCodeValidation:
    def test_empty_facility_code_raises(self):
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_facility_clear_for_work_order(tenant_id=1, facility_code="")
        assert "facility_code" in str(exc_info.value).lower()

    def test_none_facility_code_raises(self):
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_facility_clear_for_work_order(tenant_id=1, facility_code=None)
        assert "facility_code" in str(exc_info.value).lower()

    def test_whitespace_facility_code_raises(self):
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_facility_clear_for_work_order(tenant_id=1, facility_code="   ")
        assert "facility_code" in str(exc_info.value).lower()


# ===========================================================================
# 4. SLA OPEN CAP
# ===========================================================================

class TestSlaOpenCap:
    def _make_open_rows(self, count: int, priority: str = "critical") -> list[dict]:
        return [_make_work_order_row(priority=priority, status="open", order_id=i) for i in range(1, count + 1)]

    def test_critical_cap_at_3_blocks(self):
        existing = self._make_open_rows(3, "critical")
        incident_free = []
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = existing + incident_free
            # First call (incidents) returns [], second call (existing orders) returns 3 rows
            mock_list.side_effect = [[], existing]
            payload = _make_work_order_payload(priority="critical")
            with pytest.raises(ValueError) as exc_info:
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert "cap" in str(exc_info.value).lower() or "limit" in str(exc_info.value).lower()

    def test_critical_cap_at_2_allows(self):
        existing = self._make_open_rows(2, "critical")
        wo_row = _make_work_order_row(priority="critical", order_id=99)
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant", return_value={**wo_row, "assigned_to": None}), \
             patch("app.modules.facilities_work_orders.service.log_admin_action"), \
             patch("app.modules.facilities_work_orders.service.EventPublisher"):
            # Calls: (1) incidents check, (2) open cap check, (3) delay queue check
            mock_list.side_effect = [[], existing, []]
            payload = _make_work_order_payload(priority="critical")
            result = svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert result is not None

    def test_high_cap_at_10_blocks(self):
        existing = self._make_open_rows(10, "high")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = [[], existing]
            payload = _make_work_order_payload(priority="high")
            with pytest.raises(ValueError):
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")


# ===========================================================================
# 5. DELAY QUEUE CAP
# ===========================================================================

class TestDelayQueueCap:
    def _make_on_hold_rows(self, count: int, priority: str) -> list[dict]:
        return [_make_work_order_row(priority=priority, status="on_hold", order_id=i) for i in range(1, count + 1)]

    def test_critical_delay_cap_at_2_blocks(self):
        on_hold = self._make_on_hold_rows(2, "critical")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            # incident check → [], open cap check → [], delay check → on_hold rows
            mock_list.side_effect = [[], [], on_hold]
            payload = _make_work_order_payload(priority="critical")
            with pytest.raises(ValueError) as exc_info:
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert "delay" in str(exc_info.value).lower() or "cap" in str(exc_info.value).lower()

    def test_high_delay_cap_at_5_blocks(self):
        on_hold = self._make_on_hold_rows(5, "high")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = [[], [], on_hold]
            payload = _make_work_order_payload(priority="high")
            with pytest.raises(ValueError):
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")


# ===========================================================================
# 6. TENANT ISOLATION
# ===========================================================================

class TestTenantIsolation:
    def test_list_work_orders_scoped_by_tenant(self):
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            svc.list_work_orders(tenant_id=42)
            mock_list.assert_called_once_with("facilities_work_orders", 42)

    def test_get_work_order_scoped_by_tenant(self):
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            result = svc.get_work_order(tenant_id=99, order_id=1)
            assert result is None
            mock_list.assert_called_once_with("facilities_work_orders", 99)

    def test_w122_guard_uses_tenant_id(self):
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            try:
                svc._check_facility_clear_for_work_order(tenant_id=77, facility_code="FAC-X")
            except Exception:
                pass
            mock_list.assert_called_with("security_incidents", 77)


# ===========================================================================
# 7. CASE INSENSITIVE FACILITY MATCHING
# ===========================================================================

class TestFacilityCodeCaseInsensitive:
    def test_incident_match_is_case_insensitive(self):
        """Incident with uppercase facility_code should still block."""
        incident = _make_incident(facility_code="FAC-A", status="open", severity="high")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload(facility_code="fac-a")  # lowercase
            with pytest.raises(DomainValidationError):
                svc.create_work_order(tenant_id=1, request=payload, actor="admin")

    def test_different_facility_case_does_not_block(self):
        """Incident on FAC-B must not block work order for FAC-A."""
        incident = _make_incident(facility_code="FAC-B", status="open", severity="critical")
        wo_row = _make_work_order_row()
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list, \
             patch("app.modules.facilities_work_orders.service.create_entity_for_tenant", return_value={**wo_row, "assigned_to": None}), \
             patch("app.modules.facilities_work_orders.service.log_admin_action"), \
             patch("app.modules.facilities_work_orders.service.EventPublisher"):
            mock_list.return_value = [incident]
            payload = _make_work_order_payload(facility_code="FAC-A")
            result = svc.create_work_order(tenant_id=1, request=payload, actor="admin")
            assert result is not None


# ===========================================================================
# 8. CLOSURE GUARD
# ===========================================================================

class TestClosureGuard:
    def test_closure_blocked_by_active_high_incident(self):
        incident = _make_incident(status="open", severity="high")
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant",
                   return_value=[incident]):
            with pytest.raises(DomainValidationError):
                svc._check_no_blocking_security_incidents(
                    tenant_id=1,
                    order_id=1,
                    facility_code="FAC-A",
                    target_status="completed",
                )

    def test_closure_blocked_by_investigating_critical_incident(self):
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant",
                   return_value=[_make_incident(status="investigating", severity="critical")]):
            with pytest.raises(DomainValidationError):
                svc._check_no_blocking_security_incidents(
                    tenant_id=1,
                    order_id=2,
                    facility_code="FAC-A",
                    target_status="cancelled",
                )

    def test_closure_allowed_when_no_blocking_incidents(self):
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant",
                   return_value=[_make_incident(status="resolved", severity="high")]):
            # Should not raise
            svc._check_no_blocking_security_incidents(
                tenant_id=1,
                order_id=3,
                facility_code="FAC-A",
                target_status="completed",
            )

    def test_closure_guard_skips_non_closure_statuses(self):
        """Guard should be no-op for non-closure statuses like 'in_progress'."""
        with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_make_incident(status="open", severity="critical")]
            # Should not raise since 'in_progress' is not in _CLOSURE_STATUSES
            svc._check_no_blocking_security_incidents(
                tenant_id=1,
                order_id=4,
                facility_code="FAC-A",
                target_status="in_progress",
            )
            mock_list.assert_not_called()

    def test_closure_empty_facility_code_raises(self):
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_no_blocking_security_incidents(
                tenant_id=1,
                order_id=5,
                facility_code="",
                target_status="completed",
            )
        assert "facility_code" in str(exc_info.value).lower()


# ===========================================================================
# 9. ROUTER STRUCTURE
# ===========================================================================

class TestRouterStructure:
    def test_router_imports_service_as_svc(self):
        import app.modules.facilities_work_orders.router as router_mod
        assert hasattr(router_mod, "_svc"), "Router must import service as _svc"

    def test_svc_is_service_module(self):
        import app.modules.facilities_work_orders.router as router_mod
        import app.modules.facilities_work_orders.service as svc_mod
        assert router_mod._svc is svc_mod

    def test_router_does_not_import_functions_directly(self):
        """Router must not have top-level function imports from service."""
        import app.modules.facilities_work_orders.router as router_mod
        assert not hasattr(router_mod, "create_work_order"), "Should use _svc.create_work_order"
        assert not hasattr(router_mod, "list_work_orders"), "Should use _svc.list_work_orders"
        assert not hasattr(router_mod, "get_work_order"), "Should use _svc.get_work_order"

    def test_router_has_domain_validation_error_import(self):
        import app.modules.facilities_work_orders.router as router_mod
        assert hasattr(router_mod, "DomainValidationError")

    def test_router_has_work_orders_routes(self):
        import app.modules.facilities_work_orders.router as router_mod
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/facilities/work-orders" in paths

    def test_router_has_maintenance_routes(self):
        import app.modules.facilities_work_orders.router as router_mod
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/facilities/maintenance-requests" in paths

    def test_service_has_check_facility_clear_guard(self):
        assert hasattr(svc, "_check_facility_clear_for_work_order")
        assert callable(svc._check_facility_clear_for_work_order)

    def test_service_has_check_no_blocking_incidents_guard(self):
        assert hasattr(svc, "_check_no_blocking_security_incidents")
        assert callable(svc._check_no_blocking_security_incidents)


# ===========================================================================
# 10. ERROR HANDLING END-TO-END (router layer)
# ===========================================================================

class TestRouterErrorHandling:
    def test_w122_domain_error_maps_to_422(self):
        """DomainValidationError from create_work_order must become 422."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        import app.modules.facilities_work_orders.router as router_mod

        app_instance = FastAPI()
        app_instance.include_router(router_mod.router)

        with patch("app.modules.facilities_work_orders.router._svc.create_work_order",
                   side_effect=DomainValidationError("W122: security incident active")):
            with patch("app.modules.facilities_work_orders.router.get_actor", return_value="admin"), \
                 patch("app.modules.facilities_work_orders.router.permission_dependency", return_value=lambda: None), \
                 patch("app.modules.facilities_work_orders.router.get_current_tenant", return_value=lambda: {"id": 1}):
                TestClient(app_instance, raise_server_exceptions=False)
                # The 422 mapping should be present in the router code
                # Verify via source code inspection
                source = inspect.getsource(router_mod.create_work_order_endpoint)
                assert "422" in source
                assert "DomainValidationError" in source

    def test_value_error_maps_to_422_in_create_work_order(self):
        import app.modules.facilities_work_orders.router as router_mod
        source = inspect.getsource(router_mod.create_work_order_endpoint)
        assert "ValueError" in source
        assert "422" in source

    def test_maintenance_request_endpoint_has_error_handling(self):
        import app.modules.facilities_work_orders.router as router_mod
        source = inspect.getsource(router_mod.create_maintenance_request_endpoint)
        assert "422" in source
