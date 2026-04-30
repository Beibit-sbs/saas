"""W94 — hr_payroll: Payroll Cycle Approval Requires Active Employees (Ghost Payroll Guard).

GUARDED INVARIANT:
    A payroll cycle cannot be APPROVED if the tenant has no employees
    in a payable status (active or on_leave).  Approving an empty payroll
    constitutes a ghost payroll scenario: financial records are committed
    with no actual recipients, bypassing audit controls.

CROSS-ENTITY: hr_payroll_cycles × hr_employees

TESTS:
     1. test_w94_payroll_approval_gate_constant_exists   — _PAYROLL_APPROVAL_GATE_STATUSES is frozenset with APPROVED
     2. test_w94_payable_employee_statuses_set           — _PAYABLE_EMPLOYEE_STATUSES contains active/on_leave; not terminated
     3. test_w94_guard_function_exists_and_callable      — guard importable and callable
     4. test_w94_blocked_when_no_employees_at_all        — DomainValidationError when employee list is empty
     5. test_w94_blocked_when_only_terminated_employees  — terminated employees don't count as payable
     6. test_w94_blocked_when_only_offboarding_employees — offboarding does not qualify as payable
     7. test_w94_blocked_when_employee_lookup_fails      — query error → DomainValidationError (fail-closed)
     8. test_w94_allowed_when_active_employee_exists     — at least 1 active employee → APPROVED succeeds
     9. test_w94_allowed_when_on_leave_employee_exists   — on_leave counts as payable
    10. test_w94_guard_surgical_non_approval_skips_check — CALCULATING→APPROVED gate skipped for other transitions
    11. test_w94_error_message_contains_ghost_payroll_rationale — error message explains the risk
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.hr_payroll.service import (
    _PAYABLE_EMPLOYEE_STATUSES,
    _PAYROLL_APPROVAL_GATE_STATUSES,
    _check_active_employees_exist_for_payroll_approval,
)


# ---------------------------------------------------------------------------
# 1. Payroll approval gate constant exists
# ---------------------------------------------------------------------------

def test_w94_payroll_approval_gate_constant_exists():
    """_PAYROLL_APPROVAL_GATE_STATUSES must be a frozenset containing APPROVED."""
    assert isinstance(_PAYROLL_APPROVAL_GATE_STATUSES, frozenset)
    assert "APPROVED" in _PAYROLL_APPROVAL_GATE_STATUSES


# ---------------------------------------------------------------------------
# 2. Payable employee statuses set
# ---------------------------------------------------------------------------

def test_w94_payable_employee_statuses_set():
    """_PAYABLE_EMPLOYEE_STATUSES must include active and on_leave but not terminated."""
    assert isinstance(_PAYABLE_EMPLOYEE_STATUSES, frozenset)
    assert "active" in _PAYABLE_EMPLOYEE_STATUSES
    assert "on_leave" in _PAYABLE_EMPLOYEE_STATUSES
    assert "terminated" not in _PAYABLE_EMPLOYEE_STATUSES
    assert "offboarding" not in _PAYABLE_EMPLOYEE_STATUSES


# ---------------------------------------------------------------------------
# 3. Guard function importable and callable
# ---------------------------------------------------------------------------

def test_w94_guard_function_exists_and_callable():
    """Guard function must be importable and callable from service module."""
    assert callable(_check_active_employees_exist_for_payroll_approval)


# ---------------------------------------------------------------------------
# 4. Blocked when no employees at all
# ---------------------------------------------------------------------------

def test_w94_blocked_when_no_employees_at_all():
    """Empty employee list → DomainValidationError (ghost payroll blocked)."""
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError):
            _check_active_employees_exist_for_payroll_approval(
                tenant_id=1,
                cycle_id=100,
                target_status="APPROVED",
            )


# ---------------------------------------------------------------------------
# 5. Blocked when only terminated employees
# ---------------------------------------------------------------------------

def test_w94_blocked_when_only_terminated_employees():
    """Terminated employees must not count as payable — guard must block APPROVED."""
    employees = [
        {"id": 1, "status": "terminated", "employee_code": "EMP-01"},
        {"id": 2, "status": "terminated", "employee_code": "EMP-02"},
    ]
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        return_value=employees,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_active_employees_exist_for_payroll_approval(
                tenant_id=1,
                cycle_id=101,
                target_status="APPROVED",
            )
    assert "ghost payroll" in str(exc_info.value).lower() or "no employees" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 6. Blocked when only offboarding employees
# ---------------------------------------------------------------------------

def test_w94_blocked_when_only_offboarding_employees():
    """offboarding status must not qualify as payable."""
    employees = [{"id": 3, "status": "offboarding", "employee_code": "EMP-03"}]
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        return_value=employees,
    ):
        with pytest.raises(DomainValidationError):
            _check_active_employees_exist_for_payroll_approval(
                tenant_id=2,
                cycle_id=102,
                target_status="APPROVED",
            )


# ---------------------------------------------------------------------------
# 7. Fail-closed when employee lookup fails
# ---------------------------------------------------------------------------

def test_w94_blocked_when_employee_lookup_fails():
    """Query failure → DomainValidationError, not silent grant (fail-closed)."""
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB timeout"),
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_active_employees_exist_for_payroll_approval(
                tenant_id=3,
                cycle_id=103,
                target_status="APPROVED",
            )
    msg = str(exc_info.value)
    assert "lookup failed" in msg.lower() or "failed" in msg.lower()
    assert "103" in msg  # cycle_id traceable


# ---------------------------------------------------------------------------
# 8. Allowed when active employee exists
# ---------------------------------------------------------------------------

def test_w94_allowed_when_active_employee_exists():
    """At least one active employee → guard passes silently."""
    employees = [{"id": 10, "status": "active", "employee_code": "EMP-10"}]
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        return_value=employees,
    ):
        # Must not raise
        _check_active_employees_exist_for_payroll_approval(
            tenant_id=4,
            cycle_id=200,
            target_status="APPROVED",
        )


# ---------------------------------------------------------------------------
# 9. Allowed when on_leave employee exists
# ---------------------------------------------------------------------------

def test_w94_allowed_when_on_leave_employee_exists():
    """on_leave employee counts as payable — guard must pass."""
    employees = [
        {"id": 20, "status": "terminated"},  # doesn't count
        {"id": 21, "status": "on_leave"},    # counts
    ]
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        return_value=employees,
    ):
        _check_active_employees_exist_for_payroll_approval(
            tenant_id=5,
            cycle_id=201,
            target_status="APPROVED",
        )


# ---------------------------------------------------------------------------
# 10. Guard is surgical: non-APPROVED transitions skip employee check
# ---------------------------------------------------------------------------

def test_w94_guard_surgical_non_approval_skips_check():
    """CALCULATING is not in _PAYROLL_APPROVAL_GATE_STATUSES — guard must return immediately."""
    lookup_called = False

    def mock_list(entity, tenant_id):
        nonlocal lookup_called
        if entity == "hr_employees":
            lookup_called = True
        return []

    with patch("app.modules.hr_payroll.service.list_entities_for_tenant", side_effect=mock_list):
        # CALCULATING transition — should NOT hit guard
        _check_active_employees_exist_for_payroll_approval(
            tenant_id=6,
            cycle_id=300,
            target_status="CALCULATING",
        )

    assert not lookup_called, "hr_employees lookup must NOT be called for non-APPROVED transitions"


# ---------------------------------------------------------------------------
# 11. Error message contains ghost payroll rationale
# ---------------------------------------------------------------------------

def test_w94_error_message_contains_ghost_payroll_rationale():
    """DomainValidationError must explain ghost payroll risk and include cycle_id."""
    with patch(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_active_employees_exist_for_payroll_approval(
                tenant_id=7,
                cycle_id=999,
                target_status="APPROVED",
            )
    msg = str(exc_info.value)
    assert "999" in msg  # cycle_id for incident triage
    # Must communicate the financial risk
    assert "ghost" in msg.lower() or "fraudulent" in msg.lower() or "payroll" in msg.lower()
