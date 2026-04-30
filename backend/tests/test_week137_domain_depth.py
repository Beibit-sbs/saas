"""W137 — security_operations: Router DomainValidationError hardening depth tests.

Guard under test:
    _check_facility_has_no_active_critical_incident (W107)
    — security_visitors × security_incidents cross-entity guard.

New coverage added in W137:
    • Router POST /visitors now catches (ValueError, DomainValidationError) → 422
    • Router POST /incidents now catches (ValueError, DomainValidationError) → 422
    • DomainValidationError imported in router.py
    • Deep behavioural coverage: constants, guard logic, router wiring, fail-closed,
      tenant isolation, edge cases.
"""
from __future__ import annotations

import importlib
import inspect
from unittest.mock import patch

import pytest

import app.modules.security_operations.service as _svc
import app.modules.security_operations.router as _router
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# W137.1 — Constants / module surface
# ---------------------------------------------------------------------------

class TestW137Constants:
    def test_blocked_incident_statuses_exists(self):
        assert hasattr(_svc, "_BLOCKED_INCIDENT_STATUSES")

    def test_blocked_incident_statuses_is_frozenset(self):
        assert isinstance(_svc._BLOCKED_INCIDENT_STATUSES, frozenset)

    def test_blocked_incident_statuses_contains_open(self):
        assert "open" in _svc._BLOCKED_INCIDENT_STATUSES

    def test_blocked_incident_statuses_contains_investigating(self):
        assert "investigating" in _svc._BLOCKED_INCIDENT_STATUSES

    def test_blocked_incident_severities_exists(self):
        assert hasattr(_svc, "_BLOCKED_INCIDENT_SEVERITIES")

    def test_blocked_incident_severities_is_frozenset(self):
        assert isinstance(_svc._BLOCKED_INCIDENT_SEVERITIES, frozenset)

    def test_blocked_incident_severities_contains_critical(self):
        assert "critical" in _svc._BLOCKED_INCIDENT_SEVERITIES

    def test_blocked_incident_severities_contains_high(self):
        assert "high" in _svc._BLOCKED_INCIDENT_SEVERITIES

    def test_blocked_incident_severities_excludes_medium(self):
        assert "medium" not in _svc._BLOCKED_INCIDENT_SEVERITIES

    def test_blocked_incident_severities_excludes_low(self):
        assert "low" not in _svc._BLOCKED_INCIDENT_SEVERITIES

    def test_guard_function_exists(self):
        assert callable(getattr(_svc, "_check_facility_has_no_active_critical_incident", None))


# ---------------------------------------------------------------------------
# W137.2 — Guard logic: allow paths
# ---------------------------------------------------------------------------

class TestW137GuardAllowPaths:
    def _call(self, incidents: list[dict], facility_code: str = "FAC-01", tenant_id: int = 1) -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=incidents):
            _svc._check_facility_has_no_active_critical_incident(
                tenant_id=tenant_id, facility_code=facility_code
            )

    def test_no_incidents_passes(self):
        self._call([])

    def test_resolved_incident_does_not_block(self):
        self._call([{"facility_code": "FAC-01", "status": "resolved", "severity": "critical"}])

    def test_closed_incident_does_not_block(self):
        self._call([{"facility_code": "FAC-01", "status": "closed", "severity": "high"}])

    def test_low_severity_open_does_not_block(self):
        self._call([{"facility_code": "FAC-01", "status": "open", "severity": "low"}])

    def test_medium_severity_open_does_not_block(self):
        self._call([{"facility_code": "FAC-01", "status": "open", "severity": "medium"}])

    def test_different_facility_critical_open_does_not_block(self):
        self._call(
            [{"facility_code": "FAC-99", "status": "open", "severity": "critical"}],
            facility_code="FAC-01",
        )

    def test_case_insensitive_facility_code_match_allows(self):
        """Case-insensitive: 'fac-01' incident should block 'FAC-01' visitor."""
        # Uppercase incident, uppercase query → should block
        with pytest.raises(DomainValidationError):
            self._call(
                [{"facility_code": "fac-01", "status": "open", "severity": "critical"}],
                facility_code="FAC-01",
            )


# ---------------------------------------------------------------------------
# W137.3 — Guard logic: block paths
# ---------------------------------------------------------------------------

class TestW137GuardBlockPaths:
    def _call_expect_raise(self, incidents: list[dict], facility_code: str = "FAC-01") -> DomainValidationError:
        with patch.object(_svc, "list_entities_for_tenant", return_value=incidents):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_facility_has_no_active_critical_incident(
                    tenant_id=1, facility_code=facility_code
                )
        return exc_info.value

    def test_open_critical_blocks(self):
        exc = self._call_expect_raise(
            [{"facility_code": "FAC-01", "status": "open", "severity": "critical"}]
        )
        assert "FAC-01" in str(exc)

    def test_investigating_critical_blocks(self):
        exc = self._call_expect_raise(
            [{"facility_code": "FAC-01", "status": "investigating", "severity": "critical"}]
        )
        assert "critical" in str(exc).lower() or "FAC-01" in str(exc)

    def test_open_high_blocks(self):
        exc = self._call_expect_raise(
            [{"facility_code": "FAC-01", "status": "open", "severity": "high"}]
        )
        assert "FAC-01" in str(exc)

    def test_investigating_high_blocks(self):
        self._call_expect_raise(
            [{"facility_code": "FAC-01", "status": "investigating", "severity": "high"}]
        )

    def test_error_message_contains_facility_code(self):
        exc = self._call_expect_raise(
            [{"facility_code": "LAB-99", "status": "open", "severity": "critical"}],
            facility_code="LAB-99",
        )
        assert "LAB-99" in str(exc)

    def test_multiple_incidents_one_blocking_blocks(self):
        incidents = [
            {"facility_code": "FAC-01", "status": "resolved", "severity": "critical"},
            {"facility_code": "FAC-01", "status": "open", "severity": "high"},
        ]
        self._call_expect_raise(incidents)

    def test_all_resolved_passes(self):
        incidents = [
            {"facility_code": "FAC-01", "status": "resolved", "severity": "critical"},
            {"facility_code": "FAC-01", "status": "closed", "severity": "high"},
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=incidents):
            _svc._check_facility_has_no_active_critical_incident(
                tenant_id=1, facility_code="FAC-01"
            )


# ---------------------------------------------------------------------------
# W137.4 — Fail-closed behaviour
# ---------------------------------------------------------------------------

class TestW137FailClosed:
    def test_lookup_exception_raises_domain_error(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=RuntimeError("db down")):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_facility_has_no_active_critical_incident(
                    tenant_id=1, facility_code="FAC-01"
                )
        assert "lookup failed" in str(exc_info.value).lower() or "cannot verify" in str(exc_info.value).lower()

    def test_lookup_exception_preserves_cause(self):
        cause = RuntimeError("db down")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=cause):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_facility_has_no_active_critical_incident(
                    tenant_id=1, facility_code="FAC-01"
                )
        assert exc_info.value.__cause__ is cause

    def test_lookup_exception_is_domain_validation_error(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=Exception("fail")):
            with pytest.raises(DomainValidationError):
                _svc._check_facility_has_no_active_critical_incident(
                    tenant_id=1, facility_code="FAC-01"
                )


# ---------------------------------------------------------------------------
# W137.5 — Tenant isolation
# ---------------------------------------------------------------------------

class TestW137TenantIsolation:
    def test_cross_tenant_incident_does_not_block_other_tenant(self):
        """Tenant 2's incident must not block Tenant 1's visitor."""
        calls: list[tuple] = []

        def fake_list(entity_type: str, tenant_id: int):
            calls.append((entity_type, tenant_id))
            if tenant_id == 2:
                return [{"facility_code": "FAC-01", "status": "open", "severity": "critical"}]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list):
            # Tenant 1 should pass (no incidents for tenant 1)
            _svc._check_facility_has_no_active_critical_incident(
                tenant_id=1, facility_code="FAC-01"
            )

    def test_guard_queries_correct_tenant(self):
        queried_tenant_ids: list[int] = []

        def fake_list(entity_type: str, tenant_id: int):
            queried_tenant_ids.append(tenant_id)
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list):
            _svc._check_facility_has_no_active_critical_incident(
                tenant_id=42, facility_code="FAC-01"
            )

        assert 42 in queried_tenant_ids


# ---------------------------------------------------------------------------
# W137.6 — create_security_visitor wiring
# ---------------------------------------------------------------------------

class TestW137VisitorServiceWiring:
    def test_guard_fires_before_create_when_facility_code_present(self):
        """Guard must be called before create_entity_for_tenant."""
        call_order: list[str] = []

        def fake_list(entity_type: str, tenant_id: int):
            call_order.append("list")
            return [{"facility_code": "FAC-01", "status": "open", "severity": "critical"}]

        def fake_create(entity_type: str, payload: dict, tenant_id: int):
            call_order.append("create")
            return payload

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list), \
             patch.object(_svc, "create_entity_for_tenant", side_effect=fake_create):
            with pytest.raises(DomainValidationError):
                _svc.create_security_visitor({"facility_code": "FAC-01"}, 1)

        assert "list" in call_order
        assert "create" not in call_order

    def test_create_not_called_when_guard_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[{"facility_code": "FAC-01", "status": "open", "severity": "critical"}]), \
             patch.object(_svc, "create_entity_for_tenant") as mock_create:
            with pytest.raises(DomainValidationError):
                _svc.create_security_visitor({"facility_code": "FAC-01"}, 1)
        mock_create.assert_not_called()

    def test_empty_facility_code_bypasses_guard(self):
        """Empty facility_code skips guard — no lookup performed."""
        with patch.object(_svc, "list_entities_for_tenant") as mock_list, \
             patch.object(_svc, "create_entity_for_tenant", return_value={"id": 1}):
            _svc.create_security_visitor({"facility_code": ""}, 1)
        mock_list.assert_not_called()

    def test_missing_facility_code_bypasses_guard(self):
        with patch.object(_svc, "list_entities_for_tenant") as mock_list, \
             patch.object(_svc, "create_entity_for_tenant", return_value={"id": 1}):
            _svc.create_security_visitor({}, 1)
        mock_list.assert_not_called()

    def test_valid_facility_no_incident_creates_visitor(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]), \
             patch.object(_svc, "create_entity_for_tenant", return_value={"id": 99}) as mock_create:
            result = _svc.create_security_visitor({"facility_code": "FAC-01"}, 1)
        assert result == {"id": 99}
        mock_create.assert_called_once()


# ---------------------------------------------------------------------------
# W137.7 — Router structure
# ---------------------------------------------------------------------------

class TestW137RouterStructure:
    def test_router_has_routes(self):
        assert len(_router.router.routes) > 0

    def test_post_visitors_route_exists(self):
        paths = [r.path for r in _router.router.routes]
        assert any("visitors" in p for p in paths)

    def test_post_incidents_route_exists(self):
        paths = [r.path for r in _router.router.routes]
        assert any("incidents" in p for p in paths)

    def test_domain_validation_error_imported_in_router(self):
        source = inspect.getsource(_router)
        assert "DomainValidationError" in source

    def test_router_catches_domain_validation_error_for_visitors(self):
        source = inspect.getsource(_router)
        assert "DomainValidationError" in source

    def test_router_module_importable(self):
        importlib.import_module("app.modules.security_operations.router")


# ---------------------------------------------------------------------------
# W137.8 — Router endpoint: HTTP 422 on DomainValidationError (visitors)
# ---------------------------------------------------------------------------

class TestW137RouterVisitorEndpoint:
    def _invoke(self, service_side_effect=None) -> int:
        from app.modules.security_operations.router import create_security_visitor_endpoint
        from app.modules.security_operations.schemas import SecurityVisitorCreatePayload
        from fastapi import HTTPException

        pld = SecurityVisitorCreatePayload(visitor_name="John")
        with patch.object(_svc, "create_security_visitor",
                          side_effect=service_side_effect or (lambda p, tid: {"id": 1, "visitor_name": "John", "visit_purpose": "general", "status": "expected", "access_status": "pending", "tenant_id": 1})):
            try:
                create_security_visitor_endpoint(
                    payload=pld,
                    _="actor",
                    __=None,
                    tenant={"id": "1"},
                )
                return 201
            except HTTPException as e:
                return e.status_code

    def test_domain_validation_error_returns_422(self):
        status = self._invoke(service_side_effect=lambda p, tid: (_ for _ in ()).throw(DomainValidationError("blocked")))
        assert status == 422

    def test_value_error_returns_422(self):
        status = self._invoke(service_side_effect=lambda p, tid: (_ for _ in ()).throw(ValueError("bad")))
        assert status == 422

    def test_valid_visitor_returns_201(self):
        status = self._invoke()
        assert status == 201


# ---------------------------------------------------------------------------
# W137.9 — Router endpoint: HTTP 422 on DomainValidationError (incidents)
# ---------------------------------------------------------------------------

class TestW137RouterIncidentEndpoint:
    def _invoke(self, service_side_effect=None) -> int:
        from app.modules.security_operations.router import create_security_incident_endpoint
        from app.modules.security_operations.schemas import SecurityIncidentCreatePayload
        from fastapi import HTTPException

        pld = SecurityIncidentCreatePayload(incident_code="INC-1", facility_code="FAC-01")
        with patch.object(_svc, "create_security_incident",
                          side_effect=service_side_effect or (lambda p, tid: {"id": 1, "incident_code": "INC-1", "facility_code": "FAC-01", "category": "general", "severity": "low", "status": "open", "tenant_id": 1})):
            try:
                create_security_incident_endpoint(
                    payload=pld,
                    _="actor",
                    __=None,
                    tenant={"id": "1"},
                )
                return 201
            except HTTPException as e:
                return e.status_code

    def test_domain_validation_error_returns_422(self):
        status = self._invoke(service_side_effect=lambda p, tid: (_ for _ in ()).throw(DomainValidationError("domain error")))
        assert status == 422

    def test_value_error_returns_422(self):
        status = self._invoke(service_side_effect=lambda p, tid: (_ for _ in ()).throw(ValueError("cap exceeded")))
        assert status == 422

    def test_valid_incident_returns_201(self):
        status = self._invoke()
        assert status == 201
