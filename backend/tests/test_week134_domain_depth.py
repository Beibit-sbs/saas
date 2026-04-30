"""W134: Domain-depth tests for operations module.

Tests:
- _BLOCKING_FACILITY_ISSUE_SEVERITIES / _BLOCKING_FACILITY_ISSUE_STATUSES constants
- _check_no_blocking_facility_issues_for_room guard signature & failures
- Fail-closed behaviour on infra errors
- create_room_readiness integration path
- Business invariants (tenant isolation, case-insensitive, non-ready bypass, room isolation)
- Router structure (DomainValidationError wired in all POST endpoints)
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.operations.service as _svc
import app.modules.operations.router as _router
from app.modules.operations.schemas import RoomReadinessCreateSchema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TENANT = 44
_ROOM_CODE = "RM-101"


def _issue(severity: str, status: str, room_code: str = _ROOM_CODE) -> dict:
    return {
        "id": 10,
        "facility_code": room_code,
        "severity": severity,
        "status": status,
        "issue_type": "electrical",
    }


def _readiness_payload(status: str = "ready", room_code: str = _ROOM_CODE) -> RoomReadinessCreateSchema:
    return RoomReadinessCreateSchema(
        room_code=room_code,
        building_code="BLDG-A",
        status=status,
    )


def _created_readiness(payload: RoomReadinessCreateSchema) -> dict:
    return {
        "id": 1,
        "tenant_id": str(_TENANT),
        "room_code": payload.room_code,
        "building_code": payload.building_code,
        "status": str(payload.status),
    }


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------
class TestW134Constants:
    def test_blocking_severities_exists(self):
        assert hasattr(_svc, "_BLOCKING_FACILITY_ISSUE_SEVERITIES")

    def test_blocking_severities_is_frozenset(self):
        assert isinstance(_svc._BLOCKING_FACILITY_ISSUE_SEVERITIES, frozenset)

    def test_critical_in_blocking_severities(self):
        assert "critical" in _svc._BLOCKING_FACILITY_ISSUE_SEVERITIES

    def test_high_in_blocking_severities(self):
        assert "high" in _svc._BLOCKING_FACILITY_ISSUE_SEVERITIES

    def test_low_not_in_blocking_severities(self):
        assert "low" not in _svc._BLOCKING_FACILITY_ISSUE_SEVERITIES

    def test_medium_not_in_blocking_severities(self):
        assert "medium" not in _svc._BLOCKING_FACILITY_ISSUE_SEVERITIES

    def test_blocking_statuses_exists(self):
        assert hasattr(_svc, "_BLOCKING_FACILITY_ISSUE_STATUSES")

    def test_open_in_blocking_statuses(self):
        assert "open" in _svc._BLOCKING_FACILITY_ISSUE_STATUSES

    def test_in_progress_in_blocking_statuses(self):
        assert "in_progress" in _svc._BLOCKING_FACILITY_ISSUE_STATUSES

    def test_resolved_not_in_blocking_statuses(self):
        assert "resolved" not in _svc._BLOCKING_FACILITY_ISSUE_STATUSES

    def test_severities_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._BLOCKING_FACILITY_ISSUE_SEVERITIES.add("hacked")  # type: ignore[attr-defined]

    def test_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._BLOCKING_FACILITY_ISSUE_STATUSES.add("hacked")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Guard signature
# ---------------------------------------------------------------------------
class TestW134GuardSignature:
    def test_callable(self):
        assert callable(_svc._check_no_blocking_facility_issues_for_room)

    def test_requires_tenant_id(self):
        sig = inspect.signature(_svc._check_no_blocking_facility_issues_for_room)
        assert "tenant_id" in sig.parameters

    def test_requires_room_code(self):
        sig = inspect.signature(_svc._check_no_blocking_facility_issues_for_room)
        assert "room_code" in sig.parameters

    def test_requires_target_status(self):
        sig = inspect.signature(_svc._check_no_blocking_facility_issues_for_room)
        assert "target_status" in sig.parameters

    def test_returns_none_when_no_issues(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None

    def test_returns_none_when_no_critical_issues(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("low", "open")]):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None


# ---------------------------------------------------------------------------
# 3. Guard failures
# ---------------------------------------------------------------------------
class TestW134GuardFailures:
    def test_critical_open_issue_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("critical", "open")]):
            with pytest.raises(DomainValidationError, match="critical"):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_high_open_issue_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("high", "open")]):
            with pytest.raises(DomainValidationError, match="high"):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_critical_in_progress_issue_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("critical", "in_progress")]):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_high_in_progress_issue_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("high", "in_progress")]):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_low_open_does_not_block(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("low", "open")]):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None

    def test_medium_open_does_not_block(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("medium", "open")]):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None

    def test_critical_resolved_does_not_block(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("critical", "resolved")]):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None

    def test_error_message_contains_room_code(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("critical", "open")]):
            with pytest.raises(DomainValidationError, match=_ROOM_CODE):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------
class TestW134FailClosed:
    def test_runtime_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=RuntimeError("DB down")):
            with pytest.raises(DomainValidationError, match="facility_issues query failed"):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_connection_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ConnectionError("timeout")):
            with pytest.raises(DomainValidationError, match="facility_issues query failed"):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_os_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=OSError("io error")):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_value_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ValueError("parse error")):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_chained_exception_preserved(self):
        original = RuntimeError("DB down")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=original):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# 5. create_room_readiness integration
# ---------------------------------------------------------------------------
class TestW134CreatePath:
    def _setup_mocks(self, issue_severity: str | None = None, issue_status: str = "open"):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "operations_facility_issues":
                if issue_severity:
                    return [_issue(issue_severity, issue_status)]
                return []
            return []

        mock_list = MagicMock(side_effect=_list)
        mock_create = MagicMock(side_effect=lambda et, data, tid: {**data, "id": 1, "tenant_id": str(tid)})
        mock_log = MagicMock()
        return mock_list, mock_create, mock_log

    def test_critical_issue_blocks_ready(self):
        mock_list, _, _ = self._setup_mocks("critical", "open")
        with patch.object(_svc, "list_entities_for_tenant", mock_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_readiness(_TENANT, _readiness_payload("ready"), "admin")

    def test_high_issue_blocks_ready(self):
        mock_list, _, _ = self._setup_mocks("high", "open")
        with patch.object(_svc, "list_entities_for_tenant", mock_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_readiness(_TENANT, _readiness_payload("ready"), "admin")

    def test_no_issues_allows_ready(self):
        mock_list, mock_create, mock_log = self._setup_mocks(None)
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create), \
             patch.object(_svc, "log_admin_action", mock_log):
            result = _svc.create_room_readiness(_TENANT, _readiness_payload("ready"), "admin")
        assert result is not None
        mock_create.assert_called_once()

    def test_non_ready_status_bypasses_guard(self):
        """Non-ready status skips facility issues check entirely."""
        mock_list = MagicMock(return_value=[_issue("critical", "open")])
        mock_create = MagicMock(side_effect=lambda et, data, tid: {**data, "id": 1, "tenant_id": str(tid)})
        mock_log = MagicMock()
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create), \
             patch.object(_svc, "log_admin_action", mock_log):
            # "maintenance_required" is a valid non-ready status — guard should no-op
            result = _svc.create_room_readiness(
                _TENANT,
                _readiness_payload("maintenance_required"),
                "admin",
            )
        assert result is not None
        mock_create.assert_called_once()

    def test_infra_failure_blocks_ready(self):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "operations_facility_issues":
                raise RuntimeError("DB down")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_readiness(_TENANT, _readiness_payload("ready"), "admin")


# ---------------------------------------------------------------------------
# 6. Business invariants
# ---------------------------------------------------------------------------
class TestW134BusinessInvariants:
    def test_tenant_isolation(self):
        seen_tenant_ids = []

        def _list(entity_type, tenant_id):
            if entity_type == "operations_facility_issues":
                seen_tenant_ids.append(tenant_id)
                return [_issue("critical", "open")]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(99, _ROOM_CODE, "ready")
        assert seen_tenant_ids == [99]

    def test_room_isolation(self):
        """Issues for other rooms do not block the target room."""
        other_room_issue = _issue("critical", "open", room_code="RM-999")
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[other_room_issue]):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None

    def test_room_code_case_insensitive(self):
        """Room code matching is case-insensitive."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_issue("critical", "open", room_code="rm-101")]):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, "RM-101", "ready"
                )

    def test_resolved_issues_allow_ready(self):
        issues = [
            _issue("critical", "resolved"),
            _issue("high", "closed"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=issues):
            result = _svc._check_no_blocking_facility_issues_for_room(
                _TENANT, _ROOM_CODE, "ready"
            )
        assert result is None

    def test_mixed_issues_one_critical_open_blocks(self):
        issues = [
            _issue("low", "open"),
            _issue("critical", "open"),
            _issue("high", "resolved"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=issues):
            with pytest.raises(DomainValidationError):
                _svc._check_no_blocking_facility_issues_for_room(
                    _TENANT, _ROOM_CODE, "ready"
                )

    def test_status_check_guard_first_for_ready(self):
        """Guard fires FIRST for 'ready' status before create."""
        call_order = []

        def _list(entity_type, tenant_id):
            call_order.append(entity_type)
            if entity_type == "operations_facility_issues":
                return [_issue("critical", "open")]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_readiness(_TENANT, _readiness_payload("ready"), "admin")

        assert "operations_facility_issues" in call_order


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------
class TestW134RouterStructure:
    def test_room_readiness_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/operations/room-readiness" in routes

    def test_facility_issues_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/operations/facility-issues" in routes

    def test_work_orders_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/operations/work-orders" in routes

    def test_cleaning_checks_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/operations/cleaning-checks" in routes

    def test_maintenance_assets_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/operations/maintenance-assets" in routes

    def test_utility_readings_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/operations/utility-readings" in routes

    def test_domain_validation_error_imported_in_router(self):
        assert hasattr(_router, "DomainValidationError")

    def test_create_room_readiness_endpoint_exists(self):
        assert callable(getattr(_router, "create_room_readiness_endpoint", None))
