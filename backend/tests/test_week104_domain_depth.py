"""W104 — Student Life Disciplinary Case Enrollment Guard.

Cross-entity invariant: student_life_disciplinary_cases × enrollments.

A disciplinary case may only be opened for a student with an active enrollment
record. Cases with severity=high/critical auto-trigger escalation alerts and
Brain Core events. Creating cases for ghost/expelled students generates phantom
disciplinary proceedings and corrupts institutional analytics.

Guard location: student_life/service.py ::
    _check_student_is_enrolled_for_disciplinary (called BEFORE create_entity_for_tenant)
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.student_life.service import (
    _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES,
    _check_student_is_enrolled_for_disciplinary,
    create_disciplinary_case,
)
from app.modules.student_life.schemas import DisciplinaryCaseCreateSchema

TENANT_ID = 9004

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enrollment(student_id: str, status: str, eid: int = 1) -> dict:
    return {"id": eid, "student_id": student_id, "status": status}


def _case_request(
    student_id: str = "STU-001",
    severity: str = "medium",
    status: str = "reported",
) -> DisciplinaryCaseCreateSchema:
    return DisciplinaryCaseCreateSchema(
        incident_code=f"INC-{student_id}-001",
        student_id=student_id,
        incident_type="misconduct",
        severity=severity,
        status=status,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Constants smoke tests
# ---------------------------------------------------------------------------

def test_constants_active_enrollment_statuses():
    assert "enrolled" in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES
    assert "active" in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES
    assert "registered" in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES


def test_constants_ineligible_statuses_not_active():
    assert "withdrawn" not in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES
    assert "expelled" not in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES
    assert "graduated" not in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES
    assert "suspended" not in _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES


# ---------------------------------------------------------------------------
# Guard unit tests — direct _check_ function
# ---------------------------------------------------------------------------

def test_guard_enrolled_student_passes(monkeypatch):
    """Student with active enrollment → no raise."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-001", "enrolled")] if table == "enrollments" else [],
    )
    _check_student_is_enrolled_for_disciplinary(
        tenant_id=TENANT_ID,
        student_id="STU-001",
        severity="medium",
    )


def test_guard_active_status_passes(monkeypatch):
    """Student with status='active' → no raise."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-002", "active")] if table == "enrollments" else [],
    )
    _check_student_is_enrolled_for_disciplinary(
        tenant_id=TENANT_ID,
        student_id="STU-002",
        severity="high",
    )


def test_guard_registered_status_passes(monkeypatch):
    """Student with status='registered' → no raise."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-003", "registered")] if table == "enrollments" else [],
    )
    _check_student_is_enrolled_for_disciplinary(
        tenant_id=TENANT_ID,
        student_id="STU-003",
        severity="low",
    )


def test_guard_no_enrollment_records_blocks(monkeypatch):
    """Student with no enrollment records at all → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="no enrollment records found"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-GHOST",
            severity="critical",
        )


def test_guard_withdrawn_student_blocks(monkeypatch):
    """Student with withdrawn enrollment → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-WD", "withdrawn")] if table == "enrollments" else [],
    )
    with pytest.raises(DomainValidationError, match="no active enrollment found"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-WD",
            severity="high",
        )


def test_guard_expelled_student_blocks(monkeypatch):
    """Expelled student → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-EXP", "expelled")] if table == "enrollments" else [],
    )
    with pytest.raises(DomainValidationError, match="no active enrollment found"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-EXP",
            severity="critical",
        )


def test_guard_graduated_student_blocks(monkeypatch):
    """Graduated student → DomainValidationError (no open disciplinary allowed post-graduation)."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-GRAD", "graduated")] if table == "enrollments" else [],
    )
    with pytest.raises(DomainValidationError, match="no active enrollment found"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-GRAD",
            severity="medium",
        )


def test_guard_mixed_enrollments_one_active_passes(monkeypatch):
    """Student with withdrawn + active enrollment → allowed (surgical)."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: (
            [_enrollment("STU-MIX", "withdrawn", 1), _enrollment("STU-MIX", "enrolled", 2)]
            if table == "enrollments" else []
        ),
    )
    # Must not raise
    _check_student_is_enrolled_for_disciplinary(
        tenant_id=TENANT_ID,
        student_id="STU-MIX",
        severity="low",
    )


def test_guard_different_student_enrollment_does_not_count(monkeypatch):
    """Active enrollment for a different student_id must NOT satisfy the guard."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [_enrollment("STU-OTHER", "enrolled")] if table == "enrollments" else [],
    )
    with pytest.raises(DomainValidationError, match="no enrollment records found"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-TARGET",
            severity="high",
        )


def test_guard_fail_closed_on_query_error(monkeypatch):
    """If enrollments query raises, guard must raise DomainValidationError (fail-closed)."""
    def boom(table, tid):
        raise RuntimeError("DB unreachable")

    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        boom,
    )
    with pytest.raises(DomainValidationError, match="enrollments lookup failed"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-ERR",
            severity="critical",
        )


def test_guard_error_message_includes_student_id(monkeypatch):
    """Error message must clearly identify the student_id that failed."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="STU-MSG-TEST"):
        _check_student_is_enrolled_for_disciplinary(
            tenant_id=TENANT_ID,
            student_id="STU-MSG-TEST",
            severity="critical",
        )


# ---------------------------------------------------------------------------
# Integration tests — full create_disciplinary_case pathway
# ---------------------------------------------------------------------------

def test_create_disciplinary_case_blocked_when_no_enrollment(monkeypatch):
    """create_disciplinary_case must raise DomainValidationError when student not enrolled."""
    monkeypatch.setattr(
        "app.modules.student_life.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="STU-NOENROLL"):
        create_disciplinary_case(
            TENANT_ID,
            _case_request(student_id="STU-NOENROLL", severity="high"),
            actor="admin",
        )


def test_create_disciplinary_case_allowed_with_active_enrollment(monkeypatch):
    """create_disciplinary_case must succeed when student has active enrollment."""
    persisted: list[dict] = []

    def fake_list(table, tid):
        if table == "enrollments":
            return [_enrollment("STU-OK", "enrolled")]
        return []

    def fake_create(table, payload, tid):
        row = {"id": 1, "tenant_id": str(tid), **payload}
        persisted.append(row)
        return row

    monkeypatch.setattr("app.modules.student_life.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.student_life.service.create_entity_for_tenant", fake_create)

    result = create_disciplinary_case(
        TENANT_ID,
        _case_request(student_id="STU-OK", severity="medium"),
        actor="admin",
    )
    assert result.student_id == "STU-OK"
    assert persisted, "create_entity_for_tenant must have been called"


def test_create_disciplinary_case_guard_fires_before_persist(monkeypatch):
    """Guard must fire BEFORE create_entity_for_tenant — no record created on block."""
    persisted: list[dict] = []

    def fake_list(table, tid):
        return []  # no enrollments

    def fake_create(table, payload, tid):
        persisted.append(payload)
        return {"id": 99, **payload}

    monkeypatch.setattr("app.modules.student_life.service.list_entities_for_tenant", fake_list)
    monkeypatch.setattr("app.modules.student_life.service.create_entity_for_tenant", fake_create)

    with pytest.raises(DomainValidationError):
        create_disciplinary_case(
            TENANT_ID,
            _case_request(student_id="STU-NP", severity="critical"),
            actor="admin",
        )

    assert not persisted, "create_entity_for_tenant must NOT be called when guard blocks"
