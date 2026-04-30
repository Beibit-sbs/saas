"""W105 — Transport Booking Route Status Guard.

Cross-entity invariant: transport_bookings × transport_routes.

A booking may only be created for a route that exists AND has a bookable
status (active or scheduled). Booking a disrupted/cancelled/non-existent
route generates confirmed reservations for ghost journeys, misleads students,
and corrupts Brain Core transport utilisation analytics.

Guard location: transport/service.py ::
    _check_route_is_bookable  (called BEFORE create_entity_for_tenant)
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.transport.service import (
    _BOOKABLE_ROUTE_STATUSES,
    _check_route_is_bookable,
    create_transport_booking,
)

TENANT_ID = 9005

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _route(route_code: str, status: str, rid: int = 1) -> dict:
    return {"id": rid, "route_code": route_code, "status": status}


def _booking_payload(route_code: str = "RT-001", passenger_id: str = "STU-P01") -> dict:
    return {
        "route_code": route_code,
        "passenger_id": passenger_id,
        "booking_status": "confirmed",
        "seat_number": "12A",
    }


# ---------------------------------------------------------------------------
# Constants smoke tests
# ---------------------------------------------------------------------------

def test_constants_bookable_route_statuses():
    assert "active" in _BOOKABLE_ROUTE_STATUSES
    assert "scheduled" in _BOOKABLE_ROUTE_STATUSES


def test_constants_non_bookable_not_in_set():
    assert "disrupted" not in _BOOKABLE_ROUTE_STATUSES
    assert "cancelled" not in _BOOKABLE_ROUTE_STATUSES
    assert "suspended" not in _BOOKABLE_ROUTE_STATUSES


# ---------------------------------------------------------------------------
# Guard unit tests — direct _check_ function
# ---------------------------------------------------------------------------

def test_guard_active_route_passes(monkeypatch):
    """Route with status='active' → no raise."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-001", "active")] if table == "transport_routes" else [],
    )
    _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-001")


def test_guard_scheduled_route_passes(monkeypatch):
    """Route with status='scheduled' → no raise."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-002", "scheduled")] if table == "transport_routes" else [],
    )
    _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-002")


def test_guard_route_not_found_blocks(monkeypatch):
    """No route with the given route_code → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="route not found"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-GHOST")


def test_guard_disrupted_route_blocks(monkeypatch):
    """Route with status='disrupted' → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-003", "disrupted")] if table == "transport_routes" else [],
    )
    with pytest.raises(DomainValidationError, match="not bookable"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-003")


def test_guard_cancelled_route_blocks(monkeypatch):
    """Route with status='cancelled' → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-004", "cancelled")] if table == "transport_routes" else [],
    )
    with pytest.raises(DomainValidationError, match="not bookable"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-004")


def test_guard_suspended_route_blocks(monkeypatch):
    """Route with status='suspended' → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-005", "suspended")] if table == "transport_routes" else [],
    )
    with pytest.raises(DomainValidationError, match="not bookable"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-005")


def test_guard_different_route_code_does_not_satisfy(monkeypatch):
    """Active route with different route_code must NOT satisfy the guard."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-OTHER", "active")] if table == "transport_routes" else [],
    )
    with pytest.raises(DomainValidationError, match="route not found"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-TARGET")


def test_guard_route_code_case_insensitive(monkeypatch):
    """route_code match must be case-insensitive."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("rt-100", "active")] if table == "transport_routes" else [],
    )
    # Must not raise — RT-100 vs rt-100 should match
    _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-100")


def test_guard_fail_closed_on_query_error(monkeypatch):
    """If route lookup raises, guard must raise DomainValidationError (fail-closed)."""
    def boom(table, tid):
        raise RuntimeError("DB timeout")

    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        boom,
    )
    with pytest.raises(DomainValidationError, match="route lookup failed"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-ERR")


def test_guard_error_message_includes_route_code(monkeypatch):
    """Error message must clearly identify the route_code that failed."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="RT-MSG-123"):
        _check_route_is_bookable(tenant_id=TENANT_ID, route_code="RT-MSG-123")


# ---------------------------------------------------------------------------
# Integration tests — full create_transport_booking pathway
# ---------------------------------------------------------------------------

def test_create_booking_blocked_for_cancelled_route(monkeypatch):
    """create_transport_booking must raise DomainValidationError for a cancelled route."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [_route("RT-CANC", "cancelled")] if table == "transport_routes" else [],
    )
    with pytest.raises(DomainValidationError, match="RT-CANC"):
        create_transport_booking(_booking_payload(route_code="RT-CANC"), TENANT_ID)


def test_create_booking_blocked_for_unknown_route(monkeypatch):
    """create_transport_booking must raise DomainValidationError when route doesn't exist."""
    monkeypatch.setattr(
        "app.modules.transport.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="route not found"):
        create_transport_booking(_booking_payload(route_code="RT-NX"), TENANT_ID)


def test_create_booking_allowed_for_active_route(monkeypatch):
    """create_transport_booking must succeed for an active route."""
    persisted: list[dict] = []

    def fake_list(table, tid):
        return [_route("RT-OK", "active")] if table == "transport_routes" else []

    def fake_create(table, payload, tid):
        row = {"id": 1, "tenant_id": str(tid), **payload}
        persisted.append(row)
        return row

    monkeypatch.setattr("app.modules.transport.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.transport.service.create_entity_for_tenant", fake_create)

    result = create_transport_booking(_booking_payload(route_code="RT-OK"), TENANT_ID)
    assert result["route_code"] == "RT-OK"
    assert persisted, "create_entity_for_tenant must have been called"


def test_create_booking_guard_fires_before_persist(monkeypatch):
    """Guard must fire BEFORE create_entity_for_tenant — no record created on block."""
    persisted: list[dict] = []

    def fake_list(table, tid):
        return [_route("RT-D", "disrupted")] if table == "transport_routes" else []

    def fake_create(table, payload, tid):
        persisted.append(payload)
        return {"id": 99, **payload}

    monkeypatch.setattr("app.modules.transport.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.transport.service.create_entity_for_tenant", fake_create)

    with pytest.raises(DomainValidationError):
        create_transport_booking(_booking_payload(route_code="RT-D"), TENANT_ID)

    assert not persisted, "create_entity_for_tenant must NOT be called when guard blocks"
