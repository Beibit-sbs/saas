"""W96 — alumni: Alumni Record Creation Requires Graduated Student Status.

Real-world invariant:
  An alumni record may only be created for a student who has the status 'graduated'.
  Creating alumni records for active, enrolled, withdrawn, or suspended students
  produces false entries in the alumni registry — misrepresenting institutional
  graduation rates and exposing the institution to accreditation and reputational risk.

Guard: _check_student_has_graduated_for_alumni_record
  - Fail-closed: student lookup failure → DomainValidationError
  - Student not found in registry → DomainValidationError
  - Student found but status not 'graduated' → DomainValidationError
  - Student status == 'graduated' → guard passes
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# Test 1: constant exists and contains only 'graduated'
# ---------------------------------------------------------------------------
def test_w96_alumni_eligible_statuses_constant() -> None:
    from app.modules.alumni.service import _ALUMNI_ELIGIBLE_STUDENT_STATUSES

    assert isinstance(_ALUMNI_ELIGIBLE_STUDENT_STATUSES, frozenset)
    assert "graduated" in _ALUMNI_ELIGIBLE_STUDENT_STATUSES
    # Non-graduate statuses must NOT qualify
    assert "active" not in _ALUMNI_ELIGIBLE_STUDENT_STATUSES
    assert "enrolled" not in _ALUMNI_ELIGIBLE_STUDENT_STATUSES
    assert "withdrawn" not in _ALUMNI_ELIGIBLE_STUDENT_STATUSES
    assert "suspended" not in _ALUMNI_ELIGIBLE_STUDENT_STATUSES
    assert "inactive" not in _ALUMNI_ELIGIBLE_STUDENT_STATUSES


# ---------------------------------------------------------------------------
# Test 2: guard function exists and is callable
# ---------------------------------------------------------------------------
def test_w96_guard_function_exists_and_callable() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    assert callable(_check_student_has_graduated_for_alumni_record)


# ---------------------------------------------------------------------------
# Test 3: blocked when no student records found (fail-closed)
# ---------------------------------------------------------------------------
def test_w96_blocked_when_no_student_records() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=42,
            )
    assert "42" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 4: blocked when student status is 'active' (still enrolled)
# ---------------------------------------------------------------------------
def test_w96_blocked_when_student_is_active() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 42, "student_id": 42, "status": "active"}],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=42,
            )
    assert "42" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 5: blocked when student status is 'enrolled'
# ---------------------------------------------------------------------------
def test_w96_blocked_when_student_is_enrolled() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 42, "student_id": 42, "status": "enrolled"}],
    ):
        with pytest.raises(DomainValidationError):
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=42,
            )


# ---------------------------------------------------------------------------
# Test 6: blocked when student status is 'withdrawn'
# ---------------------------------------------------------------------------
def test_w96_blocked_when_student_is_withdrawn() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 42, "student_id": 42, "status": "withdrawn"}],
    ):
        with pytest.raises(DomainValidationError):
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=42,
            )


# ---------------------------------------------------------------------------
# Test 7: blocked when student status is 'suspended'
# ---------------------------------------------------------------------------
def test_w96_blocked_when_student_is_suspended() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 42, "student_id": 42, "status": "suspended"}],
    ):
        with pytest.raises(DomainValidationError):
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=42,
            )


# ---------------------------------------------------------------------------
# Test 8: fail-closed — student lookup raises exception → DomainValidationError
# ---------------------------------------------------------------------------
def test_w96_fail_closed_on_student_lookup_error() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB timeout"),
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=99,
            )
    msg = str(exc_info.value)
    assert "99" in msg
    assert "graduation" in msg.lower() or "student" in msg.lower()


# ---------------------------------------------------------------------------
# Test 9: allowed when student status is 'graduated'
# ---------------------------------------------------------------------------
def test_w96_allowed_when_student_has_graduated() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 42, "student_id": 42, "status": "graduated"}],
    ):
        # Should not raise
        _check_student_has_graduated_for_alumni_record(
            tenant_id=1,
            student_id=42,
        )


# ---------------------------------------------------------------------------
# Test 10: student lookup uses "id" field (not only "student_id") for matching
# ---------------------------------------------------------------------------
def test_w96_allowed_when_student_matched_by_id_field() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    # Student record uses "id" field (not "student_id")
    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 77, "status": "graduated"}],
    ):
        _check_student_has_graduated_for_alumni_record(
            tenant_id=1,
            student_id=77,
        )


# ---------------------------------------------------------------------------
# Test 11: error message contains student_id and false registry rationale
# ---------------------------------------------------------------------------
def test_w96_error_message_contains_student_id_and_rationale() -> None:
    from app.modules.alumni.service import (
        _check_student_has_graduated_for_alumni_record,
    )

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[{"id": 1234, "student_id": 1234, "status": "active"}],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_has_graduated_for_alumni_record(
                tenant_id=1,
                student_id=1234,
            )
    msg = str(exc_info.value)
    assert "1234" in msg
    # Should contain registry / graduation rationale
    assert any(
        word in msg.lower()
        for word in ("graduated", "alumni", "registry", "graduation")
    )
