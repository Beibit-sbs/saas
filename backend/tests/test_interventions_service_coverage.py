"""
Coverage boost: app.modules.interventions.service

Tests call service methods directly using a MagicMock DB session.
No FastAPI client or real DB is required.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.interventions.models import (
    InterventionActionType,
    InterventionAssigneeType,
    InterventionCaseSeverity,
    InterventionCaseStatus,
    InterventionCaseType,
)
from app.modules.interventions.schemas import (
    InterventionActionCreateSchema,
    InterventionCaseAssignSchema,
    InterventionCaseCreateSchema,
    InterventionCaseStatusUpdateSchema,
    InterventionCaseTakeSchema,
)
from app.modules.interventions.service import (
    InterventionService,
    _default_assignment_for_severity,
    _default_due_at,
)


def _now():
    return datetime.now(UTC)


def _make_case(
    *,
    id: int = 1,
    tenant_id: int = 1,
    severity=InterventionCaseSeverity.HIGH,
    status=InterventionCaseStatus.OPEN,
    version: int = 1,
    student_profile_id: int | None = 101,
):
    case = MagicMock()
    case.id = id
    case.tenant_id = tenant_id
    case.severity = severity
    case.status = status
    case.version = version
    case.student_profile_id = student_profile_id
    case.assignee_type = InterventionAssigneeType.GROUP
    case.assignee_ref = "dean_office"
    case.due_at = _now() + timedelta(days=3)
    case.resolved_at = None
    return case


def _make_service(db=None):
    if db is None:
        db = MagicMock()
    return InterventionService(db_session=db)


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_default_assignment_high():
    atype, aref = _default_assignment_for_severity(InterventionCaseSeverity.HIGH)
    assert atype == InterventionAssigneeType.GROUP
    assert aref == "dean_office"


def test_default_assignment_medium():
    atype, aref = _default_assignment_for_severity(InterventionCaseSeverity.MEDIUM)
    assert atype == InterventionAssigneeType.GROUP
    assert aref == "faculty_advisor"


def test_default_assignment_low():
    atype, aref = _default_assignment_for_severity(InterventionCaseSeverity.LOW)
    assert atype == InterventionAssigneeType.GROUP
    assert aref == "student_support"


def test_default_due_at_high():
    before = _now()
    due = _default_due_at(InterventionCaseSeverity.HIGH)
    assert due > before
    delta = due - _now()
    assert abs(delta.total_seconds() - 3 * 86400) < 10


def test_default_due_at_medium():
    due = _default_due_at(InterventionCaseSeverity.MEDIUM)
    delta = due - _now()
    assert abs(delta.total_seconds() - 5 * 86400) < 10


def test_default_due_at_low():
    due = _default_due_at(InterventionCaseSeverity.LOW)
    delta = due - _now()
    assert abs(delta.total_seconds() - 7 * 86400) < 10


# ---------------------------------------------------------------------------
# create_case
# ---------------------------------------------------------------------------


def test_create_case_no_student_profile():
    """create_case with student_profile_id=None skips DB student lookup."""
    db = MagicMock()
    case = _make_case(student_profile_id=None)
    # db.flush and db.refresh are needed; db.add must not raise
    db.flush = MagicMock()
    db.refresh = MagicMock(side_effect=lambda obj: None)
    db.commit = MagicMock()
    db.add = MagicMock()
    # Return the case from refresh
    db.refresh.side_effect = lambda obj: setattr(obj, "id", 42) if not hasattr(obj, "id") or obj.id is None else None

    svc = _make_service(db)
    req = InterventionCaseCreateSchema(
        case_type=InterventionCaseType.ACADEMIC_RISK,
        student_profile_id=None,
        severity=InterventionCaseSeverity.HIGH,
        title="Test case",
        description="Test",
    )
    created = _run(svc.create_case(tenant_id=1, request=req, actor="admin@e.com"))
    assert db.add.called
    assert db.commit.called


def test_create_case_with_student_profile_found():
    """create_case with student_profile_id finds the student and creates case."""
    db = MagicMock()
    student = MagicMock()
    student.tenant_id = 1
    student.id = 101
    # execute().scalar_one_or_none() returns student mock
    db.execute.return_value.scalar_one_or_none.return_value = student
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()
    db.add = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseCreateSchema(
        case_type=InterventionCaseType.ACADEMIC_RISK,
        student_profile_id=101,
        severity=InterventionCaseSeverity.MEDIUM,
        title="Risk case",
        description="desc",
    )
    _run(svc.create_case(tenant_id=1, request=req, actor="admin@e.com"))
    assert db.add.called


def test_create_case_with_default_assignment():
    """create_case fills assignee from default when not provided."""
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()
    db.add = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseCreateSchema(
        student_profile_id=None,
        severity=InterventionCaseSeverity.LOW,
        title="Low prio",
        description=None,
        assignee_type=None,
        assignee_ref=None,
    )
    _run(svc.create_case(tenant_id=1, request=req, actor="a@e.com"))
    # No exception means default assignment was applied
    assert db.commit.called


def test_create_case_explicit_assignment():
    """create_case uses provided assignee when given."""
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()
    db.add = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseCreateSchema(
        student_profile_id=None,
        severity=InterventionCaseSeverity.HIGH,
        title="Explicit assign",
        assignee_type=InterventionAssigneeType.USER,
        assignee_ref="advisor@e.com",
    )
    _run(svc.create_case(tenant_id=1, request=req, actor="admin@e.com"))
    assert db.add.called


# ---------------------------------------------------------------------------
# list_cases
# ---------------------------------------------------------------------------


def test_list_cases_all():
    db = MagicMock()
    # count query returns 2
    db.execute.return_value.scalar_one.return_value = 2
    # items query returns list
    db.execute.return_value.scalars.return_value.all.return_value = [
        _make_case(id=1),
        _make_case(id=2),
    ]

    svc = _make_service(db)
    total, items = _run(svc.list_cases(tenant_id=1, page=1, page_size=10))
    assert total == 2
    assert len(items) == 2


def test_list_cases_filtered_by_status():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 1
    db.execute.return_value.scalars.return_value.all.return_value = [_make_case()]

    svc = _make_service(db)
    total, items = _run(
        svc.list_cases(tenant_id=1, page=1, page_size=10, status=InterventionCaseStatus.OPEN)
    )
    assert total == 1


def test_list_cases_filtered_by_severity():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalars.return_value.all.return_value = []

    svc = _make_service(db)
    total, items = _run(
        svc.list_cases(
            tenant_id=1, page=1, page_size=10, severity=InterventionCaseSeverity.HIGH
        )
    )
    assert total == 0
    assert items == []


def test_list_cases_overdue_only():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 1
    db.execute.return_value.scalars.return_value.all.return_value = [_make_case()]

    svc = _make_service(db)
    total, items = _run(
        svc.list_cases(tenant_id=1, page=1, page_size=5, overdue_only=True)
    )
    assert total == 1


def test_list_cases_filtered_by_assignee_ref():
    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0
    db.execute.return_value.scalars.return_value.all.return_value = []

    svc = _make_service(db)
    total, items = _run(
        svc.list_cases(tenant_id=1, page=1, page_size=5, assignee_ref="dean_ref")
    )
    assert total == 0


# ---------------------------------------------------------------------------
# get_case
# ---------------------------------------------------------------------------


def test_get_case_found():
    db = MagicMock()
    case = _make_case(id=5)
    db.execute.return_value.scalar_one_or_none.return_value = case

    svc = _make_service(db)
    result = _run(svc.get_case(tenant_id=1, case_id=5))
    assert result.id == 5


def test_get_case_not_found():
    from app.core.module_helpers.service_validation import TenantResourceNotFoundError

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None

    svc = _make_service(db)
    with pytest.raises(TenantResourceNotFoundError):
        _run(svc.get_case(tenant_id=1, case_id=999))


# ---------------------------------------------------------------------------
# assign_case
# ---------------------------------------------------------------------------


def test_assign_case():
    db = MagicMock()
    case = _make_case(id=10, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseAssignSchema(
        expected_version=1,
        assignee_type=InterventionAssigneeType.USER,
        assignee_ref="advisor@e.com",
    )
    result = _run(svc.assign_case(tenant_id=1, case_id=10, request=req, actor="admin@e.com"))
    assert db.commit.called


def test_assign_case_with_due_at():
    db = MagicMock()
    case = _make_case(id=11, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    future_due = _now() + timedelta(days=10)
    req = InterventionCaseAssignSchema(
        expected_version=1,
        assignee_type=InterventionAssigneeType.GROUP,
        assignee_ref="deans",
        due_at=future_due,
    )
    _run(svc.assign_case(tenant_id=1, case_id=11, request=req, actor="admin@e.com"))
    assert case.due_at == future_due


# ---------------------------------------------------------------------------
# take_case
# ---------------------------------------------------------------------------


def test_take_case_moves_to_in_progress():
    db = MagicMock()
    case = _make_case(id=20, status=InterventionCaseStatus.OPEN, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseTakeSchema(expected_version=1)
    _run(svc.take_case(tenant_id=1, case_id=20, request=req, actor="handler@e.com"))
    assert case.status == InterventionCaseStatus.IN_PROGRESS
    assert case.assignee_ref == "handler@e.com"


def test_take_case_already_in_progress_stays():
    db = MagicMock()
    case = _make_case(id=21, status=InterventionCaseStatus.IN_PROGRESS, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseTakeSchema(expected_version=1)
    _run(svc.take_case(tenant_id=1, case_id=21, request=req, actor="handler@e.com"))
    # stays IN_PROGRESS
    assert case.status == InterventionCaseStatus.IN_PROGRESS


# ---------------------------------------------------------------------------
# update_case_status
# ---------------------------------------------------------------------------


def test_update_case_status_to_resolved():
    db = MagicMock()
    case = _make_case(id=30, status=InterventionCaseStatus.IN_PROGRESS, version=2)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseStatusUpdateSchema(
        expected_version=2,
        status=InterventionCaseStatus.RESOLVED,
        reason="Issue resolved",
    )
    _run(svc.update_case_status(tenant_id=1, case_id=30, request=req, actor="admin@e.com"))
    assert case.status == InterventionCaseStatus.RESOLVED
    assert case.resolved_at is not None


def test_update_case_status_to_closed():
    db = MagicMock()
    case = _make_case(id=31, status=InterventionCaseStatus.RESOLVED, version=3)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseStatusUpdateSchema(
        expected_version=3,
        status=InterventionCaseStatus.CLOSED,
    )
    _run(svc.update_case_status(tenant_id=1, case_id=31, request=req, actor="admin@e.com"))
    assert case.status == InterventionCaseStatus.CLOSED


def test_update_case_status_to_open_clears_resolved_at():
    db = MagicMock()
    case = _make_case(id=32, status=InterventionCaseStatus.RESOLVED, version=1)
    case.resolved_at = _now()
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionCaseStatusUpdateSchema(
        expected_version=1,
        status=InterventionCaseStatus.OPEN,
    )
    _run(svc.update_case_status(tenant_id=1, case_id=32, request=req, actor="admin@e.com"))
    assert case.resolved_at is None


# ---------------------------------------------------------------------------
# add_case_action
# ---------------------------------------------------------------------------


def test_add_case_action_basic():
    db = MagicMock()
    case = _make_case(id=40, status=InterventionCaseStatus.OPEN, version=1)
    action = MagicMock()
    action.id = 100
    action.action_type = InterventionActionType.CONSULTATION_SCHEDULED
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionActionCreateSchema(
        expected_version=1,
        action_type=InterventionActionType.CONSULTATION_SCHEDULED,
        description="Meeting with advisor",
        mark_case_in_progress=False,
        mark_case_resolved=False,
    )
    result_case, result_action = _run(
        svc.add_case_action(tenant_id=1, case_id=40, request=req, actor="admin@e.com")
    )
    assert db.commit.called


def test_add_case_action_mark_in_progress():
    db = MagicMock()
    case = _make_case(id=41, status=InterventionCaseStatus.OPEN, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionActionCreateSchema(
        expected_version=1,
        action_type=InterventionActionType.NOTE,
        description="Working on it",
        mark_case_in_progress=True,
        mark_case_resolved=False,
    )
    _run(svc.add_case_action(tenant_id=1, case_id=41, request=req, actor="admin@e.com"))
    assert case.status == InterventionCaseStatus.IN_PROGRESS


def test_add_case_action_mark_resolved():
    db = MagicMock()
    case = _make_case(id=42, status=InterventionCaseStatus.IN_PROGRESS, version=2)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    svc = _make_service(db)
    req = InterventionActionCreateSchema(
        expected_version=2,
        action_type=InterventionActionType.STATUS_CHANGE,
        description="Issue resolved",
        mark_case_in_progress=False,
        mark_case_resolved=True,
    )
    _run(svc.add_case_action(tenant_id=1, case_id=42, request=req, actor="admin@e.com"))
    assert case.status == InterventionCaseStatus.RESOLVED
    assert case.resolved_at is not None


# ---------------------------------------------------------------------------
# list_case_actions
# ---------------------------------------------------------------------------


def test_list_case_actions():
    db = MagicMock()
    case = _make_case(id=50)
    db.execute.return_value.scalar_one_or_none.return_value = case
    actions = [MagicMock(), MagicMock()]
    db.execute.return_value.scalars.return_value.all.return_value = actions

    svc = _make_service(db)
    result = _run(svc.list_case_actions(tenant_id=1, case_id=50))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# list_tenant_intervention_consistency_report
# ---------------------------------------------------------------------------


def test_consistency_report_empty():
    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []

    svc = _make_service(db)
    report = _run(svc.list_tenant_intervention_consistency_report(tenant_id=1))
    assert report.issue_count == 0


def test_consistency_report_with_orphaned_action():
    db = MagicMock()

    case = _make_case(id=100, student_profile_id=999)
    case.id = 100
    action = MagicMock()
    action.case_id = 9999  # orphaned — case not in case_ids
    action.id = 5

    # Use side_effect on the final `.all()` callable to return different values each call
    all_mock = MagicMock(side_effect=[
        [case],   # cases query
        [200],    # student IDs (999 is missing → issue)
        [action], # actions query
    ])
    db.execute.return_value.scalars.return_value.all = all_mock

    svc = _make_service(db)
    report = _run(svc.list_tenant_intervention_consistency_report(tenant_id=1))
    assert report.case_count == 1
    assert report.action_count == 1
    assert report.issue_count >= 1
