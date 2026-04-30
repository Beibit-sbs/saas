"""W119 — equipment_booking: Cross-entity enrollment guard hardening.

Real-world problem:
    create_equipment_booking() had no check that the requester is an active member of the
    tenant. Withdrawn, expelled, or ghost user IDs could consume shared lab inventory,
    creating booking conflicts for legitimate users.

Root fix:
    _check_requester_enrollment_for_booking() — fail-closed guard that validates
    requester_id against student_enrollments BEFORE any persist.

Guard answers the 5 hardening questions:
1. Dangerous action      : creating an equipment booking (reserves shared physical inventory)
2. Real-world constraint : only currently enrolled students/researchers may book equipment
3. External entity       : student_enrollments
4. Validate BEFORE       : create_entity_for_tenant("equipment_bookings", ...)
5. Bad outcome prevented : ghost/withdrawn users blocking inventory, denial-of-service on labs
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.equipment_booking.service import (
    _ACTIVE_ENROLLMENT_STATUSES,
    _BOOKABLE_EQUIPMENT_STATUSES,
    _check_requester_enrollment_for_booking,
    create_equipment_booking,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

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


def _make_booking_payload(
    requester_id: str = "STU-001",
    equipment_code: str = "EQ-001",
    booking_status: str = "pending",
) -> dict[str, object]:
    return {
        "requester_id": requester_id,
        "equipment_code": equipment_code,
        "start_time": "2026-06-01T09:00:00",
        "end_time": "2026-06-01T11:00:00",
        "booking_status": booking_status,
        "purpose": "Lab session",
        "conflict_flag": False,
        "cancellation_reason": None,
        "integration_source": None,
    }


# ---------------------------------------------------------------------------
# TestW119Constants — sentinel values
# ---------------------------------------------------------------------------


class TestW119Constants:
    def test_active_enrollment_statuses_type(self):
        assert isinstance(_ACTIVE_ENROLLMENT_STATUSES, frozenset)

    def test_active_included(self):
        assert "active" in _ACTIVE_ENROLLMENT_STATUSES

    def test_enrolled_included(self):
        assert "enrolled" in _ACTIVE_ENROLLMENT_STATUSES

    def test_withdrawn_excluded(self):
        assert "withdrawn" not in _ACTIVE_ENROLLMENT_STATUSES

    def test_expelled_excluded(self):
        assert "expelled" not in _ACTIVE_ENROLLMENT_STATUSES

    def test_completed_excluded(self):
        assert "completed" not in _ACTIVE_ENROLLMENT_STATUSES

    def test_bookable_equipment_statuses_type(self):
        assert isinstance(_BOOKABLE_EQUIPMENT_STATUSES, frozenset)

    def test_available_bookable(self):
        assert "available" in _BOOKABLE_EQUIPMENT_STATUSES

    def test_operational_bookable(self):
        assert "operational" in _BOOKABLE_EQUIPMENT_STATUSES

    def test_maintenance_not_bookable(self):
        assert "maintenance" not in _BOOKABLE_EQUIPMENT_STATUSES


# ---------------------------------------------------------------------------
# TestW119GuardSignature — guard raises DomainValidationError (not ValueError)
# ---------------------------------------------------------------------------


class TestW119GuardSignature:
    def test_guard_raises_domain_validation_error_not_value_error(self, monkeypatch):
        """Guard must raise DomainValidationError, not generic ValueError."""
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="NOBODY")

    def test_guard_does_not_raise_for_active_requester(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_ENROLLMENT],
        )
        # Should not raise
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_guard_does_not_raise_for_enrolled_requester(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ENROLLED_ENROLLMENT],
        )
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-002")


# ---------------------------------------------------------------------------
# TestW119GuardFailures — all blocked scenarios
# ---------------------------------------------------------------------------


class TestW119GuardFailures:
    def test_no_enrollment_at_all_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-999")

    def test_withdrawn_requester_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [WITHDRAWN_ENROLLMENT],
        )
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-003")

    def test_expelled_requester_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [EXPELLED_ENROLLMENT],
        )
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-004")

    def test_wrong_tenant_enrollment_ignored(self, monkeypatch):
        """Enrollment from tenant_id=99 must NOT satisfy tenant_id=1 lookup (different namespace)."""
        # list_entities_for_tenant filters by tenant already — simulate empty result
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [] if tenant_id == 1 else [ACTIVE_ENROLLMENT],
        )
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_case_insensitive_requester_id_match(self, monkeypatch):
        """Guard matches student_id case-insensitively."""
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_ENROLLMENT],  # student_id="STU-001"
        )
        # Upper-case variant should still find the match
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="stu-001")

    def test_whitespace_requester_id_trimmed(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_ENROLLMENT],
        )
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="  STU-001  ")


# ---------------------------------------------------------------------------
# TestW119FailClosed — lookup failure → DomainValidationError (never silently pass)
# ---------------------------------------------------------------------------


class TestW119FailClosed:
    def test_lookup_exception_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_lookup_exception_never_silently_passes(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise ConnectionError("network error")

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            boom,
        )
        # Must not silently succeed
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_lookup_ioerror_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise IOError("timeout")

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")


# ---------------------------------------------------------------------------
# TestW119CreateBookingPath — end-to-end create_equipment_booking integration
# ---------------------------------------------------------------------------


class TestW119CreateBookingPath:
    def _setup_monkeypatches(self, monkeypatch, enrollments, equipment_items, existing_bookings):
        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return enrollments
            if entity_name == "equipment_items":
                return equipment_items
            if entity_name == "equipment_bookings":
                return existing_bookings
            return []

        created = {}

        def mock_create(entity_name, payload, tenant_id):
            record = dict(payload)
            record["id"] = 99
            record["tenant_id"] = tenant_id
            created["entity_name"] = entity_name
            created["payload"] = record
            return record

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            mock_list,
        )
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.create_entity_for_tenant",
            mock_create,
        )
        return created

    def test_create_succeeds_for_active_enrolled_requester(self, monkeypatch):
        created = self._setup_monkeypatches(
            monkeypatch,
            enrollments=[ACTIVE_ENROLLMENT],
            equipment_items=[GOOD_EQUIPMENT],
            existing_bookings=[],
        )
        result = create_equipment_booking(_make_booking_payload(), tenant_id=1)
        assert result["id"] == 99
        assert created["entity_name"] == "equipment_bookings"

    def test_create_blocked_for_withdrawn_requester(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch,
            enrollments=[WITHDRAWN_ENROLLMENT],
            equipment_items=[GOOD_EQUIPMENT],
            existing_bookings=[],
        )
        with pytest.raises(DomainValidationError):
            create_equipment_booking(
                _make_booking_payload(requester_id="STU-003"), tenant_id=1
            )

    def test_create_blocked_for_unknown_requester(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch,
            enrollments=[],
            equipment_items=[GOOD_EQUIPMENT],
            existing_bookings=[],
        )
        with pytest.raises(DomainValidationError):
            create_equipment_booking(
                _make_booking_payload(requester_id="GHOST-999"), tenant_id=1
            )

    def test_enrollment_guard_fires_before_equipment_lookup(self, monkeypatch):
        """If enrollment guard raises, create must not touch equipment_items."""
        equipment_lookups: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return []  # trigger guard failure
            equipment_lookups.append(entity_name)
            return [GOOD_EQUIPMENT]

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            mock_list,
        )
        with pytest.raises(DomainValidationError):
            create_equipment_booking(_make_booking_payload(), tenant_id=1)

        assert "equipment_items" not in equipment_lookups

    def test_create_not_persisted_when_enrollment_fails(self, monkeypatch):
        created_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return [WITHDRAWN_ENROLLMENT]
            return [GOOD_EQUIPMENT]

        def mock_create(entity_name, payload, tenant_id):
            created_calls.append(entity_name)
            return {"id": 1}

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            mock_list,
        )
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.create_entity_for_tenant",
            mock_create,
        )
        with pytest.raises(DomainValidationError):
            create_equipment_booking(
                _make_booking_payload(requester_id="STU-003"), tenant_id=1
            )
        assert created_calls == [], "create_entity_for_tenant must not be called on guard failure"

    def test_empty_requester_id_blocked(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch,
            enrollments=[ACTIVE_ENROLLMENT],
            equipment_items=[GOOD_EQUIPMENT],
            existing_bookings=[],
        )
        with pytest.raises(DomainValidationError):
            create_equipment_booking(
                _make_booking_payload(requester_id=""), tenant_id=1
            )

    def test_none_requester_id_blocked(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch,
            enrollments=[ACTIVE_ENROLLMENT],
            equipment_items=[GOOD_EQUIPMENT],
            existing_bookings=[],
        )
        payload = _make_booking_payload()
        payload["requester_id"] = None
        with pytest.raises(DomainValidationError):
            create_equipment_booking(payload, tenant_id=1)


# ---------------------------------------------------------------------------
# TestW119PersistOrdering — guard fires before ANY write
# ---------------------------------------------------------------------------


class TestW119PersistOrdering:
    def test_guard_fires_before_create_entity(self, monkeypatch):
        """Guard must prevent create_entity_for_tenant when enrollment fails."""
        persist_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return []  # no enrollment
            return [GOOD_EQUIPMENT]

        def mock_create(entity_name, payload, tenant_id):
            persist_calls.append(entity_name)
            return {"id": 1}

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            mock_list,
        )
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.create_entity_for_tenant",
            mock_create,
        )
        with pytest.raises(DomainValidationError):
            create_equipment_booking(_make_booking_payload(), tenant_id=1)

        assert persist_calls == []

    def test_persist_called_once_on_success(self, monkeypatch):
        persist_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments":
                return [ACTIVE_ENROLLMENT]
            if entity_name == "equipment_items":
                return [GOOD_EQUIPMENT]
            return []  # no existing bookings

        def mock_create(entity_name, payload, tenant_id):
            persist_calls.append(entity_name)
            return {"id": 1, "tenant_id": tenant_id, **payload}

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            mock_list,
        )
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.create_entity_for_tenant",
            mock_create,
        )
        create_equipment_booking(_make_booking_payload(), tenant_id=1)
        assert persist_calls == ["equipment_bookings"]


# ---------------------------------------------------------------------------
# TestW119BusinessInvariants — combined scenarios
# ---------------------------------------------------------------------------


class TestW119BusinessInvariants:
    def test_two_tenants_isolated_enrollment_check(self, monkeypatch):
        """Tenant A enrollment must not satisfy Tenant B check."""

        def mock_list(entity_name, tenant_id):
            if entity_name == "student_enrollments" and tenant_id == 1:
                return [ACTIVE_ENROLLMENT]  # active for tenant 1
            if entity_name == "student_enrollments" and tenant_id == 2:
                return []  # no enrollment for tenant 2
            return [GOOD_EQUIPMENT]

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            mock_list,
        )
        # Tenant 1 succeeds
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")
        # Tenant 2 blocked
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=2, requester_id="STU-001")

    def test_multiple_enrollments_one_active_passes(self, monkeypatch):
        """If student has multiple rows (e.g. historical + current), active row suffices."""
        enrollments = [
            {"student_id": "STU-001", "status": "completed", "tenant_id": 1},
            {"student_id": "STU-001", "status": "active", "tenant_id": 1},
        ]
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda e, t: enrollments,
        )
        # Should pass — at least one active enrollment
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_multiple_enrollments_all_inactive_blocked(self, monkeypatch):
        enrollments = [
            {"student_id": "STU-001", "status": "completed", "tenant_id": 1},
            {"student_id": "STU-001", "status": "withdrawn", "tenant_id": 1},
        ]
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda e, t: enrollments,
        )
        with pytest.raises(DomainValidationError):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")

    def test_error_message_contains_requester_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="STU-XYZ"):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-XYZ")

    def test_enrolled_status_exact_string(self, monkeypatch):
        """'enrolled' (not just 'active') is accepted."""
        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            lambda e, t: [{"student_id": "STU-007", "status": "enrolled", "tenant_id": 1}],
        )
        _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-007")

    def test_fail_closed_error_message_mentions_lookup(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise Exception("DB timeout")

        monkeypatch.setattr(
            "app.modules.equipment_booking.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
            _check_requester_enrollment_for_booking(tenant_id=1, requester_id="STU-001")
