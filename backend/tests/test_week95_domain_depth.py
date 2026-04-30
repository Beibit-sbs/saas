"""W95 — career_services: Active Enrollment Guard on Career Opportunity Creation.

Real-world invariant:
  Only actively-enrolled students may use institutional career placement services.
  A withdrawn, dropped, or expelled student has no entitlement to career matching.

Guard: _check_student_is_actively_enrolled_for_career_opportunity
  - Fail-closed: enrollment lookup failure → DomainValidationError
  - No enrollment records at all → DomainValidationError
  - Only non-active statuses (dropped/withdrawn/completed) → DomainValidationError
  - At least one enrolled/active/registered → guard passes
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# Test 1: constant exists and contains the three expected active statuses
# ---------------------------------------------------------------------------
def test_w95_career_access_enrollment_statuses_constant() -> None:
    from app.modules.career_services.service import _CAREER_ACCESS_ENROLLMENT_STATUSES

    assert isinstance(_CAREER_ACCESS_ENROLLMENT_STATUSES, frozenset)
    assert "enrolled" in _CAREER_ACCESS_ENROLLMENT_STATUSES
    assert "active" in _CAREER_ACCESS_ENROLLMENT_STATUSES
    assert "registered" in _CAREER_ACCESS_ENROLLMENT_STATUSES
    # disqualifying statuses must NOT be in the active set
    assert "dropped" not in _CAREER_ACCESS_ENROLLMENT_STATUSES
    assert "withdrawn" not in _CAREER_ACCESS_ENROLLMENT_STATUSES
    assert "completed" not in _CAREER_ACCESS_ENROLLMENT_STATUSES


# ---------------------------------------------------------------------------
# Test 2: guard function exists and is callable
# ---------------------------------------------------------------------------
def test_w95_guard_function_exists_and_callable() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    assert callable(_check_student_is_actively_enrolled_for_career_opportunity)


# ---------------------------------------------------------------------------
# Test 3: blocked when no enrollment records exist for the student (fail-closed)
# ---------------------------------------------------------------------------
def test_w95_blocked_when_no_enrollment_records() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[],  # no enrollments at all
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=42,
                opportunity_type="internship",
            )
    assert "42" in str(exc_info.value)
    assert "enrollment" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 4: blocked when student only has dropped enrollment
# ---------------------------------------------------------------------------
def test_w95_blocked_when_only_dropped_enrollment() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 42, "status": "dropped", "id": 10}],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=42,
                opportunity_type="job",
            )
    assert "42" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 5: blocked when student only has withdrawn enrollment
# ---------------------------------------------------------------------------
def test_w95_blocked_when_only_withdrawn_enrollment() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 42, "status": "withdrawn", "id": 11}],
    ):
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=42,
                opportunity_type="internship",
            )


# ---------------------------------------------------------------------------
# Test 6: blocked when student only has completed enrollment
# ---------------------------------------------------------------------------
def test_w95_blocked_when_only_completed_enrollment() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 42, "status": "completed", "id": 12}],
    ):
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=42,
                opportunity_type="mentorship",
            )


# ---------------------------------------------------------------------------
# Test 7: fail-closed — enrollment lookup raises exception → DomainValidationError
# ---------------------------------------------------------------------------
def test_w95_fail_closed_on_enrollment_lookup_error() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB connection lost"),
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=99,
                opportunity_type="job",
            )
    msg = str(exc_info.value)
    assert "99" in msg
    assert "enrollment" in msg.lower()


# ---------------------------------------------------------------------------
# Test 8: allowed when student has "enrolled" status
# ---------------------------------------------------------------------------
def test_w95_allowed_when_student_is_enrolled() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 42, "status": "enrolled", "id": 20}],
    ):
        # Should not raise
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=42,
            opportunity_type="internship",
        )


# ---------------------------------------------------------------------------
# Test 9: allowed when student has "active" status
# ---------------------------------------------------------------------------
def test_w95_allowed_when_student_is_active() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 77, "status": "active", "id": 21}],
    ):
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=77,
            opportunity_type="job",
        )


# ---------------------------------------------------------------------------
# Test 10: allowed when student has "registered" status
# ---------------------------------------------------------------------------
def test_w95_allowed_when_student_is_registered() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 55, "status": "registered", "id": 22}],
    ):
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=55,
            opportunity_type="work_study",
        )


# ---------------------------------------------------------------------------
# Test 11: allowed when student has mixed — one dropped + one enrolled
# (at least one active enrollment is sufficient)
# ---------------------------------------------------------------------------
def test_w95_allowed_when_mixed_statuses_one_active() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[
            {"student_id": 42, "status": "dropped", "id": 30},
            {"student_id": 42, "status": "enrolled", "id": 31},
        ],
    ):
        # One active enrollment is enough — guard should pass
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=42,
            opportunity_type="internship",
        )


# ---------------------------------------------------------------------------
# Test 12: error message contains opportunity_type for incident triage
# ---------------------------------------------------------------------------
def test_w95_error_message_contains_opportunity_type_and_student_id() -> None:
    from app.modules.career_services.service import (
        _check_student_is_actively_enrolled_for_career_opportunity,
    )

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[{"student_id": 1234, "status": "withdrawn", "id": 99}],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=1234,
                opportunity_type="internship",
            )
    msg = str(exc_info.value)
    assert "1234" in msg
    assert "internship" in msg
