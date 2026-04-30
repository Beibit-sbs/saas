"""W82 — scheduling: Instructor Active Contract Guard on Section Assignment.

Cross-entity invariant: scheduling.InstructorAssignmentModel × faculty_contracts.status.
assign_instructor() must be blocked when the instructor's only existing contracts are
terminated or expired.

Without this guard, a terminated faculty member can be assigned to teach — payroll
generates payment, HR compliance fails, and students are assigned an instructor who
contractually cannot teach. A single active contract (status in {active, draft, pending})
is required for any assignment to proceed.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.scheduling.service import (
    SchedulingService,
    _INSTRUCTOR_ACTIVE_CONTRACT_STATUSES,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _service() -> SchedulingService:
    db = MagicMock()
    return SchedulingService(db_session=db)


def _make_contract(faculty_id: str, status: str) -> dict:
    return {"id": 1, "faculty_id": faculty_id, "status": status, "tenant_id": 1}


def _patch_contracts(svc: SchedulingService, contracts: list[dict]):
    """Patch list_entities_for_tenant inside scheduling.service to return given contracts."""
    return patch(
        "app.modules.scheduling.service._list_tenant_entities",
        return_value=contracts,
    )


# ---------------------------------------------------------------------------
# Test 1: constant and guard method exist
# ---------------------------------------------------------------------------

def test_w82_constant_and_guard_exist():
    assert isinstance(_INSTRUCTOR_ACTIVE_CONTRACT_STATUSES, frozenset)
    assert "active" in _INSTRUCTOR_ACTIVE_CONTRACT_STATUSES
    assert "terminated" not in _INSTRUCTOR_ACTIVE_CONTRACT_STATUSES
    assert "expired" not in _INSTRUCTOR_ACTIVE_CONTRACT_STATUSES
    svc = _service()
    assert hasattr(svc, "_check_instructor_has_active_contract")


# ---------------------------------------------------------------------------
# Test 2: blocked when instructor has only terminated contracts
# ---------------------------------------------------------------------------

def test_w82_blocked_when_all_contracts_terminated():
    svc = _service()
    contracts = [
        _make_contract("instructor-001", "terminated"),
        _make_contract("instructor-001", "expired"),
    ]
    with _patch_contracts(svc, contracts):
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_instructor_has_active_contract(tenant_id=1, instructor_id="instructor-001")

    assert "instructor-001" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 3: allowed when instructor has at least one active contract
# ---------------------------------------------------------------------------

def test_w82_allowed_when_active_contract_exists():
    svc = _service()
    contracts = [
        _make_contract("instructor-002", "terminated"),
        _make_contract("instructor-002", "active"),
    ]
    with _patch_contracts(svc, contracts):
        # Must not raise
        svc._check_instructor_has_active_contract(tenant_id=1, instructor_id="instructor-002")


# ---------------------------------------------------------------------------
# Test 4: allowed when instructor has draft or pending contract
# ---------------------------------------------------------------------------

def test_w82_allowed_when_draft_or_pending_contract():
    svc = _service()
    for status in ("draft", "pending"):
        contracts = [_make_contract("instructor-003", status)]
        with _patch_contracts(svc, contracts):
            svc._check_instructor_has_active_contract(tenant_id=1, instructor_id="instructor-003")


# ---------------------------------------------------------------------------
# Test 5: safe-skip when instructor has no contracts (not tracked in system)
# ---------------------------------------------------------------------------

def test_w82_safe_skip_when_no_contracts_for_instructor():
    svc = _service()
    # Tenant has contracts but not for this instructor
    contracts = [_make_contract("other-instructor", "terminated")]
    with _patch_contracts(svc, contracts):
        # Must not raise — instructor not in contract system
        svc._check_instructor_has_active_contract(tenant_id=1, instructor_id="instructor-999")


# ---------------------------------------------------------------------------
# Test 6: error message names instructor_id and required statuses
# ---------------------------------------------------------------------------

def test_w82_error_message_names_instructor_and_statuses():
    svc = _service()
    contracts = [_make_contract("instructor-X", "terminated")]
    with _patch_contracts(svc, contracts):
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_instructor_has_active_contract(tenant_id=1, instructor_id="instructor-X")

    msg = str(exc_info.value)
    assert "instructor-X" in msg
    assert "active" in msg
