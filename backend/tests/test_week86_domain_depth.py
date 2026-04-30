"""W86 — housing: Student Active Assignment Guard (No Double-Booking on Approval).

Cross-entity invariant: A housing request cannot be APPROVED if the student already
has an active room_assignment_records entry (status in {assigned, active}).

Approving a second assignment creates double-occupancy: one student physically in two
rooms simultaneously — inventory corruption, duplicate billing, and a violation of the
physical real-world constraint that a room has one occupant.

Seven behavioral tests covering:
1. Guard function exists and is callable
2. Constant exists and contains correct statuses
3. Guard raises when student has an active assignment (status=assigned)
4. Guard raises when student has an active assignment (status=active)
5. Guard passes when student has no assignments at all
6. Guard passes when student's only assignment is in a closed/inactive status
7. Guard raises (NO SILENT FALLBACK) when room_assignment_records query fails
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.housing.service import (
    _check_no_active_room_assignment,
    _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES,
)
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

def test_w86_constant_exists_and_contains_assigned_and_active():
    """_ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES must be a frozenset containing assigned/active."""
    assert isinstance(_ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES, frozenset), (
        "_ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES must be a frozenset"
    )
    assert "assigned" in _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES, (
        "'assigned' must be in _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES"
    )
    assert "active" in _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES, (
        "'active' must be in _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES"
    )


def test_w86_guard_function_exists_and_callable():
    """_check_no_active_room_assignment must be importable and callable."""
    assert callable(_check_no_active_room_assignment), (
        "_check_no_active_room_assignment not found or not callable"
    )


# ---------------------------------------------------------------------------
# Negative cases — guard must block
# ---------------------------------------------------------------------------

def test_w86_blocked_when_student_has_active_assignment_status_assigned():
    """Guard raises DomainValidationError when student already has status=assigned record."""
    active_assignment = [
        {
            "id": 77,
            "student_id": 42,
            "dormitory": "North Hall",
            "room_preference": "single",
            "status": "assigned",
            "integration_source": "housing_approval",
        }
    ]
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        return_value=active_assignment,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_no_active_room_assignment(tenant_id=1, student_id=42, request_id=101)

        msg = str(exc_info.value)
        assert "student_id=42" in msg, f"student_id missing from error: {msg}"
        assert "request_id=101" in msg, f"request_id missing from error: {msg}"
        assert "active" in msg.lower() or "assigned" in msg.lower(), (
            f"assignment status context missing: {msg}"
        )


def test_w86_blocked_when_student_has_active_assignment_status_active():
    """Guard raises when student has status=active room assignment."""
    active_assignment = [
        {
            "id": 55,
            "student_id": 99,
            "dormitory": "South Dorm",
            "status": "active",
        }
    ]
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        return_value=active_assignment,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_no_active_room_assignment(tenant_id=1, student_id=99, request_id=202)

        msg = str(exc_info.value)
        assert "student_id=99" in msg
        assert "request_id=202" in msg


def test_w86_error_message_contains_double_occupancy_rationale():
    """Error message must explain WHY the guard exists (double-occupancy)."""
    assignment = [{"id": 10, "student_id": 5, "status": "assigned"}]
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        return_value=assignment,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_no_active_room_assignment(tenant_id=1, student_id=5, request_id=300)

        msg = str(exc_info.value)
        # message must explain the real-world invariant
        assert "two rooms" in msg.lower() or "simultaneously" in msg.lower() or "double" in msg.lower(), (
            f"Error must mention double-occupancy rationale: {msg}"
        )


# ---------------------------------------------------------------------------
# Positive cases — guard must pass
# ---------------------------------------------------------------------------

def test_w86_allowed_when_student_has_no_assignments():
    """Guard does not raise when student has no room_assignment_records at all."""
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        return_value=[],
    ):
        # Must not raise
        _check_no_active_room_assignment(tenant_id=1, student_id=42, request_id=101)


def test_w86_allowed_when_student_assignment_is_in_inactive_status():
    """Guard does not raise when student's assignment is in a non-occupancy status."""
    # 'completed' / 'cancelled' / 'vacated' are NOT active occupancy statuses
    closed_assignment = [
        {
            "id": 12,
            "student_id": 42,
            "status": "completed",  # not in _ACTIVE_ASSIGNMENT_OCCUPANCY_STATUSES
        }
    ]
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        return_value=closed_assignment,
    ):
        # Must not raise — student left the room, they can be assigned a new one
        _check_no_active_room_assignment(tenant_id=1, student_id=42, request_id=105)


def test_w86_allowed_when_active_assignment_belongs_to_different_student():
    """Guard does not raise when the active assignment belongs to a different student."""
    other_student_assignment = [
        {
            "id": 99,
            "student_id": 77,  # different student
            "status": "assigned",
        }
    ]
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        return_value=other_student_assignment,
    ):
        # student_id=42 is being approved — student_id=77's assignment is irrelevant
        _check_no_active_room_assignment(tenant_id=1, student_id=42, request_id=110)


# ---------------------------------------------------------------------------
# NO SILENT FALLBACK — guard must block when query fails
# ---------------------------------------------------------------------------

def test_w86_no_silent_fallback_when_query_fails():
    """Guard raises DomainValidationError (not silently passes) when query fails.

    HARDENING RULE: Cannot verify invariant → must block.  Never silently grant
    approval on a broken data path.
    """
    with patch(
        "app.modules.housing.service.list_entities_for_tenant",
        side_effect=RuntimeError("database unavailable"),
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_no_active_room_assignment(tenant_id=1, student_id=42, request_id=101)

        msg = str(exc_info.value)
        assert "Cannot approve" in msg or "query failed" in msg.lower(), (
            f"Error must indicate why approval is blocked: {msg}"
        )
        assert "student_id=42" in msg
