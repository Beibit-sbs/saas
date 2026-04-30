"""W77 — enrollments: Add/Drop Deadline Enforcement.

Cross-entity invariant: enrollments × academic_terms.add_drop_deadline × utcnow().
drop_enrollment() must be blocked when the term's add_drop_deadline has passed.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.enrollments.models import AcademicTermModel
from app.modules.enrollments.service import EnrollmentLifecycleService


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_term(
    *,
    tenant_id: int = 1,
    term_id: int = 10,
    add_drop_deadline: datetime | None,
) -> MagicMock:
    term = MagicMock(spec=["id", "tenant_id", "add_drop_deadline"])
    term.id = term_id
    term.tenant_id = tenant_id
    term.add_drop_deadline = add_drop_deadline
    return term


def _service() -> EnrollmentLifecycleService:
    db = MagicMock()
    return EnrollmentLifecycleService(db_session=db)


# ---------------------------------------------------------------------------
# 1. AcademicTermModel has add_drop_deadline field
# ---------------------------------------------------------------------------

def test_w77_academic_term_model_has_add_drop_deadline_field():
    """AcademicTermModel must declare add_drop_deadline column."""
    from sqlalchemy import inspect as sa_inspect
    cols = {c.key for c in sa_inspect(AcademicTermModel).mapper.column_attrs}
    assert "add_drop_deadline" in cols, "add_drop_deadline not in AcademicTermModel"


# ---------------------------------------------------------------------------
# 2. Drop blocked when deadline is in the past
# ---------------------------------------------------------------------------

def test_w77_drop_blocked_when_deadline_passed():
    svc = _service()
    past_deadline = datetime.now(UTC) - timedelta(days=1)
    term = _make_term(add_drop_deadline=past_deadline)
    svc.db.execute.return_value.scalar_one_or_none.return_value = term

    with pytest.raises(DomainValidationError) as exc_info:
        svc._check_drop_deadline(tenant_id=1, term_id=10)

    assert "add/drop deadline" in str(exc_info.value).lower()
    assert "has passed" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 3. Drop allowed when deadline is in the future
# ---------------------------------------------------------------------------

def test_w77_drop_allowed_when_deadline_not_yet_reached():
    svc = _service()
    future_deadline = datetime.now(UTC) + timedelta(days=5)
    term = _make_term(add_drop_deadline=future_deadline)
    svc.db.execute.return_value.scalar_one_or_none.return_value = term

    # Must not raise
    svc._check_drop_deadline(tenant_id=1, term_id=10)


# ---------------------------------------------------------------------------
# 4. Drop allowed when no deadline configured on term
# ---------------------------------------------------------------------------

def test_w77_drop_allowed_when_no_deadline_set():
    svc = _service()
    term = _make_term(add_drop_deadline=None)
    svc.db.execute.return_value.scalar_one_or_none.return_value = term

    # Must not raise
    svc._check_drop_deadline(tenant_id=1, term_id=10)


# ---------------------------------------------------------------------------
# 5. Drop allowed when term record not found (no false positives)
# ---------------------------------------------------------------------------

def test_w77_drop_allowed_when_term_not_found():
    svc = _service()
    svc.db.execute.return_value.scalar_one_or_none.return_value = None

    # No term record → no deadline → must not raise
    svc._check_drop_deadline(tenant_id=1, term_id=99)


# ---------------------------------------------------------------------------
# 6. Error message contains the deadline date string
# ---------------------------------------------------------------------------

def test_w77_error_message_contains_deadline_date():
    svc = _service()
    deadline = datetime(2026, 1, 15, 23, 59, 0, tzinfo=UTC)
    term = _make_term(add_drop_deadline=deadline)
    svc.db.execute.return_value.scalar_one_or_none.return_value = term

    with pytest.raises(DomainValidationError) as exc_info:
        svc._check_drop_deadline(tenant_id=1, term_id=10)

    assert "2026-01-15" in str(exc_info.value), (
        f"Error message should contain deadline date; got: {exc_info.value}"
    )
