"""W152 — equipment_booking: deep domain hardening pack.

W119 guard coverage:
- create blocked unless requester has active enrollment
- fail-closed on student_enrollments lookup errors
- validate-before-persist for create_equipment_booking
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.equipment_booking.service as svc


ACTIVE_ENROLLMENT = {"student_id": "STU-001", "status": "active", "tenant_id": 1}
ENROLLED_ENROLLMENT = {"student_id": "STU-002", "status": "enrolled", "tenant_id": 1}
WITHDRAWN_ENROLLMENT = {"student_id": "STU-003", "status": "withdrawn", "tenant_id": 1}
EXPELLED_ENROLLMENT = {"student_id": "STU-004", "status": "expelled", "tenant_id": 1}

GOOD_EQUIPMENT = {
    "id": 10,
    "equipment_code": "EQ-001",
    "status": "available",
    "tenant_id": 1,
}


def _payload(requester_id: str = "STU-001", equipment_code: str = "EQ-001") -> dict[str, object]:
    return {
        "requester_id": requester_id,
        "equipment_code": equipment_code,
        "start_time": "2026-06-01T09:00:00",
        "end_time": "2026-06-01T11:00:00",
        "booking_status": "pending",
        "purpose": "Lab session",
        "conflict_flag": False,
        "cancellation_reason": None,
        "integration_source": None,
    }


class TestConstants:
    def test_active_enrollment_statuses_type(self):
        assert isinstance(svc._ACTIVE_ENROLLMENT_STATUSES, frozenset)

    def test_active_and_enrolled_included(self):
        assert "active" in svc._ACTIVE_ENROLLMENT_STATUSES
        assert "enrolled" in svc._ACTIVE_ENROLLMENT_STATUSES

    def test_withdrawn_and_expelled_excluded(self):
        assert "withdrawn" not in svc._ACTIVE_ENROLLMENT_STATUSES
        assert "expelled" not in svc._ACTIVE_ENROLLMENT_STATUSES

    def test_bookable_equipment_statuses_type(self):
        assert isinstance(svc._BOOKABLE_EQUIPMENT_STATUSES, frozenset)

    def test_available_operational_bookable(self):
        assert "available" in svc._BOOKABLE_EQUIPMENT_STATUSES
        assert "operational" in svc._BOOKABLE_EQUIPMENT_STATUSES

    def test_unavailable_not_bookable(self):
        assert "unavailable" not in svc._BOOKABLE_EQUIPMENT_STATUSES

    def test_maintenance_not_bookable(self):
        assert "maintenance" not in svc._BOOKABLE_EQUIPMENT_STATUSES


class TestW119Guard:
    def test_active_requester_passes(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [ACTIVE_ENROLLMENT])
        svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_enrolled_requester_passes(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [ENROLLED_ENROLLMENT])
        svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-002")

    def test_no_enrollment_blocks(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [])
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-999")

    def test_withdrawn_blocks(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [WITHDRAWN_ENROLLMENT])
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-003")

    def test_expelled_blocks(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [EXPELLED_ENROLLMENT])
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-004")

    def test_case_insensitive_match(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [ACTIVE_ENROLLMENT])
        svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="stu-001")

    def test_whitespace_trim_match(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [ACTIVE_ENROLLMENT])
        svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="  STU-001  ")

    def test_completed_status_blocks(self, monkeypatch):
        completed = {"student_id": "STU-010", "status": "completed", "tenant_id": 1}
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [completed])
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-010")

    def test_error_contains_requester_id(self, monkeypatch):
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: [])
        with pytest.raises(DomainValidationError, match="STU-XYZ"):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-XYZ")


class TestFailClosed:
    def test_lookup_runtime_error_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="lookup failed"):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_lookup_connection_error_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise ConnectionError("network")

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_lookup_ioerror_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise IOError("timeout")

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")


class TestCreateBookingPath:
    def _setup(self, monkeypatch, enrollments, equipment_items, bookings):
        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return enrollments
            if entity_name == "equipment_items":
                return equipment_items
            if entity_name == "equipment_bookings":
                return bookings
            return []

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)

    def test_create_succeeds_for_active(self, monkeypatch):
        self._setup(monkeypatch, [ACTIVE_ENROLLMENT], [GOOD_EQUIPMENT], [])
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.create_entity_for_tenant",
            lambda entity, payload, tenant_id: {"id": 99, "tenant_id": tenant_id, **payload},
        )
        result = svc.create_equipment_booking(_payload(), tenant_id=1)
        assert result["id"] == 99

    def test_create_blocked_for_withdrawn(self, monkeypatch):
        self._setup(monkeypatch, [WITHDRAWN_ENROLLMENT], [GOOD_EQUIPMENT], [])
        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", lambda e, p, t: {"id": 1})
        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(_payload(requester_id="STU-003"), tenant_id=1)

    def test_create_blocked_for_unknown_requester(self, monkeypatch):
        self._setup(monkeypatch, [], [GOOD_EQUIPMENT], [])
        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", lambda e, p, t: {"id": 1})
        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(_payload(requester_id="UNKNOWN"), tenant_id=1)

    def test_guard_fires_before_equipment_lookup(self, monkeypatch):
        lookup_order: list[str] = []

        def mock_list(entity_name, tenant_id):
            lookup_order.append(entity_name)
            if entity_name == "student_enrollments":
                return []
            return [GOOD_EQUIPMENT]

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", lambda e, p, t: {"id": 1})
        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(_payload(), tenant_id=1)
        assert lookup_order[0] == "student_enrollments"
        assert "equipment_items" not in lookup_order[1:]

    def test_validate_before_persist(self, monkeypatch):
        calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return [WITHDRAWN_ENROLLMENT]
            return [GOOD_EQUIPMENT]

        def mock_create(entity_name, payload, tenant_id):
            calls.append(entity_name)
            return {"id": 1}

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", mock_create)

        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(_payload(requester_id="STU-003"), tenant_id=1)

        assert calls == []

    def test_empty_requester_id_blocked(self, monkeypatch):
        self._setup(monkeypatch, [ACTIVE_ENROLLMENT], [GOOD_EQUIPMENT], [])
        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", lambda e, p, t: {"id": 1})
        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(_payload(requester_id=""), tenant_id=1)

    def test_none_requester_id_blocked(self, monkeypatch):
        self._setup(monkeypatch, [ACTIVE_ENROLLMENT], [GOOD_EQUIPMENT], [])
        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", lambda e, p, t: {"id": 1})
        data = _payload()
        data["requester_id"] = None
        with pytest.raises(DomainValidationError):
            svc.create_equipment_booking(data, tenant_id=1)

    def test_persist_called_once_on_success(self, monkeypatch):
        self._setup(monkeypatch, [ACTIVE_ENROLLMENT], [GOOD_EQUIPMENT], [])
        created_entities: list[str] = []

        def mock_create(entity_name, payload, tenant_id):
            created_entities.append(entity_name)
            return {"id": 88, "tenant_id": tenant_id, **payload}

        monkeypatch.setattr("app.modules.equipment_booking.service.create_entity_for_tenant", mock_create)
        svc.create_equipment_booking(_payload(), tenant_id=1)
        assert created_entities == ["equipment_bookings"]


class TestBusinessInvariants:
    def test_two_tenant_isolation(self, monkeypatch):
        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments" and tenant_id == 1:
                return [ACTIVE_ENROLLMENT]
            if entity_name == "student_enrollments" and tenant_id == 2:
                return []
            return [GOOD_EQUIPMENT]

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
        svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=2, requester_id="STU-001")

    def test_multiple_enrollments_one_active_passes(self, monkeypatch):
        rows = [
            {"student_id": "STU-001", "status": "completed", "tenant_id": 1},
            {"student_id": "STU-001", "status": "active", "tenant_id": 1},
        ]
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: rows)
        svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_multiple_enrollments_all_inactive_blocks(self, monkeypatch):
        rows = [
            {"student_id": "STU-001", "status": "completed", "tenant_id": 1},
            {"student_id": "STU-001", "status": "withdrawn", "tenant_id": 1},
        ]
        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", lambda e, t: rows)
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")


class TestTenantScopeAndLists:
    def test_guard_queries_student_enrollments_scope(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def mock_list(entity_name, tenant_id):
            calls.append((entity_name, tenant_id))
            return []

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
        with pytest.raises(DomainValidationError):
            svc._check_requester_enrollment_for_booking(tenant_id=77, requester_id="STU-001")
        assert calls[0] == ("student_enrollments", 77)

    def test_list_bookings_scoped_by_tenant(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def mock_list(entity_name, tenant_id):
            calls.append((entity_name, tenant_id))
            return []

        monkeypatch.setattr("app.modules.equipment_booking.service.list_entities_for_tenant", mock_list)
        svc.list_equipment_bookings(tenant_id=88)
        assert calls == [("equipment_bookings", 88)]


class TestRouterStructure:
    def _router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/equipment_booking/router.py").read_text(encoding="utf-8")

    def test_router_imports_service_alias(self):
        source = self._router_source()
        assert "import app.modules.equipment_booking.service as _svc" in source

    def test_router_has_no_direct_service_imports(self):
        source = self._router_source()
        assert "from app.modules.equipment_booking.service import" not in source

    def test_create_booking_catches_domain_validation_error(self):
        source = self._router_source()
        assert "except (ValueError, DomainValidationError) as exc" in source
        assert "status_code=422" in source

    def test_router_has_expected_paths(self):
        from app.modules.equipment_booking import router as router_obj

        paths = {r.path for r in router_obj.router.routes}
        assert "/api/admin/equipment-booking/equipment" in paths
        assert "/api/admin/equipment-booking/bookings" in paths
        assert "/api/admin/equipment-booking/brain-context" in paths
