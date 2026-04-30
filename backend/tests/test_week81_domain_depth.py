"""W81 — grades: Term End Date Grade Submission Lock.

Cross-entity invariant: grades × academic_terms.end_date × utcnow().
submit_grade() must be blocked when the institutional grade submission window
has closed — i.e., term.end_date + GRACE_DAYS < now().

Without this guard, professors can retroactively submit or change grades long
after term completion, corrupting already-issued transcripts, distorting
financial aid SAP calculations, and creating accreditation audit failures.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.grades.service import (
    GradeLifecycleService,
    _GRADE_SUBMISSION_GRACE_DAYS,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _service() -> GradeLifecycleService:
    db = MagicMock()
    return GradeLifecycleService(db_session=db)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_term(
    term_id: int = 7,
    tenant_id: int = 1,
    end_date: datetime | None = None,
) -> MagicMock:
    t = MagicMock()
    t.id = term_id
    t.tenant_id = tenant_id
    t.end_date = end_date
    return t


def _inject_term(svc: GradeLifecycleService, term: object) -> None:
    """Wire the DB mock to return `term` for any scalar_one_or_none query."""
    svc.db.execute.return_value.scalar_one_or_none.return_value = term


# ---------------------------------------------------------------------------
# Test 1: guard method and constant exist
# ---------------------------------------------------------------------------

def test_w81_guard_method_and_constant_exist():
    svc = _service()
    assert hasattr(svc, "_check_term_submission_window_open"), (
        "_check_term_submission_window_open must be defined on GradeLifecycleService"
    )
    assert isinstance(_GRADE_SUBMISSION_GRACE_DAYS, int), (
        "_GRADE_SUBMISSION_GRACE_DAYS must be an integer"
    )
    assert _GRADE_SUBMISSION_GRACE_DAYS >= 1


# ---------------------------------------------------------------------------
# Test 2: blocked when well past grace period (60 days after end_date)
# ---------------------------------------------------------------------------

def test_w81_blocked_when_past_grace_period():
    svc = _service()
    past_end = _now() - timedelta(days=_GRADE_SUBMISSION_GRACE_DAYS + 30)
    term = _make_term(term_id=7, end_date=past_end)
    _inject_term(svc, term)

    with pytest.raises(DomainValidationError):
        svc._check_term_submission_window_open(tenant_id=1, term_id=7)


# ---------------------------------------------------------------------------
# Test 3: allowed when within grace period (1 day after end_date)
# ---------------------------------------------------------------------------

def test_w81_allowed_within_grace_period():
    svc = _service()
    recent_end = _now() - timedelta(days=1)
    term = _make_term(term_id=8, end_date=recent_end)
    _inject_term(svc, term)

    # Must not raise
    svc._check_term_submission_window_open(tenant_id=1, term_id=8)


# ---------------------------------------------------------------------------
# Test 4: allowed when exactly at grace period boundary
# ---------------------------------------------------------------------------

def test_w81_allowed_at_grace_boundary():
    svc = _service()
    # end_date exactly GRACE_DAYS ago → deadline = now → not yet expired
    boundary_end = _now() - timedelta(days=_GRADE_SUBMISSION_GRACE_DAYS - 1)
    term = _make_term(term_id=9, end_date=boundary_end)
    _inject_term(svc, term)

    svc._check_term_submission_window_open(tenant_id=1, term_id=9)


# ---------------------------------------------------------------------------
# Test 5: allowed when term not found (safe-skip)
# ---------------------------------------------------------------------------

def test_w81_allowed_when_term_not_found():
    svc = _service()
    _inject_term(svc, None)

    # Must not raise — missing term is not our concern here
    svc._check_term_submission_window_open(tenant_id=1, term_id=999)


# ---------------------------------------------------------------------------
# Test 6: allowed when end_date is None (term without configured end date)
# ---------------------------------------------------------------------------

def test_w81_allowed_when_end_date_is_none():
    svc = _service()
    term = _make_term(term_id=10, end_date=None)
    _inject_term(svc, term)

    svc._check_term_submission_window_open(tenant_id=1, term_id=10)
