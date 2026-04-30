"""W102 — Scholarship Application Enrollment Eligibility Guard.

Cross-entity invariant: scholarship_applications × enrollments.

A scholarship application may only be submitted for a student with at least
one active enrollment record. Institutional scholarships require enrollment —
disbursing funds to non-enrolled students is financial fraud and an audit violation.

Guard location: scholarship/service.py ::
    _check_student_is_enrolled_for_scholarship  (called BEFORE create_entity_for_tenant)
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.scholarship.service import (
    _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES,
    _check_student_is_enrolled_for_scholarship,
    create_scholarship_application,
)

TENANT_ID = 9002

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enrollment(student_id: str, status: str, enroll_id: int = 1) -> dict:
    return {"id": enroll_id, "student_id": student_id, "status": status}


def _payload(
    student_id: str = "STU-001",
    scholarship_type: str = "merit",
    gpa: float = 3.5,
    status: str = "pending",
) -> dict:
    return {
        "student_id": student_id,
        "scholarship_type": scholarship_type,
        "gpa": gpa,
        "status": status,
        "requested_amount": 5000.0,
    }


# ---------------------------------------------------------------------------
# Constants smoke tests
# ---------------------------------------------------------------------------

def test_constants_active_enrollment_statuses():
    assert "enrolled" in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES
    assert "active" in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES
    assert "registered" in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES


def test_constants_withdrawn_not_active():
    assert "withdrawn" not in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES
    assert "graduated" not in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES
    assert "expelled" not in _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES


# ---------------------------------------------------------------------------
# Guard unit tests — direct _check_ function
# ---------------------------------------------------------------------------

def test_guard_enrolled_student_passes(monkeypatch):
    """Student with 'enrolled' status → no raise."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-001", "enrolled")],
    )
    _check_student_is_enrolled_for_scholarship(
        tenant_id=TENANT_ID,
        student_id="STU-001",
        scholarship_type="merit",
    )


def test_guard_active_status_passes(monkeypatch):
    """Student with 'active' enrollment status → no raise."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-002", "active")],
    )
    _check_student_is_enrolled_for_scholarship(
        tenant_id=TENANT_ID,
        student_id="STU-002",
        scholarship_type="athletic",
    )


def test_guard_registered_status_passes(monkeypatch):
    """Student with 'registered' enrollment status → no raise."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-003", "registered")],
    )
    _check_student_is_enrolled_for_scholarship(
        tenant_id=TENANT_ID,
        student_id="STU-003",
        scholarship_type="merit",
    )


def test_guard_no_enrollment_records_blocks(monkeypatch):
    """Student with no enrollment records at all → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="no enrollment records found"):
        _check_student_is_enrolled_for_scholarship(
            tenant_id=TENANT_ID,
            student_id="STU-404",
            scholarship_type="merit",
        )


def test_guard_withdrawn_student_blocks(monkeypatch):
    """Student with only 'withdrawn' enrollment → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-005", "withdrawn")],
    )
    with pytest.raises(DomainValidationError, match="not actively enrolled"):
        _check_student_is_enrolled_for_scholarship(
            tenant_id=TENANT_ID,
            student_id="STU-005",
            scholarship_type="merit",
        )


def test_guard_graduated_student_blocks(monkeypatch):
    """Student with only 'graduated' enrollment → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-006", "graduated")],
    )
    with pytest.raises(DomainValidationError, match="not actively enrolled"):
        _check_student_is_enrolled_for_scholarship(
            tenant_id=TENANT_ID,
            student_id="STU-006",
            scholarship_type="athletic",
        )


def test_guard_expelled_student_blocks(monkeypatch):
    """Student with only 'expelled' enrollment → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-007", "expelled")],
    )
    with pytest.raises(DomainValidationError, match="not actively enrolled"):
        _check_student_is_enrolled_for_scholarship(
            tenant_id=TENANT_ID,
            student_id="STU-007",
            scholarship_type="merit",
        )


def test_guard_mixed_enrollments_one_active_passes(monkeypatch):
    """Student with withdrawn + enrolled → allowed (surgical — one active is enough)."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [
            _enrollment("STU-008", "withdrawn", enroll_id=1),
            _enrollment("STU-008", "enrolled", enroll_id=2),
        ],
    )
    # Must not raise
    _check_student_is_enrolled_for_scholarship(
        tenant_id=TENANT_ID,
        student_id="STU-008",
        scholarship_type="merit",
    )


def test_guard_different_student_enrollments_do_not_count(monkeypatch):
    """Enrollments for a different student_id must NOT satisfy the guard."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-OTHER", "enrolled")],
    )
    with pytest.raises(DomainValidationError, match="no enrollment records found"):
        _check_student_is_enrolled_for_scholarship(
            tenant_id=TENANT_ID,
            student_id="STU-009",
            scholarship_type="merit",
        )


def test_guard_fail_closed_on_query_error(monkeypatch):
    """If enrollments lookup raises, guard must raise DomainValidationError (fail-closed)."""
    def boom(table, tid):
        raise RuntimeError("DB connection lost")

    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        boom,
    )
    with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
        _check_student_is_enrolled_for_scholarship(
            tenant_id=TENANT_ID,
            student_id="STU-010",
            scholarship_type="merit",
        )


# ---------------------------------------------------------------------------
# Integration tests — full create_scholarship_application pathway
# ---------------------------------------------------------------------------

def test_create_application_blocked_when_not_enrolled(monkeypatch):
    """create_scholarship_application must raise DomainValidationError for non-enrolled student."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="STU-NE"):
        create_scholarship_application(
            _payload(student_id="STU-NE"),
            TENANT_ID,
        )


def test_create_application_allowed_when_enrolled(monkeypatch):
    """create_scholarship_application must succeed when student has active enrollment."""
    created_rows: list[dict] = []

    def fake_list(table, tid):
        if table == "enrollments":
            return [_enrollment("STU-OK", "enrolled")]
        return []

    def fake_create(table, payload, tid):
        row = {"id": 1, "tenant_id": str(tid), **payload}
        created_rows.append(row)
        return row

    monkeypatch.setattr("app.modules.scholarship.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.scholarship.service.create_entity_for_tenant", fake_create)

    result = create_scholarship_application(_payload(student_id="STU-OK"), TENANT_ID)
    assert result["student_id"] == "STU-OK"
    assert created_rows, "create_entity_for_tenant must have been called"


def test_create_application_blocked_before_persist(monkeypatch):
    """Guard must fire BEFORE create_entity_for_tenant — no record created on block."""
    persisted: list[dict] = []

    def fake_list(table, tid):
        return []  # no enrollments

    def fake_create(table, payload, tid):
        persisted.append(payload)
        return {"id": 99, **payload}

    monkeypatch.setattr("app.modules.scholarship.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.scholarship.service.create_entity_for_tenant", fake_create)

    with pytest.raises(DomainValidationError):
        create_scholarship_application(_payload(student_id="STU-NP"), TENANT_ID)

    assert not persisted, "create_entity_for_tenant must NOT be called when guard blocks"


def test_create_application_gpa_check_still_applies(monkeypatch):
    """GPA guard must still fire (not bypassed by enrollment guard) for enrolled students."""
    monkeypatch.setattr(
        "app.modules.scholarship.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-GPA", "enrolled")],
    )
    with pytest.raises(ValueError, match="gpa"):
        create_scholarship_application(
            _payload(student_id="STU-GPA", scholarship_type="merit", gpa=2.0),  # below 3.0
            TENANT_ID,
        )
