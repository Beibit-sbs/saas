"""W75 — courses: prerequisite enforcement at enrollment time.

Gap: CourseModel has no prerequisite data and enroll_student() has no guard.
Fix: CoursePrerequisiteModel + _check_course_prerequisites() cross-entity guard
     in EnrollmentLifecycleService.enroll_student().

Cross-entity: enrollments × courses.prerequisites × enrollments(COMPLETED)
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_prereq(prerequisite_course_id: int) -> MagicMock:
    p = MagicMock()
    p.prerequisite_course_id = prerequisite_course_id
    return p


def _make_service(prereq_list: list, completed_count: int):
    """Build EnrollmentLifecycleService with mocked DB for prerequisite tests."""
    from app.modules.enrollments.service import EnrollmentLifecycleService

    db = MagicMock()
    # first db.execute chain ends with .scalars().all() — returns prereq_list
    db.execute.return_value.scalars.return_value.all.return_value = prereq_list
    # subsequent db.execute chains end with .scalar() — returns completed_count
    db.execute.return_value.scalar.return_value = completed_count
    return EnrollmentLifecycleService(db)


# ---------------------------------------------------------------------------
# test 1: CoursePrerequisiteModel is importable and has correct fields
# ---------------------------------------------------------------------------

def test_w75_course_prerequisite_model_has_required_fields():
    from app.modules.courses.models import CoursePrerequisiteModel
    assert hasattr(CoursePrerequisiteModel, "id")
    assert hasattr(CoursePrerequisiteModel, "tenant_id")
    assert hasattr(CoursePrerequisiteModel, "course_id")
    assert hasattr(CoursePrerequisiteModel, "prerequisite_course_id")
    assert CoursePrerequisiteModel.__tablename__ == "university_course_prerequisites"


# ---------------------------------------------------------------------------
# test 2: No prerequisites defined → enrollment proceeds without error
# ---------------------------------------------------------------------------

def test_w75_no_prerequisites_allows_enrollment():
    svc = _make_service(prereq_list=[], completed_count=0)
    # Should not raise when no prerequisites exist for the course
    svc._check_course_prerequisites(tenant_id=1, student_profile_id=5, course_id=200)


# ---------------------------------------------------------------------------
# test 3: Prerequisite not completed → DomainValidationError raised
# ---------------------------------------------------------------------------

def test_w75_prerequisite_not_completed_blocks_enrollment():
    from app.core.module_helpers.service_validation import DomainValidationError

    prereqs = [_make_prereq(prerequisite_course_id=100)]
    svc = _make_service(prereq_list=prereqs, completed_count=0)

    with pytest.raises(DomainValidationError, match="Prerequisite courses not completed"):
        svc._check_course_prerequisites(tenant_id=1, student_profile_id=5, course_id=201)


# ---------------------------------------------------------------------------
# test 4: Prerequisite completed → enrollment proceeds
# ---------------------------------------------------------------------------

def test_w75_prerequisite_completed_allows_enrollment():
    prereqs = [_make_prereq(prerequisite_course_id=100)]
    svc = _make_service(prereq_list=prereqs, completed_count=1)

    # Should not raise when the prerequisite has a COMPLETED enrollment
    svc._check_course_prerequisites(tenant_id=1, student_profile_id=5, course_id=201)


# ---------------------------------------------------------------------------
# test 5: Multiple prerequisites — all missing → error lists all missing IDs
# ---------------------------------------------------------------------------

def test_w75_multiple_prerequisites_error_lists_all_missing_course_ids():
    from app.core.module_helpers.service_validation import DomainValidationError

    prereqs = [
        _make_prereq(prerequisite_course_id=98),
        _make_prereq(prerequisite_course_id=99),
    ]
    svc = _make_service(prereq_list=prereqs, completed_count=0)

    with pytest.raises(DomainValidationError) as exc_info:
        svc._check_course_prerequisites(tenant_id=1, student_profile_id=5, course_id=202)

    msg = str(exc_info.value)
    assert "98" in msg
    assert "99" in msg
    assert "missing completed enrollment" in msg


# ---------------------------------------------------------------------------
# test 6: Error message names the target course_id for actionable feedback
# ---------------------------------------------------------------------------

def test_w75_error_message_names_target_course_id():
    from app.core.module_helpers.service_validation import DomainValidationError

    prereqs = [_make_prereq(prerequisite_course_id=55)]
    svc = _make_service(prereq_list=prereqs, completed_count=0)

    with pytest.raises(DomainValidationError) as exc_info:
        svc._check_course_prerequisites(tenant_id=1, student_profile_id=7, course_id=300)

    msg = str(exc_info.value)
    assert "course_id=300" in msg, f"Expected 'course_id=300' in error: {msg}"
    assert "55" in msg, f"Expected missing prereq ID 55 in error: {msg}"
