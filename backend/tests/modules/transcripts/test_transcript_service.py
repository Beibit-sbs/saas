from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import OptimisticLockConflictError, TenantResourceNotFoundError
from app.modules.enrollments.models import EnrollmentModel, EnrollmentStatus, EnrollmentType
from app.modules.transcripts.models import TranscriptRecordModel
from app.modules.transcripts.service import TranscriptService


class ScalarListResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return list(self._items)


class ExecuteResult:
    def __init__(self, *, scalar_one_or_none: object | None = None, scalars: list[object] | None = None):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalars = scalars or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalars(self) -> ScalarListResult:
        return ScalarListResult(self._scalars)


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 24, 10, 0, 0, tzinfo=UTC)
        if getattr(instance, "id", None) is None and instance.__class__.__name__ == "TranscriptRecordModel":
            instance.id = 9101
        if hasattr(instance, "recorded_at") and getattr(instance, "recorded_at", None) is None:
            instance.recorded_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def enrollment_factory():
    def factory(**overrides) -> EnrollmentModel:
        now = datetime(2026, 3, 24, 10, 0, 0, tzinfo=UTC)
        return EnrollmentModel(
            id=overrides.get("id", 4001),
            tenant_id=overrides.get("tenant_id", 1),
            student_profile_id=overrides.get("student_profile_id", 1001),
            course_id=overrides.get("course_id", 701),
            term_id=overrides.get("term_id", 1),
            enrollment_status=overrides.get("enrollment_status", EnrollmentStatus.COMPLETED),
            enrollment_type=overrides.get("enrollment_type", EnrollmentType.REGULAR),
            enrolled_at=overrides.get("enrolled_at", now),
            grade_code=overrides.get("grade_code", "A"),
            grade_points=overrides.get("grade_points", Decimal("4.00")),
            metadata_json=overrides.get("metadata_json", {}),
            version=overrides.get("version", 1),
            created_by=overrides.get("created_by", "owner@example.com"),
            updated_by=overrides.get("updated_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


def test_generate_transcript_success(monkeypatch: pytest.MonkeyPatch, run_async, db_session, enrollment_factory) -> None:
    async def fake_gpa(self, tenant_id: int, *, student_profile_id: int):
        return Decimal("3.75")

    monkeypatch.setattr("app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa", fake_gpa)

    course = MagicMock(id=701, course_code="CS101", title="Intro to CS", credits=3, tenant_id="1")
    term = MagicMock(id=1, term_code="2026-SPRING", term_name="Spring 2026")

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),
        ExecuteResult(scalars=[enrollment_factory(id=4001, term_id=1, course_id=701)]),
        ExecuteResult(scalar_one_or_none=course),
        ExecuteResult(scalar_one_or_none=term),
        ExecuteResult(scalar_one_or_none=None),
    ]

    service = TranscriptService(db_session)
    result = run_async(service.generate_transcript(tenant_id=1, student_profile_id=1001, actor_id="registrar@example.com"))

    assert result.student_profile_id == 1001
    assert result.total_credits == 3
    assert result.gpa == Decimal("3.75")
    assert len(result.items) == 1
    assert result.items[0].course_code == "CS101"
    db_session.commit.assert_called_once()


def test_generate_transcript_optimistic_lock(monkeypatch: pytest.MonkeyPatch, run_async, db_session, enrollment_factory) -> None:
    async def fake_gpa(self, tenant_id: int, *, student_profile_id: int):
        return Decimal("3.00")

    monkeypatch.setattr("app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa", fake_gpa)

    course = MagicMock(id=701, course_code="CS101", title="Intro to CS", credits=3, tenant_id="1")
    term = MagicMock(id=1, term_code="2026-SPRING", term_name="Spring 2026")
    existing = TranscriptRecordModel(
        id=9201,
        tenant_id=1,
        student_profile_id=1001,
        enrollment_id=4001,
        course_id=701,
        term_id=1,
        grade_code="A",
        grade_points=Decimal("4.00"),
        credits=3,
        version=3,
        metadata_json={},
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),
        ExecuteResult(scalars=[enrollment_factory(id=4001)]),
        ExecuteResult(scalar_one_or_none=course),
        ExecuteResult(scalar_one_or_none=term),
        ExecuteResult(scalar_one_or_none=existing),
    ]

    service = TranscriptService(db_session)
    with pytest.raises(OptimisticLockConflictError):
        run_async(
            service.generate_transcript(
                tenant_id=1,
                student_profile_id=1001,
                actor_id="registrar@example.com",
                expected_record_version=2,
            )
        )


def test_get_student_transcript_tenant_not_found(run_async, db_session) -> None:
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)
    service = TranscriptService(db_session)

    with pytest.raises(TenantResourceNotFoundError):
        run_async(service.get_student_transcript(tenant_id=1, student_profile_id=1001))
