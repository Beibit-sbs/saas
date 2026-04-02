from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.modules.enrollments.models import EnrollmentModel, EnrollmentStatus, EnrollmentType
from app.modules.grades.models import (
    GradeHistoryModel,
    GradeSubmissionModel,
    GradingScaleItemModel,
    GradingScaleModel,
)
from app.modules.grades.schemas import GradeChangeSchema, GradeSubmitSchema
from app.modules.grades.service import GradeLifecycleService
from app.modules.students.models import (
    StudentAdmissionSource,
    StudentProfileModel,
    StudentStatus,
)
from app.platform.events.models import OutboxEventModel


class ScalarListResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return list(self._items)

    def first(self) -> object | None:
        return self._items[0] if self._items else None


class ExecuteResult:
    def __init__(
        self,
        *,
        scalar_one_or_none: object | None = None,
        scalar_one: object | None = None,
        scalars: list[object] | None = None,
        rows: list[object] | None = None,
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalar_one = scalar_one
        self._scalars = scalars or []
        self._rows = rows or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalar_one(self) -> object | None:
        return self._scalar_one

    def scalars(self) -> ScalarListResult:
        return ScalarListResult(self._scalars)

    def all(self) -> list[object]:
        return list(self._rows)


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 23, 18, 0, 0, tzinfo=UTC)
        if getattr(instance, "id", None) is None:
            defaults = {
                "GradeSubmissionModel": 7001,
                "GradeHistoryModel": 8001,
                "OutboxEventModel": 9001,
            }
            instance.id = defaults.get(instance.__class__.__name__, 1)
        if hasattr(instance, "submitted_at") and getattr(instance, "submitted_at", None) is None:
            instance.submitted_at = now
        if hasattr(instance, "changed_at") and getattr(instance, "changed_at", None) is None:
            instance.changed_at = now
        if hasattr(instance, "available_at") and getattr(instance, "available_at", None) is None:
            instance.available_at = now
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.grades.service.log_admin_action", mock)
    return mock


@pytest.fixture(autouse=True)
def _bypass_abac_validators(monkeypatch: pytest.MonkeyPatch):
    async def _allow(*args, **kwargs):
        return None

    monkeypatch.setattr("app.modules.grades.service.validate_grade_submission", _allow)
    monkeypatch.setattr("app.modules.grades.service.validate_grade_modification", _allow)
    monkeypatch.setattr("app.modules.grades.service.validate_grade_ownership", _allow)


@pytest.fixture
def student_profile_factory():
    def factory(**overrides) -> StudentProfileModel:
        now = datetime(2026, 3, 23, 18, 0, 0, tzinfo=UTC)
        return StudentProfileModel(
            id=overrides.get("id", 1001),
            tenant_id=overrides.get("tenant_id", 1),
            person_id=overrides.get("person_id", 101),
            student_number=overrides.get("student_number", "ADM-1-1001"),
            cohort_year=overrides.get("cohort_year", 2026),
            academic_level=overrides.get("academic_level"),
            current_status=overrides.get("current_status", StudentStatus.ACTIVE),
            admission_source=overrides.get(
                "admission_source",
                StudentAdmissionSource.ADMISSIONS_WORKFLOW,
            ),
            metadata_json=overrides.get("metadata_json", {}),
            version=overrides.get("version", 1),
            created_by=overrides.get("created_by", "owner@example.com"),
            updated_by=overrides.get("updated_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


@pytest.fixture
def enrollment_factory():
    def factory(**overrides) -> EnrollmentModel:
        now = datetime(2026, 3, 23, 18, 0, 0, tzinfo=UTC)
        return EnrollmentModel(
            id=overrides.get("id", 4001),
            tenant_id=overrides.get("tenant_id", 1),
            student_profile_id=overrides.get("student_profile_id", 1001),
            course_id=overrides.get("course_id", 701),
            term_id=overrides.get("term_id", 1),
            enrollment_status=overrides.get("enrollment_status", EnrollmentStatus.ENROLLED),
            enrollment_type=overrides.get("enrollment_type", EnrollmentType.REGULAR),
            enrolled_at=overrides.get("enrolled_at", now),
            dropped_at=overrides.get("dropped_at"),
            grade_code=overrides.get("grade_code"),
            grade_points=overrides.get("grade_points"),
            metadata_json=overrides.get("metadata_json", {}),
            version=overrides.get("version", 1),
            created_by=overrides.get("created_by", "owner@example.com"),
            updated_by=overrides.get("updated_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


@pytest.fixture
def scale_factory():
    def factory(**overrides) -> GradingScaleModel:
        return GradingScaleModel(
            id=overrides.get("id", 9001),
            tenant_id=overrides.get("tenant_id", 1),
            name=overrides.get("name", "US-4.0"),
            description=overrides.get("description", "Standard 4.0 scale"),
            is_active=overrides.get("is_active", True),
        )

    return factory


@pytest.fixture
def scale_item_factory():
    def factory(**overrides) -> GradingScaleItemModel:
        return GradingScaleItemModel(
            id=overrides.get("id", 9101),
            tenant_id=overrides.get("tenant_id", 1),
            scale_id=overrides.get("scale_id", 9001),
            grade_code=overrides.get("grade_code", "A"),
            grade_points=overrides.get("grade_points", Decimal("4.00")),
            min_percentage=overrides.get("min_percentage", Decimal("90.00")),
            max_percentage=overrides.get("max_percentage", Decimal("100.00")),
        )

    return factory


@pytest.fixture
def submission_factory():
    def factory(**overrides) -> GradeSubmissionModel:
        now = datetime(2026, 3, 23, 18, 0, 0, tzinfo=UTC)
        return GradeSubmissionModel(
            id=overrides.get("id", 7001),
            tenant_id=overrides.get("tenant_id", 1),
            enrollment_id=overrides.get("enrollment_id", 4001),
            grade_code=overrides.get("grade_code", "A"),
            grade_points=overrides.get("grade_points", Decimal("4.00")),
            grading_scale_id=overrides.get("grading_scale_id", 9001),
            submitted_by=overrides.get("submitted_by", "instructor@example.com"),
            submitted_at=overrides.get("submitted_at", now),
            version=overrides.get("version", 1),
            metadata_json=overrides.get("metadata_json", {}),
        )

    return factory


class TestGradeSubmission:
    def test_submit_grade_success(
        self,
        run_async,
        db_session,
        audit_mock,
        enrollment_factory,
        scale_factory,
        scale_item_factory,
    ) -> None:
        service = GradeLifecycleService(db_session)
        request = GradeSubmitSchema(
            enrollment_id=4001,
            grading_scale_id=9001,
            grade_code="A",
            grade_points=Decimal("4.00"),
        )
        enrollment = enrollment_factory(id=4001, tenant_id=1, enrollment_status=EnrollmentStatus.COMPLETED)

        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=enrollment),
            ExecuteResult(scalar_one_or_none=type("CourseStub", (), {"tenant_id": 1})()),
            ExecuteResult(scalar_one_or_none=None),
            ExecuteResult(scalar_one_or_none=scale_factory(id=9001, tenant_id=1, is_active=True)),
            ExecuteResult(scalars=[scale_item_factory(scale_id=9001, grade_code="A", grade_points=Decimal("4.00"))]),
        ]

        result = run_async(service.submit_grade(tenant_id=1, request=request, actor_id="instructor@example.com"))

        assert result.enrollment_id == 4001
        assert result.grade_code == "A"
        assert result.grade_points == Decimal("4.00")
        assert enrollment.grade_code == "A"
        assert enrollment.grade_points == Decimal("4.00")
        added_instances = [call.args[0] for call in db_session.add.call_args_list]
        assert any(isinstance(item, OutboxEventModel) for item in added_instances)
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()

    def test_submit_grade_tenant_isolation_not_found(self, run_async, db_session) -> None:
        service = GradeLifecycleService(db_session)
        request = GradeSubmitSchema(
            enrollment_id=9999,
            grading_scale_id=9001,
            grade_code="A",
            grade_points=Decimal("4.00"),
        )
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            run_async(service.submit_grade(tenant_id=1, request=request, actor_id="instructor@example.com"))


class TestGradeChange:
    def test_change_grade_success(
        self,
        run_async,
        db_session,
        audit_mock,
        enrollment_factory,
        scale_factory,
        scale_item_factory,
        submission_factory,
    ) -> None:
        service = GradeLifecycleService(db_session)
        enrollment = enrollment_factory(id=4001, tenant_id=1, enrollment_status=EnrollmentStatus.COMPLETED)
        submission = submission_factory(enrollment_id=4001, version=1, grade_code="B", grade_points=Decimal("3.00"))

        request = GradeChangeSchema(
            enrollment_id=4001,
            grading_scale_id=9001,
            new_grade_code="A",
            new_grade_points=Decimal("4.00"),
            expected_version=1,
            reason="regrade",
        )

        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=enrollment),
            ExecuteResult(scalar_one_or_none=submission),
            ExecuteResult(scalar_one_or_none=scale_factory(id=9001, tenant_id=1, is_active=True)),
            ExecuteResult(scalars=[scale_item_factory(scale_id=9001, grade_code="A", grade_points=Decimal("4.00"))]),
        ]

        result = run_async(service.change_grade(tenant_id=1, request=request, actor_id="admin@example.com"))

        assert result.grade_code == "A"
        assert result.version == 2
        assert enrollment.grade_code == "A"
        assert enrollment.grade_points == Decimal("4.00")
        history_rows = [
            call.args[0]
            for call in db_session.add.call_args_list
            if isinstance(call.args[0], GradeHistoryModel)
        ]
        assert len(history_rows) == 1
        assert history_rows[0].previous_grade_code == "B"
        assert history_rows[0].new_grade_code == "A"
        assert history_rows[0].version == 2
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()

    def test_change_grade_optimistic_lock_conflict(
        self,
        run_async,
        db_session,
        enrollment_factory,
        submission_factory,
    ) -> None:
        service = GradeLifecycleService(db_session)
        enrollment = enrollment_factory(id=4001, tenant_id=1, enrollment_status=EnrollmentStatus.COMPLETED)
        submission = submission_factory(enrollment_id=4001, version=5)

        request = GradeChangeSchema(
            enrollment_id=4001,
            grading_scale_id=9001,
            new_grade_code="A",
            new_grade_points=Decimal("4.00"),
            expected_version=4,
        )

        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=enrollment),
            ExecuteResult(scalar_one_or_none=submission),
        ]

        with pytest.raises(OptimisticLockConflictError):
            run_async(service.change_grade(tenant_id=1, request=request, actor_id="admin@example.com"))


class TestTranscriptAndGpa:
    def test_calculate_student_gpa(self, run_async, db_session, student_profile_factory) -> None:
        service = GradeLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(
                rows=[
                    (Decimal("4.00"), 3, "1"),
                    (Decimal("3.00"), 4, "1"),
                ]
            ),
        ]

        result = run_async(service.calculate_student_gpa(tenant_id=1, student_profile_id=1001))

        assert result == Decimal("3.43")

    def test_get_student_transcript(self, run_async, db_session, student_profile_factory) -> None:
        service = GradeLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(
                rows=[
                    (
                        1,
                        "2026-SPRING",
                        "Spring 2026",
                        701,
                        "CS101",
                        "Intro to CS",
                        3,
                        "1",
                        "A",
                        Decimal("4.00"),
                        datetime(2026, 1, 15, tzinfo=UTC),
                    )
                ]
            ),
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(rows=[(Decimal("4.00"), 3, "1")]),
        ]

        result = run_async(service.get_student_transcript(tenant_id=1, student_profile_id=1001))

        assert result.student_profile_id == 1001
        assert result.total_credits == 3
        assert result.gpa == Decimal("4.00")
        assert len(result.items) == 1
        assert result.items[0].course_code == "CS101"
