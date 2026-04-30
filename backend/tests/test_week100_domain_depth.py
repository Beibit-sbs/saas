"""W100: advising session enrollment guard.

Guard: create_advising_session() requires student has active enrollment.
Cross-entity: advising_sessions × enrollments — fail-closed.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.modules.advising.service import (
    _ADVISING_ACTIVE_ENROLLMENT_STATUSES,
    _check_student_has_active_enrollment_for_advising,
)
from app.core.module_helpers.service_validation import DomainValidationError


TENANT_ID = 1
STUDENT_ID = 42


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

def test_active_enrollment_statuses_constant():
    assert isinstance(_ADVISING_ACTIVE_ENROLLMENT_STATUSES, frozenset)
    assert "enrolled" in _ADVISING_ACTIVE_ENROLLMENT_STATUSES
    assert "active" in _ADVISING_ACTIVE_ENROLLMENT_STATUSES
    assert "registered" in _ADVISING_ACTIVE_ENROLLMENT_STATUSES


def test_inactive_statuses_not_in_constant():
    assert "withdrawn" not in _ADVISING_ACTIVE_ENROLLMENT_STATUSES
    assert "graduated" not in _ADVISING_ACTIVE_ENROLLMENT_STATUSES
    assert "expelled" not in _ADVISING_ACTIVE_ENROLLMENT_STATUSES
    assert "suspended" not in _ADVISING_ACTIVE_ENROLLMENT_STATUSES


# ---------------------------------------------------------------------------
# 2. Block: no enrollments at all
# ---------------------------------------------------------------------------

def test_guard_blocks_when_no_enrollments_exist():
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=[]
    ):
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_blocks_when_student_has_no_enrollments_but_others_exist():
    other_student = [{"id": 1, "student_id": 99, "status": "enrolled"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=other_student
    ):
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


# ---------------------------------------------------------------------------
# 3. Block: inactive enrollment statuses
# ---------------------------------------------------------------------------

def test_guard_blocks_withdrawn_student():
    enrollments = [{"id": 1, "student_id": STUDENT_ID, "status": "withdrawn"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_blocks_graduated_student():
    enrollments = [{"id": 2, "student_id": STUDENT_ID, "status": "graduated"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_blocks_expelled_student():
    enrollments = [{"id": 3, "student_id": STUDENT_ID, "status": "expelled"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        with pytest.raises(DomainValidationError, match="no active enrollment"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_error_message_contains_student_id():
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=[]
    ):
        with pytest.raises(DomainValidationError, match=f"student_id={STUDENT_ID}"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


# ---------------------------------------------------------------------------
# 4. Allow: active enrollment statuses
# ---------------------------------------------------------------------------

def test_guard_allows_enrolled_student():
    enrollments = [{"id": 10, "student_id": STUDENT_ID, "status": "enrolled"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        # Must not raise
        _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_allows_active_student():
    enrollments = [{"id": 11, "student_id": STUDENT_ID, "status": "active"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_allows_registered_student():
    enrollments = [{"id": 12, "student_id": STUDENT_ID, "status": "registered"}]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


def test_guard_allows_student_with_mixed_enrollments_if_one_active():
    enrollments = [
        {"id": 20, "student_id": STUDENT_ID, "status": "withdrawn"},
        {"id": 21, "student_id": STUDENT_ID, "status": "enrolled"},
    ]
    with patch(
        "app.modules.advising.service.list_entities_for_tenant", return_value=enrollments
    ):
        _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


# ---------------------------------------------------------------------------
# 5. Fail-closed: query failure blocks action
# ---------------------------------------------------------------------------

def test_guard_fail_closed_on_enrollment_query_error():
    with patch(
        "app.modules.advising.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB connection lost"),
    ):
        with pytest.raises(DomainValidationError, match="enrollments query failed"):
            _check_student_has_active_enrollment_for_advising(TENANT_ID, STUDENT_ID)


# ---------------------------------------------------------------------------
# 6. Guard wired in create_advising_session — source inspection
# ---------------------------------------------------------------------------

def test_guard_wired_in_create_advising_session():
    import inspect
    from app.modules.advising import service as svc

    source = inspect.getsource(svc.create_advising_session)
    assert "_check_student_has_active_enrollment_for_advising" in source, (
        "W100 guard must be called inside create_advising_session"
    )


def test_guard_called_before_persist_in_create():
    import inspect
    from app.modules.advising import service as svc

    source = inspect.getsource(svc.create_advising_session)
    guard_pos = source.index("_check_student_has_active_enrollment_for_advising")
    persist_pos = source.index("create_entity_for_tenant")
    assert guard_pos < persist_pos, (
        "W100 guard must be wired BEFORE create_entity_for_tenant (guard before persist)"
    )
