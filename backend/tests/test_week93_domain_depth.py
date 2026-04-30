"""W93 — exam_governance: Exam Activation Guard (FSM + Faculty Contract Cross-Entity).

GUARDED INVARIANT:
    An exam cannot be moved to `in_progress` (activated) unless:
    1. The FSM allows the transition from the current status.
    2. The assigned faculty member has at least one active employment contract.

TESTS:
    1. test_w93_fsm_constants_present          — _ALLOWED_EXAM_STATUS_TRANSITIONS and activation constants exist
    2. test_w93_faculty_contract_statuses_set  — _FACULTY_ACTIVE_CONTRACT_STATUSES is frozenset with correct members
    3. test_w93_blocked_invalid_fsm_transition — completed→in_progress raises DomainValidationError (terminal state)
    4. test_w93_blocked_cancelled_is_terminal  — cancelled→any raises DomainValidationError
    5. test_w93_blocked_activation_missing_faculty — faculty_id empty → DomainValidationError before persist
    6. test_w93_blocked_activation_faculty_lookup_fails — contracts query error → DomainValidationError (fail-closed)
    7. test_w93_blocked_activation_no_active_contract — faculty has only terminated contract → blocked
    8. test_w93_activation_allowed_with_active_contract — valid transition + active contract → success
    9. test_w93_guard_surgical_non_activation_skips_contract — in_progress→completed skips faculty lookup
   10. test_w93_error_message_contains_faculty_id — error message includes faculty_id for traceability
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.exam_governance.service import (
    _ALLOWED_EXAM_STATUS_TRANSITIONS,
    _EXAM_ACTIVATION_STATUSES,
    _FACULTY_ACTIVE_CONTRACT_STATUSES,
    _check_faculty_has_active_contract_for_exam_activation,
    update_exam,
)
from app.modules.exam_governance.schemas import ExamUpdateSchema


# ---------------------------------------------------------------------------
# 1. FSM constants present
# ---------------------------------------------------------------------------

def test_w93_fsm_constants_present():
    """_ALLOWED_EXAM_STATUS_TRANSITIONS must exist with all lifecycle states."""
    assert isinstance(_ALLOWED_EXAM_STATUS_TRANSITIONS, dict)
    assert "scheduled" in _ALLOWED_EXAM_STATUS_TRANSITIONS
    assert "in_progress" in _ALLOWED_EXAM_STATUS_TRANSITIONS
    assert "completed" in _ALLOWED_EXAM_STATUS_TRANSITIONS
    assert "cancelled" in _ALLOWED_EXAM_STATUS_TRANSITIONS
    # Terminal states must have empty frozensets
    assert _ALLOWED_EXAM_STATUS_TRANSITIONS["completed"] == frozenset()
    assert _ALLOWED_EXAM_STATUS_TRANSITIONS["cancelled"] == frozenset()
    # scheduled → in_progress must be allowed
    assert "in_progress" in _ALLOWED_EXAM_STATUS_TRANSITIONS["scheduled"]
    # in_progress → completed must be allowed
    assert "completed" in _ALLOWED_EXAM_STATUS_TRANSITIONS["in_progress"]
    # Activation constant must exist
    assert isinstance(_EXAM_ACTIVATION_STATUSES, frozenset)
    assert "in_progress" in _EXAM_ACTIVATION_STATUSES


# ---------------------------------------------------------------------------
# 2. Faculty contract statuses set
# ---------------------------------------------------------------------------

def test_w93_faculty_contract_statuses_set():
    """_FACULTY_ACTIVE_CONTRACT_STATUSES must be a frozenset with expected values."""
    assert isinstance(_FACULTY_ACTIVE_CONTRACT_STATUSES, frozenset)
    assert "active" in _FACULTY_ACTIVE_CONTRACT_STATUSES
    # Terminated/expired status must NOT be in the set
    assert "terminated" not in _FACULTY_ACTIVE_CONTRACT_STATUSES
    assert "expired" not in _FACULTY_ACTIVE_CONTRACT_STATUSES


# ---------------------------------------------------------------------------
# 3. FSM blocks invalid transition: completed → in_progress
# ---------------------------------------------------------------------------

def test_w93_blocked_invalid_fsm_transition():
    """completed is a terminal state; any transition from it must raise DomainValidationError."""
    completed_exam = {"id": 1, "status": "completed", "faculty_id": "FAC-01", "tenant_id": 99}
    payload = ExamUpdateSchema(status="in_progress")

    with patch(
        "app.modules.exam_governance.service.list_entities_for_tenant",
        return_value=[completed_exam],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            update_exam(
                tenant_id=99,
                exam_id=1,
                payload=payload,
                actor="test-actor",
            )
    assert "terminal" in str(exc_info.value).lower() or "none" in str(exc_info.value).lower()
    assert "completed" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. FSM blocks cancelled → any
# ---------------------------------------------------------------------------

def test_w93_blocked_cancelled_is_terminal():
    """cancelled is a terminal state; moving to scheduled must raise DomainValidationError."""
    cancelled_exam = {"id": 2, "status": "cancelled", "faculty_id": "FAC-02", "tenant_id": 99}
    payload = ExamUpdateSchema(status="scheduled")

    with patch(
        "app.modules.exam_governance.service.list_entities_for_tenant",
        return_value=[cancelled_exam],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            update_exam(
                tenant_id=99,
                exam_id=2,
                payload=payload,
                actor="test-actor",
            )
    assert "cancelled" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Guard blocks activation when faculty_id is empty
# ---------------------------------------------------------------------------

def test_w93_blocked_activation_missing_faculty():
    """Empty faculty_id must raise DomainValidationError when activating an exam."""
    with pytest.raises(DomainValidationError) as exc_info:
        _check_faculty_has_active_contract_for_exam_activation(
            tenant_id=1,
            faculty_id="",
            exam_id=10,
            target_status="in_progress",
        )
    msg = str(exc_info.value)
    assert "faculty_id" in msg
    assert "missing" in msg.lower() or "empty" in msg.lower()


# ---------------------------------------------------------------------------
# 6. Guard fails closed when contracts query raises
# ---------------------------------------------------------------------------

def test_w93_blocked_activation_faculty_lookup_fails():
    """When faculty_contracts lookup raises, guard must raise DomainValidationError (fail-closed)."""
    with patch(
        "app.modules.exam_governance.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB connection lost"),
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_exam_activation(
                tenant_id=1,
                faculty_id="FAC-99",
                exam_id=5,
                target_status="in_progress",
            )
    msg = str(exc_info.value)
    assert "faculty_contracts" in msg
    assert "lookup failed" in msg.lower() or "failed" in msg.lower()


# ---------------------------------------------------------------------------
# 7. Guard blocks when faculty has only terminated contract
# ---------------------------------------------------------------------------

def test_w93_blocked_activation_no_active_contract():
    """Faculty with only terminated contract must be blocked from activating an exam."""
    terminated_contract = {"faculty_id": "FAC-10", "status": "terminated", "tenant_id": 1}

    with patch(
        "app.modules.exam_governance.service.list_entities_for_tenant",
        return_value=[terminated_contract],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_exam_activation(
                tenant_id=1,
                faculty_id="FAC-10",
                exam_id=7,
                target_status="in_progress",
            )
    msg = str(exc_info.value)
    assert "no active" in msg.lower() or "active" in msg.lower()
    assert "FAC-10" in msg


# ---------------------------------------------------------------------------
# 8. Activation allowed when faculty has active contract
# ---------------------------------------------------------------------------

def test_w93_activation_allowed_with_active_contract():
    """Valid scheduled→in_progress transition with active faculty contract must succeed."""
    scheduled_exam = {"id": 3, "status": "scheduled", "faculty_id": "FAC-20", "tenant_id": 2}
    active_contract = {"faculty_id": "FAC-20", "status": "active", "tenant_id": 2}
    updated_row = {**scheduled_exam, "status": "in_progress"}

    call_count = 0

    def mock_list(entity, tenant_id):
        nonlocal call_count
        call_count += 1
        if entity == "exams":
            return [scheduled_exam]
        if entity == "faculty_contracts":
            return [active_contract]
        return []

    with patch("app.modules.exam_governance.service.list_entities_for_tenant", side_effect=mock_list):
        with patch("app.modules.exam_governance.service.update_entity_for_tenant", return_value=updated_row):
            with patch("app.modules.exam_governance.service.log_admin_action"):
                payload = ExamUpdateSchema(status="in_progress")
                result = update_exam(tenant_id=2, exam_id=3, payload=payload, actor="admin")

    assert result.status == "in_progress"


# ---------------------------------------------------------------------------
# 9. Guard is surgical: in_progress → completed does NOT check faculty contracts
# ---------------------------------------------------------------------------

def test_w93_guard_surgical_non_activation_skips_contract():
    """When transitioning in_progress→completed, faculty contract lookup must NOT be called."""
    in_progress_exam = {"id": 4, "status": "in_progress", "faculty_id": "FAC-30", "tenant_id": 3}
    updated_row = {**in_progress_exam, "status": "completed"}

    contract_lookup_called = False

    def mock_list(entity, tenant_id):
        nonlocal contract_lookup_called
        if entity == "faculty_contracts":
            contract_lookup_called = True
        if entity == "exams":
            return [in_progress_exam]
        return []

    with patch("app.modules.exam_governance.service.list_entities_for_tenant", side_effect=mock_list):
        with patch("app.modules.exam_governance.service.update_entity_for_tenant", return_value=updated_row):
            with patch("app.modules.exam_governance.service.log_admin_action"):
                payload = ExamUpdateSchema(status="completed")
                result = update_exam(tenant_id=3, exam_id=4, payload=payload, actor="admin")

    assert result.status == "completed"
    assert not contract_lookup_called, "Faculty contract lookup must NOT be called for non-activation transitions"


# ---------------------------------------------------------------------------
# 10. Error message includes faculty_id for traceability
# ---------------------------------------------------------------------------

def test_w93_error_message_contains_faculty_id():
    """DomainValidationError on blocked activation must contain the faculty_id for triage."""
    expired_contract = {"faculty_id": "FAC-TRACE-42", "status": "expired", "tenant_id": 5}

    with patch(
        "app.modules.exam_governance.service.list_entities_for_tenant",
        return_value=[expired_contract],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_exam_activation(
                tenant_id=5,
                faculty_id="FAC-TRACE-42",
                exam_id=99,
                target_status="in_progress",
            )
    assert "FAC-TRACE-42" in str(exc_info.value)
    assert "99" in str(exc_info.value)  # exam_id present for triage
