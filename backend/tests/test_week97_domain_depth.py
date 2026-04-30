"""W97 — syllabus_governance: Syllabus approval requires course linked to active program.

Real-world invariant:
  A syllabus for a course with no active program backing is a dead syllabus.
  Approving it inflates the approved-curriculum count used in accreditation reports
  and misleads students / faculty about active offerings.

Guard: _check_course_linked_to_active_program_for_syllabus_approval
  - Returns early (no-op) for any status that is not "approved"
  - Fail-closed: any lookup exception → DomainValidationError
  - Blocks if syllabus has no course_code
  - Blocks if no course record matches the course_code
  - Blocks if all matching courses have program_id pointing to inactive/archived/draft programs
  - Passes only when at least one matching course is linked to an active program
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.syllabus_governance.service import (
    _PROGRAM_ACTIVE_STATUSES,
    _SYLLABUS_APPROVAL_TARGET_STATUS,
    _check_course_linked_to_active_program_for_syllabus_approval,
)

TENANT = 1
SYL_ID = 42
COURSE_CODE = "CS101"


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

def test_w97_program_active_statuses_constant():
    """Only 'active' qualifies; draft/inactive/archived must not be present."""
    assert "active" in _PROGRAM_ACTIVE_STATUSES
    assert "draft" not in _PROGRAM_ACTIVE_STATUSES
    assert "inactive" not in _PROGRAM_ACTIVE_STATUSES
    assert "archived" not in _PROGRAM_ACTIVE_STATUSES
    assert _SYLLABUS_APPROVAL_TARGET_STATUS == "approved"


# ---------------------------------------------------------------------------
# 2. Guard importable
# ---------------------------------------------------------------------------

def test_w97_guard_function_exists_and_callable():
    assert callable(_check_course_linked_to_active_program_for_syllabus_approval)


# ---------------------------------------------------------------------------
# 3. Non-approval status → no-op (guard returns early)
# ---------------------------------------------------------------------------

def test_w97_non_approval_status_is_noop():
    """Guard should do nothing when target_status is not 'approved'."""
    # No mocks needed — if it calls list_entities it would raise without mocks
    _check_course_linked_to_active_program_for_syllabus_approval(
        tenant_id=TENANT, syllabus_id=SYL_ID, target_status="under_review"
    )
    _check_course_linked_to_active_program_for_syllabus_approval(
        tenant_id=TENANT, syllabus_id=SYL_ID, target_status="draft"
    )
    _check_course_linked_to_active_program_for_syllabus_approval(
        tenant_id=TENANT, syllabus_id=SYL_ID, target_status="published"
    )
    _check_course_linked_to_active_program_for_syllabus_approval(
        tenant_id=TENANT, syllabus_id=SYL_ID, target_status=""
    )


# ---------------------------------------------------------------------------
# 4. Blocked when syllabus has no course_code
# ---------------------------------------------------------------------------

def test_w97_blocked_when_syllabus_has_no_course_code():
    syllabi = [{"id": SYL_ID, "course_code": "", "status": "under_review"}]
    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        return_value=syllabi,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    assert str(SYL_ID) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Blocked when syllabus not found
# ---------------------------------------------------------------------------

def test_w97_blocked_when_syllabus_not_found():
    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    assert str(SYL_ID) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 6. Blocked when no matching course found for course_code
# ---------------------------------------------------------------------------

def test_w97_blocked_when_no_course_matches_course_code():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE, "status": "under_review"}]
    courses: list = []  # no courses at all

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    msg = str(exc_info.value)
    assert COURSE_CODE in msg


# ---------------------------------------------------------------------------
# 7. Blocked when course exists but program is inactive
# ---------------------------------------------------------------------------

def test_w97_blocked_when_program_is_inactive():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [{"id": 10, "course_code": COURSE_CODE, "program_id": "p1", "status": "active"}]
    programs = [{"id": "p1", "status": "inactive"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            return programs
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    assert COURSE_CODE in str(exc_info.value)


# ---------------------------------------------------------------------------
# 8. Blocked when program is archived
# ---------------------------------------------------------------------------

def test_w97_blocked_when_program_is_archived():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [{"id": 10, "course_code": COURSE_CODE, "program_id": "p2", "status": "active"}]
    programs = [{"id": "p2", "status": "archived"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            return programs
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError):
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )


# ---------------------------------------------------------------------------
# 9. Blocked when program is draft (only "active" qualifies)
# ---------------------------------------------------------------------------

def test_w97_blocked_when_program_is_draft():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [{"id": 10, "course_code": COURSE_CODE, "program_id": "p3", "status": "active"}]
    programs = [{"id": "p3", "status": "draft"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            return programs
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError):
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )


# ---------------------------------------------------------------------------
# 10. Fail-closed on courses lookup error
# ---------------------------------------------------------------------------

def test_w97_fail_closed_on_courses_lookup_error():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            raise RuntimeError("DB unavailable")
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    assert COURSE_CODE in str(exc_info.value)


# ---------------------------------------------------------------------------
# 11. Fail-closed on programs lookup error
# ---------------------------------------------------------------------------

def test_w97_fail_closed_on_programs_lookup_error():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [{"id": 10, "course_code": COURSE_CODE, "program_id": "p99"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            raise RuntimeError("programs table offline")
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    assert COURSE_CODE in str(exc_info.value)


# ---------------------------------------------------------------------------
# 12. Passes when course is linked to an active program
# ---------------------------------------------------------------------------

def test_w97_allowed_when_course_linked_to_active_program():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [{"id": 10, "course_code": COURSE_CODE, "program_id": "p_active"}]
    programs = [{"id": "p_active", "status": "active"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            return programs
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        # Must not raise
        _check_course_linked_to_active_program_for_syllabus_approval(
            tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
        )


# ---------------------------------------------------------------------------
# 13. Passes when one of multiple courses is linked to an active program
# ---------------------------------------------------------------------------

def test_w97_allowed_when_one_of_many_courses_has_active_program():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [
        {"id": 10, "course_code": COURSE_CODE, "program_id": "p_inactive"},
        {"id": 11, "course_code": COURSE_CODE, "program_id": "p_active"},
    ]
    programs = [
        {"id": "p_inactive", "status": "inactive"},
        {"id": "p_active", "status": "active"},
    ]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            return programs
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        _check_course_linked_to_active_program_for_syllabus_approval(
            tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
        )


# ---------------------------------------------------------------------------
# 14. Error message contains syllabus_id and course_code
# ---------------------------------------------------------------------------

def test_w97_error_message_contains_syllabus_id_and_course_code():
    syllabi = [{"id": SYL_ID, "course_code": COURSE_CODE}]
    courses = [{"id": 10, "course_code": COURSE_CODE, "program_id": "p_arch"}]
    programs = [{"id": "p_arch", "status": "archived"}]

    def fake_list(entity_type, tenant_id):
        if entity_type == "syllabi":
            return syllabi
        if entity_type == "courses":
            return courses
        if entity_type == "programs":
            return programs
        return []

    with patch(
        "app.modules.syllabus_governance.service.list_entities_for_tenant",
        side_effect=fake_list,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_course_linked_to_active_program_for_syllabus_approval(
                tenant_id=TENANT, syllabus_id=SYL_ID, target_status="approved"
            )
    msg = str(exc_info.value)
    assert str(SYL_ID) in msg
    assert COURSE_CODE in msg
