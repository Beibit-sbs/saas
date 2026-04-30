"""W99: student_services ticket resolution quality guard.

Guard: update_student_service_ticket_status → 'resolved' requires:
  1. ticket owner_id != 'unassigned' (no ghost resolutions)
  2. meaningful resolution_notes (not empty/placeholder)

Cross-entity: transition guard + business invariant per hardening rules.
"""
from __future__ import annotations

import pytest

from app.modules.student_services.service import (
    _TICKET_RESOLVED_TARGET_STATUS,
    _RESOLUTION_NOTES_PLACEHOLDER_VALUES,
    _UNASSIGNED_OWNER_SENTINEL,
    _check_ticket_resolution_requirements,
)
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

def test_resolved_target_status_constant():
    assert _TICKET_RESOLVED_TARGET_STATUS == "resolved"


def test_resolution_placeholder_values_constant():
    assert isinstance(_RESOLUTION_NOTES_PLACEHOLDER_VALUES, frozenset)
    assert "pending" in _RESOLUTION_NOTES_PLACEHOLDER_VALUES
    assert "n/a" in _RESOLUTION_NOTES_PLACEHOLDER_VALUES
    assert "" in _RESOLUTION_NOTES_PLACEHOLDER_VALUES
    assert "tbd" in _RESOLUTION_NOTES_PLACEHOLDER_VALUES


def test_unassigned_owner_sentinel_constant():
    assert _UNASSIGNED_OWNER_SENTINEL == "unassigned"


# ---------------------------------------------------------------------------
# 2. Guard is a no-op for non-resolved target statuses
# ---------------------------------------------------------------------------

def test_guard_noop_for_in_progress():
    # must NOT raise for non-resolved transitions
    _check_ticket_resolution_requirements(
        ticket_id=1,
        owner_id="unassigned",
        resolution_notes=None,
        target_status="in_progress",
    )


def test_guard_noop_for_closed():
    _check_ticket_resolution_requirements(
        ticket_id=2,
        owner_id="unassigned",
        resolution_notes=None,
        target_status="closed",
    )


def test_guard_noop_for_open():
    _check_ticket_resolution_requirements(
        ticket_id=3,
        owner_id="unassigned",
        resolution_notes=None,
        target_status="open",
    )


# ---------------------------------------------------------------------------
# 3. Block: unassigned owner
# ---------------------------------------------------------------------------

def test_guard_blocks_unassigned_owner():
    with pytest.raises(DomainValidationError, match="unassigned"):
        _check_ticket_resolution_requirements(
            ticket_id=10,
            owner_id="unassigned",
            resolution_notes="Fixed the issue by updating the student record.",
            target_status="resolved",
        )


def test_guard_blocks_empty_owner():
    with pytest.raises(DomainValidationError, match="unassigned"):
        _check_ticket_resolution_requirements(
            ticket_id=11,
            owner_id="",
            resolution_notes="Resolved: provided enrollment confirmation to student.",
            target_status="resolved",
        )


def test_guard_error_message_contains_ticket_id_for_owner():
    with pytest.raises(DomainValidationError, match="ticket_id=42"):
        _check_ticket_resolution_requirements(
            ticket_id=42,
            owner_id="unassigned",
            resolution_notes="Some resolution note",
            target_status="resolved",
        )


# ---------------------------------------------------------------------------
# 4. Block: missing or placeholder resolution_notes
# ---------------------------------------------------------------------------

def test_guard_blocks_none_resolution_notes():
    with pytest.raises(DomainValidationError, match="resolution_notes"):
        _check_ticket_resolution_requirements(
            ticket_id=20,
            owner_id="staff.advisor@uni.edu",
            resolution_notes=None,
            target_status="resolved",
        )


def test_guard_blocks_pending_placeholder():
    with pytest.raises(DomainValidationError, match="resolution_notes"):
        _check_ticket_resolution_requirements(
            ticket_id=21,
            owner_id="staff.advisor@uni.edu",
            resolution_notes="pending",
            target_status="resolved",
        )


def test_guard_blocks_na_placeholder():
    with pytest.raises(DomainValidationError, match="resolution_notes"):
        _check_ticket_resolution_requirements(
            ticket_id=22,
            owner_id="registrar.jones",
            resolution_notes="n/a",
            target_status="resolved",
        )


def test_guard_blocks_tbd_placeholder():
    with pytest.raises(DomainValidationError, match="resolution_notes"):
        _check_ticket_resolution_requirements(
            ticket_id=23,
            owner_id="support.team",
            resolution_notes="tbd",
            target_status="resolved",
        )


def test_guard_blocks_empty_string_resolution_notes():
    with pytest.raises(DomainValidationError, match="resolution_notes"):
        _check_ticket_resolution_requirements(
            ticket_id=24,
            owner_id="admin.staff",
            resolution_notes="",
            target_status="resolved",
        )


# ---------------------------------------------------------------------------
# 5. Allow: valid owner + meaningful resolution notes
# ---------------------------------------------------------------------------

def test_guard_allows_valid_resolution():
    # Must not raise
    _check_ticket_resolution_requirements(
        ticket_id=30,
        owner_id="advisor.smith",
        resolution_notes="Contacted registrar; student enrollment record corrected. Issue closed.",
        target_status="resolved",
    )


def test_guard_allows_long_resolution_notes():
    long_notes = "Student presented an issue with financial aid disbursement. " * 5
    _check_ticket_resolution_requirements(
        ticket_id=31,
        owner_id="financial.aid.office",
        resolution_notes=long_notes,
        target_status="resolved",
    )


# ---------------------------------------------------------------------------
# 6. Guard wired in update function
# ---------------------------------------------------------------------------

def test_guard_wired_in_update_function():
    """Guard is called inside update_student_service_ticket_status before persist."""
    import inspect
    from app.modules.student_services import service as svc_module

    source = inspect.getsource(svc_module.update_student_service_ticket_status)
    assert "_check_ticket_resolution_requirements" in source, (
        "W99 guard must be called inside update_student_service_ticket_status"
    )
    # Guard call must appear before update_entity_for_tenant call
    guard_pos = source.index("_check_ticket_resolution_requirements")
    persist_pos = source.index("update_entity_for_tenant")
    assert guard_pos < persist_pos, (
        "W99 guard must be wired BEFORE update_entity_for_tenant (guard before persist)"
    )
