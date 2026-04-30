"""W136: Domain-depth tests for housing module.

Tests:
- Constants: _ASSIGNABLE_ROOM_STATUSES, _ASSIGNABLE_ROOM_OCCUPANCY
- _check_room_is_assignable guard signature & failures
- Fail-closed on infra errors
- create_room_assignment integration path
- _check_no_active_room_assignment (W86 guard)
- Business invariants (tenant isolation, case-insensitive, room isolation)
- Router structure (DomainValidationError wired)
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.housing.service as _svc
import app.modules.housing.router as _router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TENANT = 66
_ROOM_CODE = "DORM-A-101"
_STUDENT_ID = 777


def _room(room_code: str = _ROOM_CODE, status: str = "active", occupancy: str = "available") -> dict:
    return {
        "id": 1,
        "room_code": room_code,
        "status": status,
        "occupancy": occupancy,
        "building_code": "DORM-A",
    }


def _assignment(student_id: int = _STUDENT_ID, status: str = "assigned") -> dict:
    return {
        "id": 10,
        "student_id": student_id,
        "status": status,
        "room_code": _ROOM_CODE,
        "integration_source": "housing_approval",
        "source_entity_id": "100",
    }


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------
class TestW136Constants:
    def test_assignable_room_statuses_exists(self):
        assert hasattr(_svc, "_ASSIGNABLE_ROOM_STATUSES")

    def test_assignable_room_statuses_is_frozenset(self):
        assert isinstance(_svc._ASSIGNABLE_ROOM_STATUSES, frozenset)

    def test_active_in_assignable_statuses(self):
        assert "active" in _svc._ASSIGNABLE_ROOM_STATUSES

    def test_maintenance_not_in_assignable_statuses(self):
        assert "maintenance" not in _svc._ASSIGNABLE_ROOM_STATUSES

    def test_closed_not_in_assignable_statuses(self):
        assert "closed" not in _svc._ASSIGNABLE_ROOM_STATUSES

    def test_assignable_room_occupancy_exists(self):
        assert hasattr(_svc, "_ASSIGNABLE_ROOM_OCCUPANCY")

    def test_available_in_assignable_occupancy(self):
        assert "available" in _svc._ASSIGNABLE_ROOM_OCCUPANCY

    def test_occupied_not_in_assignable_occupancy(self):
        assert "occupied" not in _svc._ASSIGNABLE_ROOM_OCCUPANCY

    def test_assignable_room_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._ASSIGNABLE_ROOM_STATUSES.add("hacked")  # type: ignore[attr-defined]

    def test_assignable_room_occupancy_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._ASSIGNABLE_ROOM_OCCUPANCY.add("hacked")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Guard signature
# ---------------------------------------------------------------------------
class TestW136GuardSignature:
    def test_callable(self):
        assert callable(_svc._check_room_is_assignable)

    def test_requires_tenant_id(self):
        sig = inspect.signature(_svc._check_room_is_assignable)
        assert "tenant_id" in sig.parameters

    def test_requires_room_code(self):
        sig = inspect.signature(_svc._check_room_is_assignable)
        assert "room_code" in sig.parameters

    def test_returns_none_when_active_available(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="active", occupancy="available")]):
            result = _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)
        assert result is None


# ---------------------------------------------------------------------------
# 3. Guard failures
# ---------------------------------------------------------------------------
class TestW136GuardFailures:
    def test_room_not_found_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="not found"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_maintenance_status_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="maintenance")]):
            with pytest.raises(DomainValidationError, match="maintenance"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_closed_status_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="closed")]):
            with pytest.raises(DomainValidationError, match="closed"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_occupied_room_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="active", occupancy="occupied")]):
            with pytest.raises(DomainValidationError, match="occupied"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_reserved_occupancy_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="active", occupancy="reserved")]):
            with pytest.raises(DomainValidationError):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_error_message_contains_room_code(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match=_ROOM_CODE):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_reserved_status_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="reserved")]):
            with pytest.raises(DomainValidationError):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------
class TestW136FailClosed:
    def test_runtime_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=RuntimeError("DB down")):
            with pytest.raises(DomainValidationError, match="room lookup failed"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_connection_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ConnectionError("timeout")):
            with pytest.raises(DomainValidationError, match="room lookup failed"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_os_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=OSError("io error")):
            with pytest.raises(DomainValidationError):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_value_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ValueError("parse error")):
            with pytest.raises(DomainValidationError):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_chained_exception_preserved(self):
        original = RuntimeError("storage failure")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=original):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# 5. create_room_assignment integration
# ---------------------------------------------------------------------------
class TestW136CreateRoomAssignment:
    def _mk_list(self, rooms: list[dict]):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "housing_rooms":
                return rooms
            return []
        return MagicMock(side_effect=_list)

    def _mk_create(self):
        return MagicMock(side_effect=lambda et, data, tid: {**data, "id": 1, "tenant_id": str(tid)})

    def test_active_available_room_creates(self):
        mock_list = self._mk_list([_room(status="active", occupancy="available")])
        mock_create = self._mk_create()
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_room_assignment(
                {"room_code": _ROOM_CODE, "student_id": _STUDENT_ID}, _TENANT
            )
        assert result is not None
        mock_create.assert_called_once()

    def test_maintenance_room_blocks_assignment(self):
        mock_list = self._mk_list([_room(status="maintenance")])
        with patch.object(_svc, "list_entities_for_tenant", mock_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_assignment(
                    {"room_code": _ROOM_CODE, "student_id": _STUDENT_ID}, _TENANT
                )

    def test_occupied_room_blocks_assignment(self):
        mock_list = self._mk_list([_room(status="active", occupancy="occupied")])
        with patch.object(_svc, "list_entities_for_tenant", mock_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_assignment(
                    {"room_code": _ROOM_CODE, "student_id": _STUDENT_ID}, _TENANT
                )

    def test_empty_room_code_bypasses_guard(self):
        """Empty room_code skips the guard."""
        mock_create = self._mk_create()
        with patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_room_assignment(
                {"room_code": "", "student_id": _STUDENT_ID}, _TENANT
            )
        assert result is not None
        mock_create.assert_called_once()

    def test_infra_failure_blocks(self):
        def _list(entity_type, tenant_id):
            if entity_type == "housing_rooms":
                raise RuntimeError("DB down")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_room_assignment(
                    {"room_code": _ROOM_CODE, "student_id": _STUDENT_ID}, _TENANT
                )

    def test_guard_fires_before_create(self):
        mock_list = MagicMock(return_value=[_room(status="closed")])
        mock_create = MagicMock()
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            with pytest.raises(DomainValidationError):
                _svc.create_room_assignment(
                    {"room_code": _ROOM_CODE, "student_id": _STUDENT_ID}, _TENANT
                )
        mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# 6. Business invariants
# ---------------------------------------------------------------------------
class TestW136BusinessInvariants:
    def test_tenant_isolation(self):
        seen_tenant_ids = []

        def _list(entity_type, tenant_id):
            if entity_type == "housing_rooms":
                seen_tenant_ids.append(tenant_id)
                return []
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc._check_room_is_assignable(tenant_id=99, room_code=_ROOM_CODE)
        assert seen_tenant_ids == [99]

    def test_room_code_case_insensitive(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(room_code="dorm-a-101", status="active", occupancy="available")]):
            result = _svc._check_room_is_assignable(tenant_id=_TENANT, room_code="DORM-A-101")
        assert result is None

    def test_different_room_code_not_matched(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(room_code="DORM-B-999", status="active", occupancy="available")]):
            with pytest.raises(DomainValidationError, match="not found"):
                _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)

    def test_w86_active_assignment_blocks_approval(self):
        """W86: student with active assignment cannot be approved for new one."""
        existing_assignments = [_assignment(student_id=_STUDENT_ID, status="assigned")]

        def _list(entity_type, tenant_id):
            if entity_type == "room_assignment_records":
                return existing_assignments
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError, match="already has an active"):
                _svc._check_no_active_room_assignment(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, request_id=200
                )

    def test_w86_no_active_assignment_allows_approval(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            result = _svc._check_no_active_room_assignment(
                tenant_id=_TENANT, student_id=_STUDENT_ID, request_id=200
            )
        assert result is None

    def test_w86_completed_assignment_does_not_block(self):
        existing_assignments = [_assignment(student_id=_STUDENT_ID, status="completed")]

        with patch.object(_svc, "list_entities_for_tenant", return_value=existing_assignments):
            result = _svc._check_no_active_room_assignment(
                tenant_id=_TENANT, student_id=_STUDENT_ID, request_id=200
            )
        assert result is None

    def test_room_status_whitespace_trimmed(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_room(status="  active  ", occupancy="  available  ")]):
            result = _svc._check_room_is_assignable(tenant_id=_TENANT, room_code=_ROOM_CODE)
        assert result is None


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------
# NOTE: `import app.modules.housing.router as _router` resolves to the APIRouter
# object (not the module) due to package-level re-export. Tests are adapted accordingly.

class TestW136RouterStructure:
    def test_post_route_exists(self):
        routes = {r.path for r in _router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/housing" in routes

    def test_patch_status_route_exists(self):
        routes = {r.path for r in _router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/housing/{request_id}/status" in routes

    def test_housing_router_has_routes(self):
        assert len(_router.routes) > 0  # type: ignore[attr-defined]

    def test_domain_validation_error_importable(self):
        """DomainValidationError is importable — used in the router."""
        from app.core.module_helpers.service_validation import DomainValidationError
        assert DomainValidationError is not None

    def test_create_request_endpoint_in_routes(self):
        """Verify the POST / endpoint handler exists by route method."""
        post_routes = [r for r in _router.routes if "POST" in getattr(r, "methods", set())]  # type: ignore[attr-defined]
        assert len(post_routes) >= 1

    def test_patch_status_endpoint_in_routes(self):
        """Verify the PATCH /{id}/status route exists."""
        patch_routes = [r for r in _router.routes if "PATCH" in getattr(r, "methods", set())]  # type: ignore[attr-defined]
        assert len(patch_routes) >= 1
