"""
Tests for enrollments.dropout_risk → interventions cross-module flow.
W: enrollments service creates InterventionCaseModel directly when enrollment
   transitions to a dropout-risk status (WITHDRAWN / SUSPENDED / DROPPED).
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Minimal stub factories
# ---------------------------------------------------------------------------

def _make_enrollment(*, student_profile_id: int = 42, course_id: int = 7, id: int = 1, version: int = 1, tenant_id: int = 999):
    e = MagicMock()
    e.id = id
    e.student_profile_id = student_profile_id
    e.course_id = course_id
    e.version = version
    e.tenant_id = tenant_id
    return e


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dropout_risk_creates_intervention_on_withdrawn():
    """Transitioning an enrollment to WITHDRAWN must create an intervention."""
    from app.modules.enrollments.service import EnrollmentLifecycleService
    from app.modules.enrollments.models import EnrollmentStatus
    from app.modules.enrollments.schemas import EnrollmentStatusChangeSchema
    from app.modules.interventions.models import (
        InterventionCaseModel,
        InterventionCaseSeverity,
        InterventionCaseStatus,
    )

    added: list = []

    db = MagicMock()
    # _load_enrollment uses db.execute(...).scalar_one_or_none()
    enrollment = _make_enrollment()
    enrollment.enrollment_status = EnrollmentStatus.ENROLLED
    db.execute.return_value.scalar_one_or_none.return_value = enrollment

    def fake_add(obj):
        added.append(obj)

    db.add = fake_add
    db.commit = MagicMock()
    db.rollback = MagicMock()

    svc = EnrollmentLifecycleService(db)

    request = EnrollmentStatusChangeSchema(
        expected_version=1,
        to_status=EnrollmentStatus.WITHDRAWN,
        reason="Student requested withdrawal",
    )

    # Patch brain signal helper so it doesn't fail (brain_core_service imported locally)
    with patch("app.modules.enrollments.service._emit_dropout_risk_signal"):
        with patch("app.modules.brain_core.service.brain_core_service") as _bcs:
            with patch("app.modules.enrollments.service.EnrollmentReadSchema") as _schema:
                _schema.model_validate.return_value = MagicMock()
                asyncio.run(svc.change_enrollment_status(
                    tenant_id=999,
                    enrollment_id=1,
                    request=request,
                    actor_id="test_actor",
                ))

    intervention_cases = [o for o in added if isinstance(o, InterventionCaseModel)]
    assert len(intervention_cases) == 1, "Expected 1 InterventionCaseModel to be created"
    case = intervention_cases[0]
    assert case.tenant_id == 999
    assert case.student_profile_id == 42
    assert case.severity == InterventionCaseSeverity.HIGH
    assert case.status == InterventionCaseStatus.OPEN
    assert "dropout" in case.title.lower() or "risk" in case.title.lower()


def test_dropout_risk_creates_intervention_on_suspended():
    """Transitioning to SUSPENDED must also create intervention."""
    from app.modules.enrollments.service import EnrollmentLifecycleService
    from app.modules.enrollments.models import EnrollmentStatus
    from app.modules.enrollments.schemas import EnrollmentStatusChangeSchema
    from app.modules.interventions.models import InterventionCaseModel

    added: list = []
    db = MagicMock()
    enrollment = _make_enrollment(student_profile_id=55)
    enrollment.enrollment_status = EnrollmentStatus.ENROLLED
    db.execute.return_value.scalar_one_or_none.return_value = enrollment
    db.add = lambda obj: added.append(obj)
    db.commit = MagicMock()
    db.rollback = MagicMock()

    svc = EnrollmentLifecycleService(db)
    request = EnrollmentStatusChangeSchema(
        expected_version=1,
        to_status=EnrollmentStatus.SUSPENDED,
        reason="Academic probation",
    )

    with patch("app.modules.enrollments.service._emit_dropout_risk_signal"):
        with patch("app.modules.brain_core.service.brain_core_service"):
            with patch("app.modules.enrollments.service.EnrollmentReadSchema") as _schema:
                _schema.model_validate.return_value = MagicMock()
                asyncio.run(svc.change_enrollment_status(
                    tenant_id=999,
                    enrollment_id=1,
                    request=request,
                    actor_id="test_actor",
                ))

    cases = [o for o in added if isinstance(o, InterventionCaseModel)]
    assert len(cases) == 1
    assert cases[0].student_profile_id == 55


def test_no_intervention_on_non_dropout_status_change():
    """Transitioning to COMPLETED must NOT create an intervention."""
    from app.modules.enrollments.service import EnrollmentLifecycleService
    from app.modules.enrollments.models import EnrollmentStatus
    from app.modules.enrollments.schemas import EnrollmentStatusChangeSchema
    from app.modules.interventions.models import InterventionCaseModel

    added: list = []
    db = MagicMock()
    enrollment = _make_enrollment()
    enrollment.enrollment_status = EnrollmentStatus.ENROLLED
    db.execute.return_value.scalar_one_or_none.return_value = enrollment
    db.add = lambda obj: added.append(obj)
    db.commit = MagicMock()
    db.rollback = MagicMock()

    svc = EnrollmentLifecycleService(db)
    request = EnrollmentStatusChangeSchema(
        expected_version=1,
        to_status=EnrollmentStatus.COMPLETED,
        reason="Course finished",
    )

    with patch("app.modules.enrollments.service.EnrollmentReadSchema") as _schema:
        _schema.model_validate.return_value = MagicMock()
        asyncio.run(svc.change_enrollment_status(
            tenant_id=999,
            enrollment_id=1,
            request=request,
            actor_id="test_actor",
        ))

    cases = [o for o in added if isinstance(o, InterventionCaseModel)]
    assert cases == [], "No intervention should be created for COMPLETED status"
