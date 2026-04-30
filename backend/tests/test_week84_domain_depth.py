"""W84 — degree_progress: Program Requirement Item Course Existence Guard.

Cross-entity invariant: ProgramRequirementItemModel.course_id MUST reference a real course
in the tenant's course catalog (CourseModel). A phantom course_id creates a
permanently-unsatisfiable graduation requirement that blocks every student in the program.

Six behavioral tests covering: method existence, blocked when course not found,
allowed when course exists, error message content, cross-tenant isolation, and
guard integration in create_program_requirement_item().
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.degree_progress.service import DegreeProgressService
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_service() -> DegreeProgressService:
    db = MagicMock()
    return DegreeProgressService(db_session=db)


def _mock_course(course_id: int, tenant_id: int) -> MagicMock:
    c = MagicMock()
    c.id = course_id
    c.tenant_id = str(tenant_id)
    return c


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_w84_guard_and_create_methods_exist():
    """_check_course_exists_in_tenant and create_program_requirement_item must be present."""
    svc = _make_service()
    assert callable(getattr(svc, "_check_course_exists_in_tenant", None)), (
        "_check_course_exists_in_tenant not found on DegreeProgressService"
    )
    assert callable(getattr(svc, "create_program_requirement_item", None)), (
        "create_program_requirement_item not found on DegreeProgressService"
    )


def test_w84_blocked_when_course_not_in_catalog():
    """Guard raises DomainValidationError when course_id does not exist for the tenant."""
    svc = _make_service()
    svc.db.execute.return_value.scalar_one_or_none.return_value = None  # course not found

    with pytest.raises(DomainValidationError) as exc_info:
        with patch("app.modules.degree_progress.service.DegreeProgressService._check_course_exists_in_tenant",
                   wraps=svc._check_course_exists_in_tenant):
            svc._check_course_exists_in_tenant(tenant_id=10, course_id=999)

    assert "course_id=999" in str(exc_info.value)


def test_w84_allowed_when_course_exists():
    """Guard does not raise when course_id is found in the tenant's catalog."""
    svc = _make_service()
    svc.db.execute.return_value.scalar_one_or_none.return_value = _mock_course(42, 10)

    # Should not raise
    svc._check_course_exists_in_tenant(tenant_id=10, course_id=42)


def test_w84_error_message_contains_course_id_and_tenant_id():
    """Error message must identify course_id and tenant_id for operator actionability."""
    svc = _make_service()
    svc.db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(DomainValidationError) as exc_info:
        svc._check_course_exists_in_tenant(tenant_id=77, course_id=404)

    msg = str(exc_info.value)
    assert "course_id=404" in msg, f"course_id missing from error: {msg}"
    assert "tenant_id=77" in msg, f"tenant_id missing from error: {msg}"


def test_w84_different_tenant_course_not_found_is_blocked():
    """A course_id valid for tenant A but not tenant B must be blocked for tenant B."""
    svc = _make_service()
    # DB returns None — course not in tenant 99's catalog (belongs to another tenant)
    svc.db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(DomainValidationError):
        svc._check_course_exists_in_tenant(tenant_id=99, course_id=42)


def test_w84_blocked_when_courses_module_unavailable():
    """Guard raises DomainValidationError when courses module import fails."""
    svc = _make_service()
    
    with patch("app.modules.degree_progress.service.DegreeProgressService._check_course_exists_in_tenant") as mock_guard:
        mock_guard.side_effect = DomainValidationError("Cannot verify course_id=999 exists: courses module unavailable")
        
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_course_exists_in_tenant(tenant_id=10, course_id=999)
        
        assert "courses module unavailable" in str(exc_info.value)


def test_w84_create_item_calls_guard_and_persists():
    """create_program_requirement_item: guard fires, item added when course valid."""
    svc = _make_service()

    guard_calls = []

    def _fake_guard(tenant_id: int, course_id: int) -> None:
        guard_calls.append((tenant_id, course_id))

    svc._check_course_exists_in_tenant = _fake_guard

    svc.create_program_requirement_item(
        tenant_id=10,
        requirement_id=5,
        course_id=42,
        credits=3,
        required=True,
    )

    # Guard was called with correct tenant + course
    assert guard_calls == [(10, 42)], f"Guard not called correctly: {guard_calls}"
    # Item was added to the session
    svc.db.add.assert_called_once()
    added = svc.db.add.call_args[0][0]
    assert added.tenant_id == 10
    assert added.course_id == 42
    assert added.requirement_id == 5
    assert added.credits == 3
    assert added.required is True
