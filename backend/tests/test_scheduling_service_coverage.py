"""
Coverage boost: app.modules.scheduling.service

Tests call SchedulingService methods directly with MagicMock DB sessions.
Billing and audit side-effects are patched out.
"""
from __future__ import annotations

import asyncio
from datetime import time
from unittest.mock import MagicMock, patch

import pytest

from app.modules.scheduling.models import (
    DayOfWeek,
    SectionStatus,
)
from app.modules.scheduling.schemas import (
    CourseSectionCreateSchema,
    SectionScheduleCreateSchema,
    DisciplineCreateSchema,
)
from app.modules.scheduling.service import SchedulingService, _time_to_str


def _run(coro):
    return asyncio.run(coro)


def _make_service(db=None):
    if db is None:
        db = MagicMock()
    return SchedulingService(db_session=db)


def _make_section(**kwargs):
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.tenant_id = kwargs.get("tenant_id", 1)
    s.status = kwargs.get("status", SectionStatus.PLANNED)
    s.max_capacity = kwargs.get("max_capacity", 30)
    s.instructor_id = kwargs.get("instructor_id", "instr@e.com")
    s.version = kwargs.get("version", 1)
    return s


def _make_classroom(**kwargs):
    c = MagicMock()
    c.id = kwargs.get("id", 1)
    c.tenant_id = kwargs.get("tenant_id", 1)
    c.capacity = kwargs.get("capacity", 50)
    c.is_active = True
    return c


def _make_slot(**kwargs):
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.tenant_id = kwargs.get("tenant_id", 1)
    s.start_time = kwargs.get("start_time", time(9, 0))
    s.end_time = kwargs.get("end_time", time(10, 0))
    s.is_active = True
    return s


# ---------------------------------------------------------------------------
# Pure helper
# ---------------------------------------------------------------------------


def test_time_to_str():
    assert _time_to_str(time(9, 30)) == "09:30:00"


def test_time_to_str_none():
    assert _time_to_str(None) == "00:00:00"


# ---------------------------------------------------------------------------
# _load_lesson_topic
# ---------------------------------------------------------------------------


def test_load_lesson_topic_found():
    db = MagicMock()
    topic = MagicMock()
    topic.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.return_value = topic
    svc = _make_service(db)
    result = svc._load_lesson_topic(tenant_id=1, topic_id=5)
    assert result is topic


def test_load_lesson_topic_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        svc._load_lesson_topic(tenant_id=1, topic_id=999)


# ---------------------------------------------------------------------------
# _load_time_slot
# ---------------------------------------------------------------------------


def test_load_time_slot_found():
    db = MagicMock()
    slot = _make_slot()
    db.execute.return_value.scalar_one_or_none.return_value = slot

    svc = _make_service(db)
    with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_time_slot_exists"):
        with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_time_range"):
            result = svc._load_time_slot(tenant_id=1, time_slot_id=1)
    assert result is slot


def test_load_time_slot_not_found():
    from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises((DomainValidationError, TenantResourceNotFoundError)):
        svc._load_time_slot(tenant_id=1, time_slot_id=999)


# ---------------------------------------------------------------------------
# _load_classroom
# ---------------------------------------------------------------------------


def test_load_classroom_found():
    db = MagicMock()
    classroom = _make_classroom()
    db.execute.return_value.scalar_one_or_none.return_value = classroom

    svc = _make_service(db)
    with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_classroom_exists"):
        result = svc._load_classroom(tenant_id=1, classroom_id=1)
    assert result is classroom


# ---------------------------------------------------------------------------
# _load_course_placeholder
# ---------------------------------------------------------------------------


def test_load_course_placeholder_found_same_tenant():
    db = MagicMock()
    course = MagicMock()
    course.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.return_value = course

    svc = _make_service(db)
    result = svc._load_course_placeholder(tenant_id=1, course_id=5)
    assert result is course


def test_load_course_placeholder_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        svc._load_course_placeholder(tenant_id=1, course_id=999)


def test_load_course_placeholder_wrong_tenant():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    course = MagicMock()
    course.tenant_id = 2  # different tenant
    db.execute.return_value.scalar_one_or_none.return_value = course

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        svc._load_course_placeholder(tenant_id=1, course_id=5)


def test_load_course_placeholder_no_tenant_id_attribute():
    db = MagicMock()
    course = object()  # no tenant_id attribute
    db.execute.return_value.scalar_one_or_none.return_value = course

    svc = _make_service(db)
    # Should not raise — course with no tenant_id passes
    result = svc._load_course_placeholder(tenant_id=1, course_id=5)
    assert result is course


# ---------------------------------------------------------------------------
# _validate_term_exists
# ---------------------------------------------------------------------------


def test_validate_term_exists_found():
    db = MagicMock()
    term = MagicMock()
    term.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.return_value = term
    svc = _make_service(db)
    svc._validate_term_exists(tenant_id=1, term_id=10)  # should not raise


def test_validate_term_exists_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        svc._validate_term_exists(tenant_id=1, term_id=999)


# ---------------------------------------------------------------------------
# _get_room_conflict
# ---------------------------------------------------------------------------


def test_get_room_conflict_returns_none():
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    result = svc._get_room_conflict(
        tenant_id=1,
        classroom_id=1,
        time_slot_id=1,
        day_of_week=DayOfWeek.MONDAY,
    )
    assert result is None


def test_get_room_conflict_returns_conflict():
    db = MagicMock()
    conflict = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = conflict

    svc = _make_service(db)
    result = svc._get_room_conflict(
        tenant_id=1,
        classroom_id=1,
        time_slot_id=1,
        day_of_week=DayOfWeek.MONDAY,
        exclude_section_id=5,
    )
    assert result is conflict


# ---------------------------------------------------------------------------
# _find_instructor_conflicts
# ---------------------------------------------------------------------------


def test_find_instructor_conflicts_empty():
    db = MagicMock()
    db.execute.return_value.all.return_value = []

    svc = _make_service(db)
    result = svc._find_instructor_conflicts(
        tenant_id=1,
        instructor_id="instr@e.com",
        day_of_week=DayOfWeek.MONDAY,
        start_time=time(9, 0),
        end_time=time(10, 0),
        exclude_section_id=None,
    )
    assert result == []


def test_find_instructor_conflicts_with_conflicts():
    db = MagicMock()
    row = (1, DayOfWeek.MONDAY, time(9, 0), time(10, 0))
    db.execute.return_value.all.return_value = [row]

    svc = _make_service(db)
    result = svc._find_instructor_conflicts(
        tenant_id=1,
        instructor_id="instr@e.com",
        day_of_week=DayOfWeek.MONDAY,
        start_time=time(9, 0),
        end_time=time(10, 0),
        exclude_section_id=2,
    )
    assert len(result) == 1
    assert result[0]["section_id"] == 1


# ---------------------------------------------------------------------------
# create_course_section
# ---------------------------------------------------------------------------


def _patch_billing_and_audit():
    """Context manager that suppresses billing/audit side effects."""
    bill = patch("app.modules.scheduling.service.assert_billing_write_allowed")
    audit = patch("app.modules.scheduling.service._audit")
    return bill, audit


@pytest.mark.parametrize("instructor_id", [None, "instr@e.com"])
def test_create_course_section_happy(instructor_id):
    db = MagicMock()
    # course + term found
    course = MagicMock()
    course.tenant_id = 1
    term = MagicMock()
    term.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.side_effect = [course, term]
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = CourseSectionCreateSchema(
        course_id=10,
        term_id=20,
        section_code="SEC-01",
        instructor_id=instructor_id,
        max_capacity=30,
    )
    bill, audit = _patch_billing_and_audit()
    with bill, audit:
        with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_section_capacity"):
            with patch("app.modules.scheduling.schemas.CourseSectionReadSchema.model_validate", return_value=MagicMock()):
                _run(svc.create_course_section(tenant_id=1, request=req, actor_id="admin@e.com"))
    assert db.add.called
    assert db.commit.called


def test_create_course_section_integrity_error():
    from app.core.module_helpers.service_validation import DomainValidationError
    from sqlalchemy.exc import IntegrityError

    db = MagicMock()
    course = MagicMock()
    course.tenant_id = 1
    term = MagicMock()
    term.tenant_id = 1
    db.execute.return_value.scalar_one_or_none.side_effect = [course, term]
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit.side_effect = IntegrityError("dup", params={}, orig=Exception())
    db.rollback = MagicMock()

    svc = _make_service(db)
    req = CourseSectionCreateSchema(
        course_id=10, term_id=20, section_code="SEC-DUP", max_capacity=25
    )
    bill, audit = _patch_billing_and_audit()
    with bill, audit:
        with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_section_capacity"):
            with pytest.raises(DomainValidationError):
                _run(svc.create_course_section(tenant_id=1, request=req, actor_id="admin@e.com"))
    assert db.rollback.called


# ---------------------------------------------------------------------------
# schedule_section
# ---------------------------------------------------------------------------


def test_schedule_section_cancelled_section_raises():
    from app.core.module_helpers.service_validation import DomainValidationError

    db = MagicMock()
    section = _make_section(status=SectionStatus.CANCELLED)
    db.execute.return_value.scalar_one_or_none.return_value = section

    svc = _make_service(db)
    req = SectionScheduleCreateSchema(
        time_slot_id=1, classroom_id=1, day_of_week=DayOfWeek.MONDAY
    )
    with pytest.raises(DomainValidationError, match="cancelled"):
        _run(svc.schedule_section(tenant_id=1, section_id=1, request=req, actor_id="a@e.com"))


def test_schedule_section_already_has_schedule_raises():
    from app.core.module_helpers.service_validation import DomainValidationError

    db = MagicMock()
    section = _make_section(status=SectionStatus.PLANNED)
    slot = _make_slot()
    classroom = _make_classroom(capacity=50)
    existing_schedule = MagicMock()

    # calls: load_course_section → slot → classroom → instructor_ids → existing_schedule
    db.execute.return_value.scalar_one_or_none.side_effect = [
        section,       # _load_course_section
        slot,          # _load_time_slot  
        classroom,     # _load_classroom
        None,          # _get_room_conflict (no conflict)
        existing_schedule,  # _load_section_schedule
    ]
    # instructor lookup returns empty
    db.execute.return_value.all.return_value = []

    svc = _make_service(db)
    req = SectionScheduleCreateSchema(
        time_slot_id=1, classroom_id=1, day_of_week=DayOfWeek.TUESDAY
    )
    bill, audit = _patch_billing_and_audit()
    with bill, audit:
        with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_time_slot_exists"):
            with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_time_range"):
                with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_classroom_exists"):
                    with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_room_capacity"):
                        with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_no_room_conflict"):
                            with patch("app.modules.scheduling.business_rules.SchedulingRules.validate_no_instructor_conflict"):
                                with pytest.raises(DomainValidationError, match="already has a schedule"):
                                    _run(svc.schedule_section(tenant_id=1, section_id=1, request=req, actor_id="a@e.com"))


# ---------------------------------------------------------------------------
# create_discipline
# ---------------------------------------------------------------------------


def test_create_discipline():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None  # no duplicate

    svc = _make_service(db)
    req = DisciplineCreateSchema(
        unique_code="MATH-101",
        title="Mathematics",
        credits=3,
    )
    with patch("app.modules.scheduling.service.assert_billing_write_allowed"):
        with patch("app.modules.scheduling.schemas.DisciplineReadSchema.model_validate", return_value=MagicMock()):
            _run(svc.create_discipline(tenant_id=1, request=req, actor_id="admin@e.com"))
    assert db.add.called


# ---------------------------------------------------------------------------
# DATA INTEGRITY: scheduling conflict guards (unit tests for business rules)
# ---------------------------------------------------------------------------

def test_validate_no_room_conflict_raises_when_conflict_exists() -> None:
    """validate_no_room_conflict raises DomainValidationError when a room conflict exists."""
    from app.modules.scheduling.business_rules import SchedulingRules
    from app.core.module_helpers.service_validation import DomainValidationError

    existing_section = MagicMock()  # truthy → conflict found
    with pytest.raises(DomainValidationError, match="room conflict detected for classroom_id=5"):
        SchedulingRules.validate_no_room_conflict(
            existing_section, classroom_id=5, day_of_week="MONDAY"
        )


def test_validate_no_room_conflict_passes_when_none() -> None:
    """validate_no_room_conflict does NOT raise when there is no room conflict."""
    from app.modules.scheduling.business_rules import SchedulingRules

    # Should not raise
    SchedulingRules.validate_no_room_conflict(None, classroom_id=5, day_of_week="MONDAY")


def test_validate_no_instructor_conflict_raises_when_conflicts_exist() -> None:
    """validate_no_instructor_conflict raises DomainValidationError when instructor conflicts exist."""
    from app.modules.scheduling.business_rules import SchedulingRules
    from app.core.module_helpers.service_validation import DomainValidationError

    conflicts = [MagicMock()]  # non-empty list → conflict
    with pytest.raises(DomainValidationError, match="instructor conflict detected for instructor_id=INS01"):
        SchedulingRules.validate_no_instructor_conflict(
            conflicts, instructor_id="INS01", day_of_week="TUESDAY"
        )


def test_validate_no_instructor_conflict_passes_when_empty() -> None:
    """validate_no_instructor_conflict does NOT raise when there are no instructor conflicts."""
    from app.modules.scheduling.business_rules import SchedulingRules

    # Should not raise
    SchedulingRules.validate_no_instructor_conflict([], instructor_id="INS01", day_of_week="TUESDAY")

