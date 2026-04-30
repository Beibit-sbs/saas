from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.enrollments.models import (
    EnrollmentModel,
    EnrollmentStatus,
    EnrollmentStatusHistoryModel,
    EnrollmentType,
)
from app.modules.enrollments.schemas import (
    EnrollmentCreateSchema,
    EnrollmentDropSchema,
    EnrollmentStatusChangeSchema,
)
from app.modules.enrollments.service import EnrollmentLifecycleService
from app.modules.scheduling.models import SectionStatus
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
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalar_one = scalar_one
        self._scalars = scalars or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalar_one(self) -> object | None:
        return self._scalar_one

    def scalars(self) -> ScalarListResult:
        return ScalarListResult(self._scalars)

    def scalar(self) -> object | None:
        if self._scalar_one is not None:
            return self._scalar_one
        if self._scalar_one_or_none is not None:
            return self._scalar_one_or_none
        return None


@pytest.fixture
def run_async():
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 23, 16, 0, 0, tzinfo=UTC)
        if getattr(instance, "id", None) is None:
            defaults = {
                "EnrollmentModel": 4001,
                "EnrollmentStatusHistoryModel": 5001,
                "OutboxEventModel": 6001,
            }
            instance.id = defaults.get(instance.__class__.__name__, 1)
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if hasattr(instance, "updated_at") and getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if hasattr(instance, "changed_at") and getattr(instance, "changed_at", None) is None:
            instance.changed_at = now
        if hasattr(instance, "enrolled_at") and getattr(instance, "enrolled_at", None) is None:
            instance.enrolled_at = now
        if hasattr(instance, "available_at") and getattr(instance, "available_at", None) is None:
            instance.available_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def billing_guard_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="assert_billing_write_allowed")
    monkeypatch.setattr("app.modules.enrollments.service.assert_billing_write_allowed", mock)
    return mock


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.enrollments.service.log_admin_action", mock)
    return mock


@pytest.fixture
def student_profile_factory():
    def factory(**overrides) -> StudentProfileModel:
        now = datetime(2026, 3, 23, 16, 0, 0, tzinfo=UTC)
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
def course_factory():
    def factory(**overrides):
        course = MagicMock()
        course.id = overrides.get("id", 701)
        course.tenant_id = overrides.get("tenant_id", "1")
        course.status = overrides.get("status", "active")
        return course

    return factory


@pytest.fixture
def term_factory():
    def factory(**overrides):
        term = MagicMock()
        term.id = overrides.get("id", 1)
        term.tenant_id = overrides.get("tenant_id", 1)
        term.status = overrides.get("status", "active")
        term.term_code = overrides.get("term_code", "2026-SPRING")
        return term

    return factory


@pytest.fixture
def section_factory():
    def factory(**overrides):
        section = MagicMock()
        section.id = overrides.get("id", 501)
        section.tenant_id = overrides.get("tenant_id", 1)
        section.course_id = overrides.get("course_id", 701)
        section.term_id = overrides.get("term_id", 1)
        section.max_capacity = overrides.get("max_capacity", 30)
        section.status = overrides.get("status", SectionStatus.SCHEDULED)
        return section

    return factory


@pytest.fixture
def enrollment_factory():
    def factory(**overrides) -> EnrollmentModel:
        now = datetime(2026, 3, 23, 16, 0, 0, tzinfo=UTC)
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


class TestEnrollStudent:
    def test_success(
        self,
        run_async,
        db_session,
        audit_mock,
        billing_guard_mock,
        student_profile_factory,
        course_factory,
        term_factory,
        section_factory,
    ) -> None:
        service = EnrollmentLifecycleService(db_session)
        request = EnrollmentCreateSchema(
            student_profile_id=1001,
            course_id=701,
            term_id=1,
            section_id=501,
            enrollment_status=EnrollmentStatus.ENROLLED,
        )
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=course_factory(id=701, tenant_id="1")),
            ExecuteResult(scalar_one_or_none=term_factory(id=1, tenant_id=1)),
            ExecuteResult(scalars=[]),
            ExecuteResult(scalar_one_or_none=section_factory(id=501, tenant_id=1, course_id=701, term_id=1)),
            ExecuteResult(scalar_one=0),
            ExecuteResult(scalars=[]),
        ]

        result = run_async(service.enroll_student(tenant_id=1, request=request, actor_id="registrar@example.com"))

        assert result.student_profile_id == 1001
        assert result.course_id == 701
        assert result.term_id == 1
        assert result.enrollment_status == EnrollmentStatus.ENROLLED
        added_instances = [call.args[0] for call in db_session.add.call_args_list]
        assert any(isinstance(item, OutboxEventModel) for item in added_instances)
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()
        billing_guard_mock.assert_called_once_with(1, action="enrollments.create")

    def test_tenant_missing_fail_closed(self, run_async, db_session) -> None:
        service = EnrollmentLifecycleService(db_session)
        request = EnrollmentCreateSchema(student_profile_id=1001, course_id=701, term_id=1, section_id=501)

        with pytest.raises(TenantRequiredError):
            run_async(service.enroll_student(tenant_id=None, request=request, actor_id="registrar@example.com"))

    def test_student_not_found(self, run_async, db_session) -> None:
        service = EnrollmentLifecycleService(db_session)
        request = EnrollmentCreateSchema(student_profile_id=1001, course_id=701, term_id=1, section_id=501)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            run_async(service.enroll_student(tenant_id=1, request=request, actor_id="registrar@example.com"))

    def test_course_placeholder_tenant_mismatch(self, run_async, db_session, student_profile_factory, course_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        request = EnrollmentCreateSchema(student_profile_id=1001, course_id=701, term_id=1, section_id=501)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=course_factory(id=701, tenant_id="9")),
        ]

        with pytest.raises(TenantResourceNotFoundError, match="Course 701"):
            run_async(service.enroll_student(tenant_id=1, request=request, actor_id="registrar@example.com"))


def test_list_tenant_enrollment_consistency_report_detects_issues(
    run_async,
    db_session,
    enrollment_factory,
) -> None:
    db_session.execute.side_effect = [
        ExecuteResult(
            scalars=[
                enrollment_factory(id=4001, student_profile_id=1001, course_id=701, term_id=1),
                enrollment_factory(id=4002, student_profile_id=9999, course_id=702, term_id=2),
            ]
        ),
        ExecuteResult(scalars=[1001]),
        ExecuteResult(scalars=[701]),
        ExecuteResult(scalars=[1]),
    ]

    service = EnrollmentLifecycleService(db_session)
    result = run_async(service.list_tenant_enrollment_consistency_report(tenant_id=1))

    assert result.enrollment_count == 2
    course_query = db_session.execute.call_args_list[2].args[0]
    assert str(course_query.compile(compile_kwargs={"literal_binds": True})).find("tenant_id = 1") != -1
    issue_types = [issue.issue_type for issue in result.issues]
    assert "enrollment_missing_student_profile" in issue_types
    assert "enrollment_missing_course" in issue_types
    assert "enrollment_missing_term" in issue_types

    def test_duplicate_active_enrollment_prevented(
        self,
        run_async,
        db_session,
        student_profile_factory,
        course_factory,
        term_factory,
        enrollment_factory,
    ) -> None:
        service = EnrollmentLifecycleService(db_session)
        request = EnrollmentCreateSchema(student_profile_id=1001, course_id=701, term_id=1, section_id=501)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=course_factory(id=701, tenant_id="1")),
            ExecuteResult(scalar_one_or_none=term_factory(id=1, tenant_id=1)),
            ExecuteResult(scalars=[enrollment_factory(student_profile_id=1001, course_id=701, term_id=1)]),
        ]

        with pytest.raises(DomainValidationError, match="Active enrollment already exists"):
            run_async(service.enroll_student(tenant_id=1, request=request, actor_id="registrar@example.com"))


class TestReadOperations:
    def test_get_enrollment_success(self, run_async, db_session, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(
            scalar_one_or_none=enrollment_factory(id=4001, tenant_id=1)
        )

        result = run_async(service.get_enrollment(tenant_id=1, enrollment_id=4001))

        assert result.id == 4001
        assert result.tenant_id == 1

    def test_list_student_enrollments(self, run_async, db_session, student_profile_factory, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one=2),
            ExecuteResult(
                scalars=[
                    enrollment_factory(id=4001, tenant_id=1),
                    enrollment_factory(id=4002, tenant_id=1, term_id=2),
                ]
            ),
        ]

        result = run_async(
            service.list_student_enrollments(
                tenant_id=1,
                student_profile_id=1001,
                page=1,
                page_size=20,
            )
        )

        assert result.total == 2
        assert len(result.items) == 2

    def test_list_course_roster(self, run_async, db_session, course_factory, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=course_factory(id=701, tenant_id="1")),
            ExecuteResult(scalar_one=1),
            ExecuteResult(scalars=[enrollment_factory(course_id=701, term_id=1)]),
        ]

        result = run_async(
            service.list_course_roster(
                tenant_id=1,
                course_id=701,
                term_id=1,
                page=1,
                page_size=50,
            )
        )

        assert result.total == 1
        assert result.items[0].course_id == 701
        assert result.items[0].term_id == 1

    def test_get_active_enrollment_for_student_course_term(self, run_async, db_session, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(
            scalars=[enrollment_factory(student_profile_id=1001, course_id=701, term_id=1)]
        )

        result = run_async(
            service.get_active_enrollment_for_student_course_term(
                tenant_id=1,
                student_profile_id=1001,
                course_id=701,
                term_id=1,
            )
        )

        assert result is not None
        assert result.term_id == 1


class TestStatusLifecycle:
    def test_change_status_merges_metadata_and_appends_history(
        self,
        run_async,
        db_session,
        audit_mock,
        enrollment_factory,
    ) -> None:
        service = EnrollmentLifecycleService(db_session)
        enrollment = enrollment_factory(
            enrollment_status=EnrollmentStatus.ENROLLED,
            version=1,
            metadata_json={"existing": 1, "nested": {"left": True}},
        )
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=enrollment)

        result = run_async(
            service.change_enrollment_status(
                tenant_id=1,
                enrollment_id=enrollment.id,
                request=EnrollmentStatusChangeSchema(
                    expected_version=1,
                    to_status=EnrollmentStatus.SUSPENDED,
                    reason="disciplinary_hold",
                    metadata_json={"nested": {"right": True}, "new": 2},
                ),
                actor_id="registrar@example.com",
            )
        )

        assert result.enrollment_status == EnrollmentStatus.SUSPENDED
        assert result.version == 2
        assert result.metadata_json == {
            "existing": 1,
            "nested": {"left": True, "right": True},
            "new": 2,
        }
        history_rows = [
            call.args[0]
            for call in db_session.add.call_args_list
            if isinstance(call.args[0], EnrollmentStatusHistoryModel)
        ]
        assert len(history_rows) == 1
        assert history_rows[0].from_status == EnrollmentStatus.ENROLLED
        assert history_rows[0].to_status == EnrollmentStatus.SUSPENDED
        assert history_rows[0].version == 2  # enrollment v1 → v2 on this transition
        audit_mock.assert_called_once()

    def test_optimistic_lock_conflict(self, run_async, db_session, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        enrollment = enrollment_factory(enrollment_status=EnrollmentStatus.ENROLLED, version=4)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=enrollment)

        with pytest.raises(OptimisticLockConflictError):
            run_async(
                service.change_enrollment_status(
                    tenant_id=1,
                    enrollment_id=enrollment.id,
                    request=EnrollmentStatusChangeSchema(
                        expected_version=3,
                        to_status=EnrollmentStatus.SUSPENDED,
                    ),
                    actor_id="registrar@example.com",
                )
            )

    def test_drop_enrollment(self, run_async, db_session, audit_mock, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        enrollment = enrollment_factory(enrollment_status=EnrollmentStatus.ENROLLED, version=2)
        # First execute: load enrollment; second: _check_drop_deadline term lookup → None (no deadline)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=enrollment),
            ExecuteResult(scalar_one_or_none=None),
        ]

        result = run_async(
            service.drop_enrollment(
                tenant_id=1,
                enrollment_id=enrollment.id,
                request=EnrollmentDropSchema(
                    expected_version=2,
                    reason="student_requested_drop",
                    metadata_json={"source": "portal"},
                ),
                actor_id="registrar@example.com",
            )
        )

        assert result.enrollment_status == EnrollmentStatus.DROPPED
        assert result.dropped_at is not None
        assert result.version == 3
        assert result.metadata_json["source"] == "portal"
        history_rows = [
            call.args[0]
            for call in db_session.add.call_args_list
            if isinstance(call.args[0], EnrollmentStatusHistoryModel)
        ]
        assert len(history_rows) == 1
        assert history_rows[0].version == 3  # enrollment v2 → v3 on drop
        audit_mock.assert_called_once()

    def test_invalid_terminal_transition(self, run_async, db_session, enrollment_factory) -> None:
        service = EnrollmentLifecycleService(db_session)
        enrollment = enrollment_factory(enrollment_status=EnrollmentStatus.COMPLETED, version=2)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=enrollment)

        with pytest.raises(DomainValidationError, match="not allowed"):
            run_async(
                service.change_enrollment_status(
                    tenant_id=1,
                    enrollment_id=enrollment.id,
                    request=EnrollmentStatusChangeSchema(
                        expected_version=2,
                        to_status=EnrollmentStatus.ENROLLED,
                    ),
                    actor_id="registrar@example.com",
                )
            )