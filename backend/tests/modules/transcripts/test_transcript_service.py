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
        if getattr(instance, "id", None) is None:
            if instance.__class__.__name__ == "TranscriptRecordModel":
                instance.id = 9101
            if instance.__class__.__name__ == "TranscriptSnapshotModel":
                instance.id = 9301
        if hasattr(instance, "recorded_at") and getattr(instance, "recorded_at", None) is None:
            instance.recorded_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.transcripts.service.log_admin_action", mock)
    return mock


@pytest.fixture
def billing_usage_mocks(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    billing_write = MagicMock(name="assert_billing_write_allowed")
    quota_check = MagicMock(name="assert_quota_with_increment")
    usage_record = MagicMock(name="record_usage_event")
    monkeypatch.setattr("app.modules.transcripts.service.assert_billing_write_allowed", billing_write)
    monkeypatch.setattr("app.modules.transcripts.service.assert_quota_with_increment", quota_check)
    monkeypatch.setattr("app.modules.transcripts.service.record_usage_event", usage_record)
    return {
        "billing_write": billing_write,
        "quota_check": quota_check,
        "usage_record": usage_record,
    }


@pytest.fixture(autouse=True)
def _apply_billing_usage_mocks(billing_usage_mocks: dict[str, MagicMock]) -> None:
    _ = billing_usage_mocks


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


def test_generate_transcript_success(
    monkeypatch: pytest.MonkeyPatch,
    run_async,
    db_session,
    enrollment_factory,
    audit_mock: MagicMock,
    billing_usage_mocks: dict[str, MagicMock],
) -> None:
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
    assert audit_mock.call_count == 1
    assert audit_mock.call_args.kwargs["action"] == "transcripts.transcript.generated"
    billing_usage_mocks["billing_write"].assert_called_once_with(1, action="transcripts.generate")
    billing_usage_mocks["quota_check"].assert_called_once_with(1, "transcripts_generated", increment=1)
    billing_usage_mocks["usage_record"].assert_called_once_with(
        tenant_id=1,
        metric="transcripts_generated",
        value=1,
    )


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


def test_get_student_transcript_records_read_usage(
    monkeypatch: pytest.MonkeyPatch,
    run_async,
    db_session,
    billing_usage_mocks: dict[str, MagicMock],
) -> None:
    async def fake_gpa(self, tenant_id: int, *, student_profile_id: int):
        return Decimal("4.00")

    monkeypatch.setattr("app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa", fake_gpa)

    term = MagicMock(id=1, term_code="2026-SPRING", term_name="Spring 2026")
    course = MagicMock(id=701, course_code="CS101", title="Intro to CS", credits=3, tenant_id="1")
    record = TranscriptRecordModel(
        id=9201,
        tenant_id=1,
        student_profile_id=1001,
        enrollment_id=4001,
        course_id=701,
        term_id=1,
        grade_code="A",
        grade_points=Decimal("4.00"),
        credits=3,
        version=1,
        metadata_json={},
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),
        ExecuteResult(scalars=[record]),
        ExecuteResult(scalar_one_or_none=course),
        ExecuteResult(scalar_one_or_none=term),
    ]

    service = TranscriptService(db_session)
    result = run_async(service.get_student_transcript(tenant_id=1, student_profile_id=1001))

    assert result.student_profile_id == 1001
    assert result.total_credits == 3
    assert len(result.items) == 1
    billing_usage_mocks["usage_record"].assert_called_once_with(
        tenant_id=1,
        metric="transcripts_read",
        value=1,
    )


def test_create_snapshot_emits_audit(
    monkeypatch: pytest.MonkeyPatch,
    run_async,
    db_session,
    enrollment_factory,
    audit_mock: MagicMock,
) -> None:
    async def fake_gpa(self, tenant_id: int, *, student_profile_id: int):
        return Decimal("3.80")

    monkeypatch.setattr("app.modules.transcripts.service.GradeLifecycleService.calculate_student_gpa", fake_gpa)

    def _add_with_snapshot_id(instance: object) -> None:
        if instance.__class__.__name__ == "TranscriptSnapshotModel" and getattr(instance, "id", None) is None:
            instance.id = 9301

    db_session.add.side_effect = _add_with_snapshot_id

    def _refresh_with_snapshot_id(instance: object) -> None:
        if instance.__class__.__name__ == "TranscriptSnapshotModel" and getattr(instance, "id", None) is None:
            instance.id = 9301

    db_session.refresh.side_effect = _refresh_with_snapshot_id

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
    result = run_async(
        service.create_transcript_snapshot(
            tenant_id=1,
            student_profile_id=1001,
            actor_id="registrar@example.com",
        )
    )

    assert result.student_profile_id == 1001
    # one audit for transcript generation + one audit for snapshot creation
    assert audit_mock.call_count == 2
    actions = [call.kwargs.get("action") for call in audit_mock.call_args_list]
    assert "transcripts.transcript.generated" in actions
    assert "transcripts.snapshot.created" in actions


def test_get_transcript_consistency_report_detects_issues(run_async, db_session, enrollment_factory) -> None:
    enrollment_match = enrollment_factory(
        id=4001,
        course_id=701,
        term_id=1,
        grade_code="A",
        grade_points=Decimal("4.00"),
    )
    enrollment_mismatch = enrollment_factory(
        id=4002,
        course_id=702,
        term_id=2,
        grade_code="B",
        grade_points=Decimal("3.00"),
    )

    matching_record = TranscriptRecordModel(
        id=9201,
        tenant_id=1,
        student_profile_id=1001,
        enrollment_id=4001,
        course_id=701,
        term_id=1,
        grade_code="A",
        grade_points=Decimal("4.00"),
        credits=3,
        version=1,
        metadata_json={},
    )
    mismatched_record = TranscriptRecordModel(
        id=9202,
        tenant_id=1,
        student_profile_id=1001,
        enrollment_id=4002,
        course_id=702,
        term_id=2,
        grade_code="C",
        grade_points=Decimal("2.00"),
        credits=3,
        version=1,
        metadata_json={},
    )
    dangling_record = TranscriptRecordModel(
        id=9203,
        tenant_id=1,
        student_profile_id=1001,
        enrollment_id=4999,
        course_id=799,
        term_id=9,
        grade_code="A",
        grade_points=Decimal("4.00"),
        credits=2,
        version=1,
        metadata_json={},
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=MagicMock(id=1001, tenant_id=1)),
        ExecuteResult(scalars=[enrollment_match, enrollment_mismatch]),
        ExecuteResult(scalars=[matching_record, mismatched_record, dangling_record]),
    ]

    service = TranscriptService(db_session)
    result = run_async(service.get_student_transcript_consistency_report(tenant_id=1, student_profile_id=1001))

    assert result.student_profile_id == 1001
    assert result.enrollment_count == 2
    assert result.transcript_record_count == 3
    assert result.issue_count == 3
    issue_types = [issue.issue_type for issue in result.issues]
    assert "transcript_record_mismatch" in issue_types
    assert "dangling_transcript_record" in issue_types


def test_list_tenant_transcript_consistency_reports_filters_students_with_issues(
    run_async,
    db_session,
    enrollment_factory,
) -> None:
    enrollment_clean = enrollment_factory(
        id=4001,
        student_profile_id=1001,
        course_id=701,
        term_id=1,
        grade_code="A",
        grade_points=Decimal("4.00"),
    )
    enrollment_problem = enrollment_factory(
        id=4002,
        student_profile_id=1002,
        course_id=702,
        term_id=2,
        grade_code="B",
        grade_points=Decimal("3.00"),
    )

    record_clean = TranscriptRecordModel(
        id=9201,
        tenant_id=1,
        student_profile_id=1001,
        enrollment_id=4001,
        course_id=701,
        term_id=1,
        grade_code="A",
        grade_points=Decimal("4.00"),
        credits=3,
        version=1,
        metadata_json={},
    )
    record_problem = TranscriptRecordModel(
        id=9202,
        tenant_id=1,
        student_profile_id=1002,
        enrollment_id=4002,
        course_id=702,
        term_id=2,
        grade_code="C",
        grade_points=Decimal("2.00"),
        credits=3,
        version=1,
        metadata_json={},
    )

    db_session.execute.side_effect = [
        ExecuteResult(scalars=[enrollment_clean, enrollment_problem]),
        ExecuteResult(scalars=[record_clean, record_problem]),
    ]

    service = TranscriptService(db_session)
    result = run_async(service.list_tenant_transcript_consistency_reports(tenant_id=1))

    assert result.scanned_student_count == 2
    assert result.students_with_issues == 1
    assert result.total_issue_count == 2
    assert len(result.reports) == 1
    assert result.reports[0].student_profile_id == 1002
    assert result.reports[0].issue_count == 2
