"""W78 — grades: Enrollment ↔ Section data-model invariant.

Cross-entity invariant: grades × enrollments.section_id × scheduling.course_sections.status.
Grade submission is blocked unless enrollment has a concrete section linkage and section is active.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.grades.schemas import GradeSubmitSchema
from app.modules.grades.service import GradeLifecycleService


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _service() -> GradeLifecycleService:
    db = MagicMock()
    return GradeLifecycleService(db_session=db)


def _make_enrollment(
    enrollment_id: int = 42,
    course_id: int = 10,
    term_id: int = 5,
    section_id: int | None = 100,
    tenant_id: int = 1,
) -> MagicMock:
    e = MagicMock()
    e.id = enrollment_id
    e.course_id = course_id
    e.term_id = term_id
    e.section_id = section_id
    e.tenant_id = tenant_id
    return e


def _make_section(
    section_id: int = 100,
    status: str = "scheduled",
    course_id: int = 10,
    term_id: int = 5,
    tenant_id: int = 1,
    section_code: str = "A01",
) -> MagicMock:
    s = MagicMock()
    s.id = section_id
    s.course_id = course_id
    s.term_id = term_id
    s.tenant_id = tenant_id
    s.status = status
    s.section_code = section_code
    return s

# ---------------------------------------------------------------------------
# 1. GradeLifecycleService has _check_section_not_cancelled method
# ---------------------------------------------------------------------------

def test_w78_grade_service_has_section_not_cancelled_guard():
    assert hasattr(GradeLifecycleService, "_check_section_not_cancelled"), (
        "_check_section_not_cancelled not found on GradeLifecycleService"
    )


# ---------------------------------------------------------------------------
# 2. student in cancelled section -> BLOCK
# ---------------------------------------------------------------------------

def test_w78_blocked_when_single_section_cancelled():
    svc = _service()
    enrollment = _make_enrollment(enrollment_id=42, course_id=10, term_id=5, section_id=100)
    cancelled_section = _make_section(section_id=100, status="cancelled", section_code="A01")

    with patch("app.modules.grades.service.select", return_value=MagicMock()), \
         patch("app.modules.grades.service.and_", return_value=MagicMock()):
        svc.db.execute.return_value.scalar_one_or_none.return_value = cancelled_section
        svc._load_enrollment = MagicMock(return_value=enrollment)

        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_section_not_cancelled(tenant_id=1, enrollment_id=42)

    error_msg = str(exc_info.value)
    assert "not active" in error_msg.lower()
    assert "section_id=100" in error_msg


# ---------------------------------------------------------------------------
# 3. student in active section -> ALLOW
# ---------------------------------------------------------------------------

def test_w78_allowed_when_single_section_scheduled():
    svc = _service()
    enrollment = _make_enrollment(enrollment_id=42, course_id=10, term_id=5, section_id=100)
    scheduled_section = _make_section(section_id=100, status="scheduled", section_code="A01")

    with patch("app.modules.grades.service.select", return_value=MagicMock()), \
         patch("app.modules.grades.service.and_", return_value=MagicMock()):
        svc.db.execute.return_value.scalar_one_or_none.return_value = scheduled_section
        svc._load_enrollment = MagicMock(return_value=enrollment)

        svc._check_section_not_cancelled(tenant_id=1, enrollment_id=42)


# ---------------------------------------------------------------------------
# 4. mismatch (wrong section) -> BLOCK
# ---------------------------------------------------------------------------

def test_w78_blocked_when_section_mismatch_with_enrollment_course_term():
    svc = _service()
    enrollment = _make_enrollment(enrollment_id=42, course_id=10, term_id=5, section_id=100)
    wrong_section = _make_section(section_id=100, status="scheduled", course_id=11, term_id=5)

    with patch("app.modules.grades.service.select", return_value=MagicMock()), \
         patch("app.modules.grades.service.and_", return_value=MagicMock()):
        svc.db.execute.return_value.scalar_one_or_none.return_value = wrong_section
        svc._load_enrollment = MagicMock(return_value=enrollment)

        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_section_not_cancelled(tenant_id=1, enrollment_id=42)

    assert "mismatch" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 5. tenant isolation (section другого tenant) -> BLOCK
# ---------------------------------------------------------------------------

def test_w78_blocked_when_section_from_other_tenant():
    svc = _service()
    enrollment = _make_enrollment(enrollment_id=42, course_id=10, term_id=5, section_id=100)

    with patch("app.modules.grades.service.select", return_value=MagicMock()), \
         patch("app.modules.grades.service.and_", return_value=MagicMock()):
        svc.db.execute.return_value.scalar_one_or_none.return_value = None
        svc._load_enrollment = MagicMock(return_value=enrollment)

        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_section_not_cancelled(tenant_id=1, enrollment_id=42)

    assert "not found" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 6. no section_id -> BLOCK (data integrity)
# ---------------------------------------------------------------------------

def test_w78_blocked_when_no_section_id_on_enrollment():
    svc = _service()
    enrollment = _make_enrollment(enrollment_id=42, course_id=10, term_id=5, section_id=None)
    svc._load_enrollment = MagicMock(return_value=enrollment)

    with pytest.raises(DomainValidationError) as exc_info:
        svc._check_section_not_cancelled(tenant_id=1, enrollment_id=42)

    assert "no section_id" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 7. event not emitted before validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w78_submit_grade_does_not_emit_event_before_validation_failure():
    svc = _service()
    enrollment = _make_enrollment(enrollment_id=42, course_id=10, term_id=5, section_id=None)
    request = GradeSubmitSchema(
        enrollment_id=42,
        grading_scale_id=1,
        grade_code="A",
        grade_points=4,
    )

    with patch("app.modules.grades.service.assert_billing_write_allowed"), \
         patch("app.modules.grades.service.assert_quota_with_increment"), \
         patch("app.modules.grades.service.validate_grade_submission", new=AsyncMock(return_value=None)), \
         patch("app.modules.grades.service.EventPublisher") as event_publisher_cls:
        svc._load_enrollment = MagicMock(return_value=enrollment)
        svc._load_course = MagicMock(return_value=MagicMock())

        with pytest.raises(DomainValidationError):
            await svc.submit_grade(tenant_id=1, request=request, actor_id="instructor@example.com")

        event_publisher_cls.assert_not_called()
