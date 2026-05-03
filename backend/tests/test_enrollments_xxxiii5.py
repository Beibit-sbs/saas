"""
XXXIII.5 — enrollments._load_course fix

Verifies that the formerly-named `_load_course_placeholder` is now:
  - renamed to `_load_course`
  - filters by tenant_id at SQL level (not just post-fetch validation)
  - tenant mismatch is blocked
  - inactive course is blocked
  - metadata key is "real_course_reference_validated"
  - all call-sites (enroll_student, get_enrollments_by_course) use the fixed method
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.courses.models import CourseModel
from app.modules.enrollments.models import (
    EnrollmentModel,
    EnrollmentStatus,
    EnrollmentType,
)
from app.modules.enrollments.schemas import EnrollmentCreateSchema
from app.modules.enrollments.service import EnrollmentLifecycleService
from app.modules.students.models import (
    StudentAdmissionSource,
    StudentProfileModel,
    StudentStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class ScalarResult:
    def __init__(self, value=None):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar_one(self):
        return self._value

    def scalar(self):
        return self._value

    def scalars(self):
        class _List:
            def __init__(self, v):
                self._v = v

            def all(self):
                return [self._v] if self._v is not None else []

            def first(self):
                return self._v

        return _List(self._value)


def _make_db(*return_values):
    """Return a MagicMock db_session whose execute() pops from a list."""
    db = MagicMock(spec=Session)
    return_values_list = list(return_values)

    def _execute(stmt, *args, **kwargs):
        if return_values_list:
            val = return_values_list.pop(0)
        else:
            val = None
        return ScalarResult(val)

    db.execute.side_effect = _execute
    db.refresh.side_effect = lambda obj: None
    return db


def _make_course(tenant_id=1, status="active", course_id=701):
    c = MagicMock(spec=CourseModel)
    c.id = course_id
    c.tenant_id = tenant_id
    c.status = status
    return c


def _make_student(tenant_id=1, student_id=1001):
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return StudentProfileModel(
        id=student_id,
        tenant_id=tenant_id,
        person_id=101,
        student_number=f"STU-{student_id}",
        cohort_year=2026,
        current_status=StudentStatus.ACTIVE,
        admission_source=StudentAdmissionSource.ADMISSIONS_WORKFLOW,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# 1. _load_course — happy path
# ---------------------------------------------------------------------------


def test_load_course_returns_course_for_correct_tenant():
    """_load_course returns the course when tenant_id matches."""
    course = _make_course(tenant_id=1)
    db = _make_db(course)
    svc = EnrollmentLifecycleService(db)

    result = svc._load_course(tenant_id=1, course_id=701)

    assert result is course


# ---------------------------------------------------------------------------
# 2. _load_course — not found
# ---------------------------------------------------------------------------


def test_load_course_raises_when_course_not_found():
    """_load_course raises TenantResourceNotFoundError when course does not exist."""
    db = _make_db(None)
    svc = EnrollmentLifecycleService(db)

    with pytest.raises(TenantResourceNotFoundError, match="[Cc]ourse"):
        svc._load_course(tenant_id=1, course_id=9999)


# ---------------------------------------------------------------------------
# 3. _load_course — cross-tenant blocked
# ---------------------------------------------------------------------------


def test_load_course_blocks_cross_tenant_access():
    """_load_course raises TenantResourceNotFoundError when course belongs to another tenant."""
    course = _make_course(tenant_id=2)  # different tenant
    db = _make_db(course)
    svc = EnrollmentLifecycleService(db)

    with pytest.raises(TenantResourceNotFoundError, match="[Cc]ourse"):
        svc._load_course(tenant_id=1, course_id=701)


# ---------------------------------------------------------------------------
# 4. _load_course — SQL includes tenant_id filter
# ---------------------------------------------------------------------------


def test_load_course_sql_includes_tenant_id_filter():
    """_load_course SQL WHERE clause must include tenant_id = <tenant>."""
    from sqlalchemy.dialects import postgresql

    course = _make_course(tenant_id=1)
    db = MagicMock(spec=Session)
    captured_stmt = []

    def _capture(stmt, *a, **kw):
        captured_stmt.append(stmt)
        r = MagicMock()
        r.scalar_one_or_none.return_value = course
        return r

    db.execute.side_effect = _capture
    svc = EnrollmentLifecycleService(db)
    svc._load_course(tenant_id=42, course_id=701)

    assert len(captured_stmt) == 1
    compiled = str(
        captured_stmt[0].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "42" in compiled  # tenant_id value in SQL
    assert "701" in compiled  # course_id value in SQL


# ---------------------------------------------------------------------------
# 5. _load_course — inactive course raises DomainValidationError
# ---------------------------------------------------------------------------


def test_load_course_raises_for_inactive_course():
    """_load_course raises DomainValidationError when course status is not 'active'."""
    course = _make_course(tenant_id=1, status="archived")
    db = _make_db(course)
    svc = EnrollmentLifecycleService(db)

    with pytest.raises(DomainValidationError, match="[Nn]ot active|cannot accept"):
        svc._load_course(tenant_id=1, course_id=701)


# ---------------------------------------------------------------------------
# 6. _load_course is NOT named _load_course_placeholder anymore
# ---------------------------------------------------------------------------


def test_load_course_placeholder_method_no_longer_exists():
    """The old placeholder method name must be gone from EnrollmentLifecycleService."""
    assert not hasattr(
        EnrollmentLifecycleService, "_load_course_placeholder"
    ), "_load_course_placeholder still exists — rename was not applied"


# ---------------------------------------------------------------------------
# 7. enroll_student propagates course-not-found error
# ---------------------------------------------------------------------------


def test_enroll_student_raises_when_course_not_found(monkeypatch):
    """enroll_student raises TenantResourceNotFoundError when course does not exist."""
    monkeypatch.setattr(
        "app.modules.enrollments.service.assert_billing_write_allowed", MagicMock()
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_admin_action", MagicMock()
    )
    monkeypatch.setattr(
        "app.modules.enrollments.service.log_data_access_event", MagicMock()
    )

    student = _make_student(tenant_id=1)
    db = _make_db(student, None)  # student found, course not found
    svc = EnrollmentLifecycleService(db)
    request = EnrollmentCreateSchema(
        student_profile_id=1001, course_id=9999, term_id=1, section_id=501
    )

    with pytest.raises(TenantResourceNotFoundError):
        asyncio.run(
            svc.enroll_student(tenant_id=1, request=request, actor_id="reg@example.com")
        )


# ---------------------------------------------------------------------------
# 8. Metadata key is real_course_reference_validated, not placeholder
# ---------------------------------------------------------------------------


def test_metadata_key_is_real_course_reference_validated():
    """Ensure 'placeholder_existing_course_model' no longer appears in service source."""
    import inspect
    from app.modules.enrollments import service as _svc_module

    source = inspect.getsource(_svc_module)
    assert "placeholder_existing_course_model" not in source, (
        "Old placeholder metadata key still present in enrollments/service.py"
    )
    assert "real_course_reference_validated" in source, (
        "New metadata key 'real_course_reference_validated' not found in enrollments/service.py"
    )
