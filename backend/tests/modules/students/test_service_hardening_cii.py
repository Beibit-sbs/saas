"""Phase CII - Students Service Hardening (canonical fail-safe hooks).

Verifies:
1. create_student_profile records outcome + metric after successful persistence.
2. change_student_status records outcome + metric after successful status mutation.
3. create_student_profile survives outcome dependency failure and still records metric.
4. graduation eligibility guard remains fail-closed.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.students.models import StudentAdmissionSource, StudentProfileModel, StudentStatus
from app.modules.students.schemas import StudentProfileCreateSchema, StudentStatusChangeSchema
from app.modules.students.service import StudentLifecycleService


class ExecuteResult:
    def __init__(self, *, scalar_one_or_none: object | None = None):
        self._scalar_one_or_none = scalar_one_or_none

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=UTC)
        if getattr(instance, "id", None) is None:
            defaults = {
                "StudentProfileModel": 1001,
                "StudentStatusHistoryModel": 2001,
                "OutboxEventModel": 4001,
            }
            instance.id = defaults.get(instance.__class__.__name__, 1)
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if hasattr(instance, "updated_at") and getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if hasattr(instance, "changed_at") and getattr(instance, "changed_at", None) is None:
            instance.changed_at = now
        if hasattr(instance, "available_at") and getattr(instance, "available_at", None) is None:
            instance.available_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1

    session.refresh.side_effect = fake_refresh
    return session


def _person(*, person_id: int = 101, tenant_id: int = 1) -> MagicMock:
    person = MagicMock()
    person.id = person_id
    person.tenant_id = tenant_id
    person.status = "active"
    return person


def _profile(*, profile_id: int = 1001, tenant_id: int = 1, status: StudentStatus = StudentStatus.ADMITTED) -> StudentProfileModel:
    now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=UTC)
    return StudentProfileModel(
        id=profile_id,
        tenant_id=tenant_id,
        person_id=101,
        student_number="ADM-1-1001",
        cohort_year=2026,
        academic_level=None,
        current_status=status,
        admission_source=StudentAdmissionSource.ADMISSIONS_WORKFLOW,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
    )


def test_create_student_profile_records_outcome_and_metric(
    run_async,
    db_session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StudentLifecycleService(db_session)
    request = StudentProfileCreateSchema(person_id=101, student_number="ADM-1-1001", cohort_year=2026)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=_person(person_id=101, tenant_id=1)),
        ExecuteResult(scalar_one_or_none=None),
    ]

    outcome = MagicMock()
    metric = MagicMock()
    monkeypatch.setattr("app.modules.students.service._record_outcome", outcome)
    monkeypatch.setattr("app.modules.students.service._metric", metric)

    result = run_async(service.create_student_profile(tenant_id=1, request=request, created_by="actor@example.com"))

    assert result.entity.person_id == 101
    outcome.assert_called_once_with(result.entity.id, "student_profile_created", "actor@example.com")
    metric.assert_called_once_with(1, "student_profiles_created", 1)


def test_change_student_status_records_outcome_and_metric(
    run_async,
    db_session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StudentLifecycleService(db_session)
    profile = _profile(status=StudentStatus.ADMITTED)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=profile)

    outcome = MagicMock()
    metric = MagicMock()
    monkeypatch.setattr("app.modules.students.service._record_outcome", outcome)
    monkeypatch.setattr("app.modules.students.service._metric", metric)

    result = run_async(
        service.change_student_status(
            tenant_id=1,
            student_profile_id=profile.id,
            request=StudentStatusChangeSchema(expected_version=1, to_status=StudentStatus.ACTIVE, reason="activate"),
            actor_id="registrar@example.com",
        )
    )

    assert result.entity.current_status == StudentStatus.ACTIVE
    outcome.assert_called_once_with(profile.id, "student_status_active", "registrar@example.com")
    metric.assert_called_once_with(1, "student_status_updates", 1)


def test_create_student_profile_survives_outcome_failure_and_records_metric(
    run_async,
    db_session: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = StudentLifecycleService(db_session)
    request = StudentProfileCreateSchema(person_id=101, student_number="ADM-1-1001", cohort_year=2026)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=_person(person_id=101, tenant_id=1)),
        ExecuteResult(scalar_one_or_none=None),
    ]

    metric = MagicMock()
    monkeypatch.setattr("app.modules.students.service._metric", metric)

    mock_brain = MagicMock()
    mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")

    with patch("app.modules.brain_core.service.brain_core_service", mock_brain):
        result = run_async(service.create_student_profile(tenant_id=1, request=request, created_by="actor@example.com"))

    assert result.entity.id > 0
    metric.assert_called_once_with(1, "student_profiles_created", 1)


def test_change_student_status_graduation_guard_fail_closed(
    run_async,
    db_session: MagicMock,
) -> None:
    service = StudentLifecycleService(db_session)
    profile = _profile(status=StudentStatus.ACTIVE)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=profile)

    class _Eligibility:
        eligible = False
        credits_earned = 100
        minimum_credits = 120
        remaining_required_items = ["thesis"]

    class _DegreeProgressService:
        def __init__(self, _db: Session):
            pass

        async def is_student_eligible_for_graduation(self, *args, **kwargs):
            return _Eligibility()

    with patch("app.modules.degree_progress.service.DegreeProgressService", _DegreeProgressService):
        with pytest.raises(DomainValidationError, match="not eligible for graduation"):
            run_async(
                service.change_student_status(
                    tenant_id=1,
                    student_profile_id=profile.id,
                    request=StudentStatusChangeSchema(
                        expected_version=1,
                        to_status=StudentStatus.GRADUATED,
                        reason="graduation",
                    ),
                    actor_id="registrar@example.com",
                )
            )
