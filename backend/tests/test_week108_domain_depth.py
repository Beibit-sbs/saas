"""W108 — Housing: Room Assignment Availability Guard (cross-entity: housing_room_assignments × housing_rooms).

Business invariant: A student can only be assigned to a room that exists, is active,
and has available occupancy.

Bad outcomes if guard is missing:
  - Multiple students assigned to same room (double occupancy)
  - Students assigned to maintenance/closed/non-functional rooms
  - Phantom housing records during room unavailability
  - Housing utilisation analytics corrupted (double-count occupancy)
  - Cascade failures in room allocation system

Guard location: housing/service.py :: create_room_assignment() → _check_room_is_assignable()
                BEFORE create_entity_for_tenant("housing_room_assignments", ...)
"""
from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
SERVICE_MODULE = "app.modules.housing.service"


def _svc():
    """Return freshly imported service module."""
    return importlib.import_module(SERVICE_MODULE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_room(room_code: str, status: str, occupancy: str, **extra) -> dict:
    return {
        "id": 1,
        "room_code": room_code,
        "status": status,
        "occupancy": occupancy,
        **extra,
    }


def _assignment_payload(room_code: str = "ROOM-101") -> dict:
    return {"room_code": room_code, "student_id": 1, "semester": "fall_2024"}


TENANT = 42

# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestW108Constants:
    def test_assignable_room_statuses_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_ASSIGNABLE_ROOM_STATUSES")

    def test_assignable_room_statuses_is_frozenset(self):
        svc = _svc()
        assert isinstance(svc._ASSIGNABLE_ROOM_STATUSES, frozenset)

    def test_assignable_room_statuses_contains_active(self):
        svc = _svc()
        assert "active" in svc._ASSIGNABLE_ROOM_STATUSES

    def test_assignable_room_occupancy_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_ASSIGNABLE_ROOM_OCCUPANCY")

    def test_assignable_room_occupancy_is_frozenset(self):
        svc = _svc()
        assert isinstance(svc._ASSIGNABLE_ROOM_OCCUPANCY, frozenset)

    def test_assignable_room_occupancy_contains_available(self):
        svc = _svc()
        assert "available" in svc._ASSIGNABLE_ROOM_OCCUPANCY

    def test_assignable_room_occupancy_does_not_contain_occupied(self):
        svc = _svc()
        assert "occupied" not in svc._ASSIGNABLE_ROOM_OCCUPANCY


# ---------------------------------------------------------------------------
# 2. Guard unit tests (_check_room_is_assignable)
# ---------------------------------------------------------------------------

class TestCheckRoomIsAssignable:
    def _call(self, rooms: list[dict], room_code: str = "ROOM-101"):
        from app.modules.housing.service import _check_room_is_assignable

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=rooms,
        ):
            return _check_room_is_assignable(tenant_id=TENANT, room_code=room_code)

    def test_passes_active_available_room_exists(self):
        """Guard passes: room exists with status 'active' and occupancy 'available'."""
        self._call([_make_room("ROOM-101", "active", "available")])

    def test_passes_other_room_exists_different_code(self):
        """Guard passes: another room exists but different code, and both are active/available."""
        self._call(
            [
                _make_room("ROOM-999", "active", "available"),
                _make_room("ROOM-101", "active", "available"),
            ]
        )

    def test_blocks_room_not_found(self):
        """Guard blocks: no room with the given code exists."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant", return_value=[]
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="MISSING-101")

    def test_blocks_room_maintenance_status(self):
        """Guard blocks: room exists but status='maintenance'."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "maintenance", "available")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_blocks_room_closed_status(self):
        """Guard blocks: room exists but status='closed'."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "closed", "available")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_blocks_room_reserved_status(self):
        """Guard blocks: room exists but status='reserved'."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "reserved", "available")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_blocks_room_occupied_occupancy(self):
        """Guard blocks: room exists, active, but occupancy='occupied'."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "active", "occupied")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_blocks_room_reserved_occupancy(self):
        """Guard blocks: room exists, active, but occupancy='reserved'."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "active", "reserved")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_room_code_match_is_case_insensitive(self):
        """Guard: room_code matching is case-insensitive."""
        self._call([_make_room("ROOM-101", "active", "available")], room_code="room-101")

    def test_fail_closed_lookup_error_raises_domain_error(self):
        """FAIL-CLOSED: if list_entities_for_tenant raises, guard raises DomainValidationError."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            side_effect=RuntimeError("db timeout"),
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_error_message_contains_room_code_on_not_found(self):
        """Error message must reference the room_code for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch("app.modules.housing.service.list_entities_for_tenant", return_value=[]):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError, match="ROOM-XYZ"):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-XYZ")

    def test_error_message_contains_status_on_wrong_status(self):
        """Error message must state the actual room status for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "maintenance", "available")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError, match="maintenance"):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")

    def test_error_message_contains_occupancy_on_wrong_occupancy(self):
        """Error message must state the actual occupancy for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.housing.service.list_entities_for_tenant",
            return_value=[_make_room("ROOM-101", "active", "occupied")],
        ):
            from app.modules.housing.service import _check_room_is_assignable

            with pytest.raises(DomainValidationError, match="occupied"):
                _check_room_is_assignable(tenant_id=TENANT, room_code="ROOM-101")


# ---------------------------------------------------------------------------
# 3. Integration: create_room_assignment wires the guard
# ---------------------------------------------------------------------------

class TestCreateRoomAssignmentGuard:
    def _run(
        self,
        rooms: list[dict],
        payload: dict | None = None,
        create_return: dict | None = None,
    ) -> tuple[object, MagicMock]:
        from app.modules.housing.service import create_room_assignment

        _payload = payload or _assignment_payload()
        _create_ret = create_return or {"id": 99, **_payload}

        mock_create = MagicMock(return_value=_create_ret)
        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant", return_value=rooms
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant", mock_create
            ),
        ):
            result = create_room_assignment(_payload, TENANT)
        return result, mock_create

    def test_assignment_allowed_active_available_room(self):
        """create_room_assignment succeeds with existing active+available room."""
        result, mock_create = self._run([_make_room("ROOM-101", "active", "available")])
        mock_create.assert_called_once()

    def test_assignment_blocked_maintenance_room(self):
        """create_room_assignment raises for maintenance room — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.housing.service import create_room_assignment

        mock_create = MagicMock()
        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant",
                return_value=[_make_room("ROOM-101", "maintenance", "available")],
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant", mock_create
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_room_assignment(_assignment_payload(), TENANT)

        mock_create.assert_not_called()

    def test_assignment_blocked_occupied_room(self):
        """create_room_assignment raises for occupied room — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.housing.service import create_room_assignment

        mock_create = MagicMock()
        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant",
                return_value=[_make_room("ROOM-101", "active", "occupied")],
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant", mock_create
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_room_assignment(_assignment_payload(), TENANT)

        mock_create.assert_not_called()

    def test_assignment_blocked_room_not_found(self):
        """create_room_assignment raises when room_code not found — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.housing.service import create_room_assignment

        mock_create = MagicMock()
        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant", return_value=[]
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant", mock_create
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_room_assignment(_assignment_payload("GHOST-ROOM"), TENANT)

        mock_create.assert_not_called()

    def test_guard_fires_before_persist(self):
        """Guard is invoked BEFORE create_entity_for_tenant — persist never called on block."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.housing.service import create_room_assignment

        call_order: list[str] = []

        def fake_list(table, tid):
            call_order.append("list")
            return [_make_room("ROOM-101", "maintenance", "available")]

        def fake_create(table, payload, tid):
            call_order.append("create")
            return payload

        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant", side_effect=fake_list
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant", side_effect=fake_create
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_room_assignment(_assignment_payload(), TENANT)

        assert "list" in call_order
        assert "create" not in call_order

    def test_no_room_code_in_payload_skips_guard(self):
        """If room_code is absent from payload, guard is skipped (no breakage)."""
        from app.modules.housing.service import create_room_assignment

        mock_create = MagicMock(return_value={"id": 1})
        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant", return_value=[]
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant", mock_create
            ),
        ):
            create_room_assignment({"student_id": 1}, TENANT)

        mock_create.assert_called_once()

    def test_multiple_rooms_first_blocking_one_cited(self):
        """Error message cites first blocking room found."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.housing.service import create_room_assignment

        with (
            patch(
                "app.modules.housing.service.list_entities_for_tenant",
                return_value=[
                    _make_room("ROOM-101", "maintenance", "available"),
                    _make_room("ROOM-101", "closed", "available"),
                ],
            ),
            patch(
                "app.modules.housing.service.create_entity_for_tenant",
                return_value={"id": 1},
            ),
        ):
            with pytest.raises(DomainValidationError, match="maintenance"):
                create_room_assignment(_assignment_payload(), TENANT)
