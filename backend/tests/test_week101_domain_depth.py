"""W101 — Operations Room Readiness Safety Guard.

Cross-entity invariant: operations_room_readiness × operations_facility_issues.

A room cannot be marked 'ready' when there are open or in-progress facility
issues with severity 'critical' or 'high' for the same room_code.

Real-world danger: Marking a hazardous room as ready allows classes and events
in an unsafe space, creating safety compliance violations and liability exposure.

Guard location: operations/service.py ::
    _check_no_blocking_facility_issues_for_room  (called BEFORE create_entity_for_tenant)
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.operations.service import (
    _BLOCKING_FACILITY_ISSUE_SEVERITIES,
    _BLOCKING_FACILITY_ISSUE_STATUSES,
    _ROOM_READINESS_READY_STATUS,
    _check_no_blocking_facility_issues_for_room,
    create_room_readiness,
)
from app.modules.operations.schemas import RoomReadinessCreateSchema

TENANT_ID = 9001

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _issue(room_code: str, severity: str, status: str, issue_id: int = 1) -> dict:
    return {
        "id": issue_id,
        "facility_code": room_code,
        "severity": severity,
        "status": status,
        "issue_type": "safety_hazard",
    }


# ---------------------------------------------------------------------------
# Constants smoke tests
# ---------------------------------------------------------------------------

def test_constants_ready_status():
    assert _ROOM_READINESS_READY_STATUS == "ready"


def test_constants_blocking_severities():
    assert "critical" in _BLOCKING_FACILITY_ISSUE_SEVERITIES
    assert "high" in _BLOCKING_FACILITY_ISSUE_SEVERITIES


def test_constants_blocking_statuses():
    assert "open" in _BLOCKING_FACILITY_ISSUE_STATUSES
    assert "in_progress" in _BLOCKING_FACILITY_ISSUE_STATUSES


# ---------------------------------------------------------------------------
# Guard unit tests — direct _check_ function
# ---------------------------------------------------------------------------

def test_guard_no_issues_passes(monkeypatch):
    """No facility issues at all — room can be marked ready."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    # Must not raise
    _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-A1", "ready")


def test_guard_non_ready_status_bypasses_guard(monkeypatch):
    """Only 'ready' status triggers the guard; other statuses bypass it."""
    called = []

    def fake_list(table, tid):
        called.append(table)
        return [_issue("ROOM-A1", "critical", "open")]

    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        fake_list,
    )
    # Should not raise AND should not call list_entities_for_tenant
    for status in ("needs_cleaning", "maintenance_required", "blocked"):
        called.clear()
        _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-A1", status)
        assert not called, f"Guard called list_entities for non-ready status '{status}'"


def test_guard_critical_open_issue_blocks(monkeypatch):
    """Critical + open issue → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-A1", "critical", "open", issue_id=42)],
    )
    with pytest.raises(DomainValidationError, match="critical"):
        _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-A1", "ready")


def test_guard_high_open_issue_blocks(monkeypatch):
    """High + open issue → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-B2", "high", "open", issue_id=7)],
    )
    with pytest.raises(DomainValidationError, match="high"):
        _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-B2", "ready")


def test_guard_critical_in_progress_blocks(monkeypatch):
    """Critical + in_progress issue → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-C3", "critical", "in_progress", issue_id=99)],
    )
    with pytest.raises(DomainValidationError, match="critical"):
        _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-C3", "ready")


def test_guard_low_severity_does_not_block(monkeypatch):
    """Low severity issues must NOT block room readiness."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-D4", "low", "open")],
    )
    _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-D4", "ready")


def test_guard_medium_severity_does_not_block(monkeypatch):
    """Medium severity issues must NOT block room readiness."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-E5", "medium", "open")],
    )
    _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-E5", "ready")


def test_guard_resolved_issue_does_not_block(monkeypatch):
    """Resolved/closed issues must NOT block room readiness."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-F6", "critical", "resolved")],
    )
    _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-F6", "ready")


def test_guard_different_room_issue_does_not_block(monkeypatch):
    """Critical issue for a DIFFERENT room must not block the target room."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: [_issue("ROOM-OTHER", "critical", "open")],
    )
    _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-G7", "ready")


def test_guard_case_insensitive_room_code(monkeypatch):
    """Room code matching must be case-insensitive."""
    issues = [_issue("room-h8", "critical", "open")]
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: issues,
    )
    with pytest.raises(DomainValidationError):
        _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-H8", "ready")


def test_guard_fail_closed_on_query_error(monkeypatch):
    """If facility_issues lookup raises, guard must raise DomainValidationError (fail-closed)."""
    def boom(table, tid):
        raise RuntimeError("DB is down")

    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        boom,
    )
    with pytest.raises(DomainValidationError, match="facility_issues query failed"):
        _check_no_blocking_facility_issues_for_room(TENANT_ID, "ROOM-I9", "ready")


# ---------------------------------------------------------------------------
# Integration tests — full create_room_readiness pathway
# ---------------------------------------------------------------------------

def test_create_room_readiness_blocked_when_critical_issue_open(monkeypatch):
    """create_room_readiness must raise DomainValidationError when critical+open issue exists."""
    monkeypatch.setattr(
        "app.modules.operations.service.list_entities_for_tenant",
        lambda table, tid: (
            [_issue("ROOM-J10", "critical", "open")] if table == "operations_facility_issues" else []
        ),
    )
    request = RoomReadinessCreateSchema(
        room_code="ROOM-J10",
        building_code="BLDG-1",
        status="ready",
    )
    with pytest.raises(DomainValidationError, match="ROOM-J10"):
        create_room_readiness(TENANT_ID, request, actor="test")


def test_create_room_readiness_allowed_when_no_blocking_issues(monkeypatch):
    """create_room_readiness must succeed when no critical/high+open issues exist."""
    def fake_list(table, tid):
        if table == "operations_facility_issues":
            return [_issue("ROOM-K11", "low", "open")]
        return []

    created_rows = []

    def fake_create(table, payload, tid):
        row = {"id": 1, "tenant_id": str(tid), **payload}
        created_rows.append(row)
        return row

    monkeypatch.setattr("app.modules.operations.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.operations.service.create_entity_for_tenant", fake_create)

    request = RoomReadinessCreateSchema(
        room_code="ROOM-K11",
        building_code="BLDG-2",
        status="ready",
    )
    result = create_room_readiness(TENANT_ID, request, actor="test")
    assert result.room_code == "ROOM-K11"
    assert created_rows, "create_entity_for_tenant must have been called"


def test_create_room_readiness_non_ready_status_bypasses_guard(monkeypatch):
    """Non-ready statuses must bypass the guard even if critical issues exist."""
    created_rows = []

    def fake_list(table, tid):
        # Critical issue exists — but guard must be bypassed for non-ready status
        return [_issue("ROOM-L12", "critical", "open")]

    def fake_create(table, payload, tid):
        row = {"id": 2, "tenant_id": str(tid), **payload}
        created_rows.append(row)
        return row

    monkeypatch.setattr("app.modules.operations.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.operations.service.create_entity_for_tenant", fake_create)

    for status in ("needs_cleaning", "maintenance_required", "blocked"):
        created_rows.clear()
        request = RoomReadinessCreateSchema(
            room_code="ROOM-L12",
            building_code="BLDG-3",
            status=status,
        )
        result = create_room_readiness(TENANT_ID, request, actor="test")
        assert result is not None
        assert created_rows, f"create_entity must have been called for status='{status}'"
