"""W83 — financial_aid: Disbursement Enrollment Verification Gate (SAP Rule).

Cross-entity invariant: financial_aid_records × enrollments.status.
update_financial_aid_status(→ disbursed) must be blocked when the student has
no active enrollment records.

Without this guard, aid can be disbursed to a fully withdrawn or dropped student,
violating Title IV SAP (Satisfactory Academic Progress) federal requirements and
creating institutional liability — funds must be returned, audits triggered.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.financial_aid.service import (
    _DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT,
    _SAP_ACTIVE_ENROLLMENT_STATUSES,
    _check_student_has_active_enrollment,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_enrollment(student_id: int, status: str) -> dict:
    return {"id": 1, "student_id": student_id, "status": status, "tenant_id": 1}


def _patch_enrollments(enrollments: list[dict]):
    return patch(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        return_value=enrollments,
    )


# ---------------------------------------------------------------------------
# Test 1: constants exist and are correctly typed
# ---------------------------------------------------------------------------

def test_w83_constants_exist():
    assert isinstance(_DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT, frozenset)
    assert "disbursed" in _DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT
    assert isinstance(_SAP_ACTIVE_ENROLLMENT_STATUSES, frozenset)
    assert "enrolled" in _SAP_ACTIVE_ENROLLMENT_STATUSES
    assert "rejected" not in _SAP_ACTIVE_ENROLLMENT_STATUSES


# ---------------------------------------------------------------------------
# Test 2: disbursement blocked when student has only withdrawn enrollments
# ---------------------------------------------------------------------------

def test_w83_disbursement_blocked_when_all_enrollments_withdrawn():
    enrollments = [
        _make_enrollment(101, "withdrawn"),
        _make_enrollment(101, "dropped"),
    ]
    with _patch_enrollments(enrollments):
        with pytest.raises(ValueError) as exc_info:
            _check_student_has_active_enrollment(tenant_id=1, student_id=101, term="2026-FALL")

    assert "101" in str(exc_info.value)
    assert "SAP" in str(exc_info.value) or "enrollment" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Test 3: disbursement allowed when student has an active enrollment
# ---------------------------------------------------------------------------

def test_w83_disbursement_allowed_when_enrolled():
    enrollments = [_make_enrollment(102, "enrolled")]
    with _patch_enrollments(enrollments):
        # Must not raise
        _check_student_has_active_enrollment(tenant_id=1, student_id=102, term="2026-FALL")


# ---------------------------------------------------------------------------
# Test 4: disbursement allowed for other SAP-active statuses (active, registered)
# ---------------------------------------------------------------------------

def test_w83_disbursement_allowed_for_all_active_statuses():
    for status in ("active", "registered"):
        enrollments = [_make_enrollment(103, status)]
        with _patch_enrollments(enrollments):
            _check_student_has_active_enrollment(tenant_id=1, student_id=103, term="2026-FALL")


# ---------------------------------------------------------------------------
# Test 5: safe-skip when student has no enrollment records in system
# ---------------------------------------------------------------------------

def test_w83_blocked_when_student_not_in_enrollment_system():
    """FAIL-CLOSED: Cannot verify enrollment → disbursement must be blocked."""
    # Tenant has other enrollments but not for this student
    enrollments = [_make_enrollment(999, "withdrawn")]
    with _patch_enrollments(enrollments):
        # HARDENING: Must raise ValueError (no silent fallback)
        with pytest.raises(ValueError) as exc_info:
            _check_student_has_active_enrollment(tenant_id=1, student_id=42, term="2026-FALL")

        msg = str(exc_info.value)
        assert "no enrollment records found" in msg.lower()
        assert "cannot verify" in msg.lower()


# ---------------------------------------------------------------------------
# Test 6: error message names student_id and term
# ---------------------------------------------------------------------------

def test_w83_error_message_names_student_and_term():
    enrollments = [_make_enrollment(200, "withdrawn")]
    with _patch_enrollments(enrollments):
        with pytest.raises(ValueError) as exc_info:
            _check_student_has_active_enrollment(tenant_id=1, student_id=200, term="2026-SPRING")

    msg = str(exc_info.value)
    assert "200" in msg
    assert "2026-SPRING" in msg
