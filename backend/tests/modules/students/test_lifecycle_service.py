from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.students.models import (
    StudentAdmissionSource,
    StudentProfileModel,
    StudentProgramBindingModel,
    StudentProgramBindingState,
    StudentStatus,
    StudentStatusHistoryModel,
)
from app.modules.students.schemas import (
    AdmissionsProvisionStudentRequestSchema,
    StudentProfileCreateSchema,
    StudentProgramBindingCreateSchema,
    StudentStatusChangeSchema,
)
from app.modules.students.service import StudentLifecycleService
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
                "StudentProgramBindingModel": 3001,
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


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.students.service.log_admin_action", mock)
    return mock


@pytest.fixture
def person_factory():
    def factory(**overrides):
        person = MagicMock()
        person.id = overrides.get("id", 101)
        person.tenant_id = overrides.get("tenant_id", 1)
        person.status = overrides.get("status", "active")
        return person

    return factory


@pytest.fixture
def program_factory():
    def factory(**overrides):
        program = MagicMock()
        program.id = overrides.get("id", 501)
        program.tenant_id = overrides.get("tenant_id", 1)
        program.status = overrides.get("status", "active")
        return program

    return factory


@pytest.fixture
def student_profile_factory():
    def factory(**overrides) -> StudentProfileModel:
        now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=UTC)
        return StudentProfileModel(
            id=overrides.get("id", 1001),
            tenant_id=overrides.get("tenant_id", 1),
            person_id=overrides.get("person_id", 101),
            student_number=overrides.get("student_number", "ADM-1-1001"),
            cohort_year=overrides.get("cohort_year", 2026),
            academic_level=overrides.get("academic_level"),
            current_status=overrides.get("current_status", StudentStatus.ADMITTED),
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
def binding_factory():
    def factory(**overrides) -> StudentProgramBindingModel:
        now = datetime(2026, 3, 23, 10, 0, 0, tzinfo=UTC)
        return StudentProgramBindingModel(
            id=overrides.get("id", 3001),
            tenant_id=overrides.get("tenant_id", 1),
            student_profile_id=overrides.get("student_profile_id", 1001),
            program_id=overrides.get("program_id", 501),
            is_primary=overrides.get("is_primary", True),
            binding_state=overrides.get("binding_state", StudentProgramBindingState.ACTIVE),
            started_at=overrides.get("started_at", now),
            ended_at=overrides.get("ended_at"),
            metadata_json=overrides.get("metadata_json", {}),
            version=overrides.get("version", 1),
            created_by=overrides.get("created_by", "owner@example.com"),
            updated_by=overrides.get("updated_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


class TestCreateStudentProfile:
    def test_success(self, run_async, db_session, audit_mock, person_factory) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProfileCreateSchema(
            person_id=101,
            student_number="ADM-1-1001",
            cohort_year=2026,
        )
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=None),
        ]

        result = run_async(service.create_student_profile(tenant_id=1, request=request, created_by="actor@example.com"))

        assert result.entity.tenant_id == 1
        assert result.entity.person_id == 101
        assert result.entity.current_status == StudentStatus.ADMITTED
        assert result.idempotent_replay is False
        added_instances = [call.args[0] for call in db_session.add.call_args_list]
        assert any(isinstance(item, OutboxEventModel) for item in added_instances)
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()

    def test_tenant_missing_fail_closed(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProfileCreateSchema(person_id=101, student_number="ADM-1-1001", cohort_year=2026)

        with pytest.raises(TenantRequiredError):
            run_async(service.create_student_profile(tenant_id=None, request=request, created_by="actor@example.com"))

    def test_person_not_found_in_tenant(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProfileCreateSchema(person_id=101, student_number="ADM-1-1001", cohort_year=2026)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

        with pytest.raises(DomainValidationError, match="Person not found"):
            run_async(service.create_student_profile(tenant_id=1, request=request, created_by="actor@example.com"))

    def test_duplicate_profile_returns_replay(self, run_async, db_session, person_factory, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProfileCreateSchema(person_id=101, student_number="ADM-1-1001", cohort_year=2026)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=student_profile_factory(person_id=101, tenant_id=1)),
        ]

        result = run_async(service.create_student_profile(tenant_id=1, request=request, created_by="actor@example.com"))
        assert result.idempotent_replay is True
        assert result.entity.person_id == 101


class TestGetStudentProfile:
    def test_success(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(
            scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)
        )

        result = run_async(service.get_student_profile(tenant_id=1, student_profile_id=1001))

        assert result.id == 1001
        assert result.tenant_id == 1

    def test_cross_tenant_access_blocked(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            run_async(service.get_student_profile(tenant_id=1, student_profile_id=1001))

    def test_not_found(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            run_async(service.get_student_profile(tenant_id=1, student_profile_id=9999))


class TestListStudentProfiles:
    def test_pagination(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one=2),
            ExecuteResult(
                scalars=[
                    student_profile_factory(id=1001, tenant_id=1),
                    student_profile_factory(id=1002, tenant_id=1),
                ]
            ),
        ]

        result = run_async(service.list_student_profiles(tenant_id=1, page=1, page_size=2))

        assert result.total == 2
        assert result.page == 1
        assert len(result.items) == 2

    def test_tenant_isolation(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.side_effect = [ExecuteResult(scalar_one=0), ExecuteResult(scalars=[])]

        result = run_async(service.list_student_profiles(tenant_id=9, page=1, page_size=20))

        assert result.total == 0
        assert result.items == []

    def test_optional_status_filter(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one=1),
            ExecuteResult(
                scalars=[
                    student_profile_factory(
                        id=1101,
                        tenant_id=1,
                        current_status=StudentStatus.ACTIVE,
                    )
                ]
            ),
        ]

        result = run_async(
            service.list_student_profiles(
                tenant_id=1,
                page=1,
                page_size=20,
                status=StudentStatus.ACTIVE,
            )
        )

        assert result.total == 1
        assert result.items[0].current_status == StudentStatus.ACTIVE


class TestChangeStudentStatus:
    def test_valid_transition(self, run_async, db_session, audit_mock, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        profile = student_profile_factory(current_status=StudentStatus.ADMITTED, version=1)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=profile)

        result = run_async(
            service.change_student_status(
                tenant_id=1,
                student_profile_id=profile.id,
                request=StudentStatusChangeSchema(
                    expected_version=1,
                    to_status=StudentStatus.ACTIVE,
                    reason="activation",
                ),
                actor_id="registrar@example.com",
            )
        )

        assert result.entity.current_status == StudentStatus.ACTIVE
        assert result.entity.version == 2
        assert result.idempotent_replay is False
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()

    def test_invalid_transition(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        profile = student_profile_factory(current_status=StudentStatus.GRADUATED, version=3)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=profile)

        with pytest.raises(DomainValidationError, match="not allowed"):
            run_async(
                service.change_student_status(
                    tenant_id=1,
                    student_profile_id=profile.id,
                    request=StudentStatusChangeSchema(
                        expected_version=3,
                        to_status=StudentStatus.ACTIVE,
                    ),
                    actor_id="registrar@example.com",
                )
            )

    def test_append_only_history_validation(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        profile = student_profile_factory(current_status=StudentStatus.ADMITTED, version=1)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=profile)

        run_async(
            service.change_student_status(
                tenant_id=1,
                student_profile_id=profile.id,
                request=StudentStatusChangeSchema(
                    expected_version=1,
                    to_status=StudentStatus.ACTIVE,
                    reason="activated",
                    metadata_json={"origin": "test"},
                ),
                actor_id="registrar@example.com",
            )
        )

        history_rows = [
            call.args[0]
            for call in db_session.add.call_args_list
            if isinstance(call.args[0], StudentStatusHistoryModel)
        ]
        assert len(history_rows) == 1
        assert history_rows[0].from_status == StudentStatus.ADMITTED
        assert history_rows[0].to_status == StudentStatus.ACTIVE

    def test_optimistic_lock_conflict(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        profile = student_profile_factory(current_status=StudentStatus.ADMITTED, version=4)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=profile)

        with pytest.raises(OptimisticLockConflictError):
            run_async(
                service.change_student_status(
                    tenant_id=1,
                    student_profile_id=profile.id,
                    request=StudentStatusChangeSchema(
                        expected_version=3,
                        to_status=StudentStatus.ACTIVE,
                    ),
                    actor_id="registrar@example.com",
                )
            )


class TestBindStudentToProgram:
    def test_success(self, run_async, db_session, audit_mock, student_profile_factory, program_factory) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProgramBindingCreateSchema(
            student_profile_id=1001,
            program_id=501,
            is_primary=True,
            binding_state=StudentProgramBindingState.ACTIVE,
        )
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=program_factory(id=501, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=None),
            ExecuteResult(scalar_one_or_none=None),
        ]

        result = run_async(service.bind_student_to_program(tenant_id=1, request=request, actor_id="actor@example.com"))

        assert result.entity.student_profile_id == 1001
        assert result.entity.program_id == 501
        assert result.entity.is_primary is True
        assert result.idempotent_replay is False
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()

    def test_enforce_single_active_primary_binding(
        self,
        run_async,
        db_session,
        student_profile_factory,
        program_factory,
        binding_factory,
    ) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProgramBindingCreateSchema(
            student_profile_id=1001,
            program_id=502,
            is_primary=True,
            binding_state=StudentProgramBindingState.ACTIVE,
        )
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=program_factory(id=502, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=None),
            ExecuteResult(scalar_one_or_none=binding_factory(id=3002, student_profile_id=1001, is_primary=True)),
        ]

        with pytest.raises(DomainValidationError, match="already has an active primary"):
            run_async(service.bind_student_to_program(tenant_id=1, request=request, actor_id="actor@example.com"))

    def test_program_not_in_tenant(self, run_async, db_session, student_profile_factory) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProgramBindingCreateSchema(
            student_profile_id=1001,
            program_id=9001,
            is_primary=True,
            binding_state=StudentProgramBindingState.ACTIVE,
        )
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=None),
        ]

        with pytest.raises(DomainValidationError, match="Program not found"):
            run_async(service.bind_student_to_program(tenant_id=1, request=request, actor_id="actor@example.com"))

    def test_duplicate_binding_returns_replay(self, run_async, db_session, student_profile_factory, program_factory, binding_factory) -> None:
        service = StudentLifecycleService(db_session)
        request = StudentProgramBindingCreateSchema(
            student_profile_id=1001,
            program_id=501,
            is_primary=False,
            binding_state=StudentProgramBindingState.ACTIVE,
        )
        db_session.execute.side_effect = [
            ExecuteResult(scalar_one_or_none=student_profile_factory(id=1001, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=program_factory(id=501, tenant_id=1)),
            ExecuteResult(scalar_one_or_none=binding_factory(student_profile_id=1001, program_id=501)),
        ]

        result = run_async(service.bind_student_to_program(tenant_id=1, request=request, actor_id="actor@example.com"))
        assert result.idempotent_replay is True
        assert result.entity.student_profile_id == 1001


class TestGetActivePrimaryProgram:
    def test_success(self, run_async, db_session, binding_factory) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(
            scalars=[binding_factory(id=3001, student_profile_id=1001, is_primary=True)]
        )

        result = run_async(service.get_active_primary_program(tenant_id=1, student_profile_id=1001))

        assert result is not None
        assert result.program_id == 501

    def test_no_active_binding(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.return_value = ExecuteResult(scalars=[])

        result = run_async(service.get_active_primary_program(tenant_id=1, student_profile_id=1001))

        assert result is None


class TestProvisionStudentForAdmissionsCompat:
    def test_create_new_student_profile(
        self,
        run_async,
        db_session,
        monkeypatch: pytest.MonkeyPatch,
        student_profile_factory,
        binding_factory,
    ) -> None:
        service = StudentLifecycleService(db_session)
        request = AdmissionsProvisionStudentRequestSchema(
            person_id=101,
            program_id=501,
            student_number="ADM-1-1001",
            cohort_year=2026,
            metadata_json={"workflow_instance_id": 7001},
        )
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)

        create_mock = AsyncMock(return_value=student_profile_factory(id=1001, person_id=101))
        primary_mock = AsyncMock(return_value=None)
        bind_mock = AsyncMock(return_value=binding_factory(student_profile_id=1001, program_id=501, is_primary=True))
        monkeypatch.setattr(service, "create_student_profile", create_mock)
        monkeypatch.setattr(service, "get_active_primary_program", primary_mock)
        monkeypatch.setattr(service, "bind_student_to_program", bind_mock)

        result = run_async(service.provision_student_for_admissions_compat(tenant_id=1, request=request, actor_id="workflow@system"))

        assert result.student_profile.person_id == 101
        assert result.active_primary_program.program_id == 501
        create_mock.assert_awaited_once()
        bind_mock.assert_awaited_once()

    def test_reuse_existing_profile(
        self,
        run_async,
        db_session,
        monkeypatch: pytest.MonkeyPatch,
        student_profile_factory,
        binding_factory,
    ) -> None:
        service = StudentLifecycleService(db_session)
        request = AdmissionsProvisionStudentRequestSchema(
            person_id=101,
            program_id=501,
            student_number="ADM-1-1001",
            cohort_year=2026,
        )
        db_session.execute.return_value = ExecuteResult(
            scalar_one_or_none=student_profile_factory(id=1001, person_id=101)
        )

        create_mock = AsyncMock()
        primary_mock = AsyncMock(return_value=binding_factory(student_profile_id=1001, program_id=501, is_primary=True))
        bind_mock = AsyncMock()
        monkeypatch.setattr(service, "create_student_profile", create_mock)
        monkeypatch.setattr(service, "get_active_primary_program", primary_mock)
        monkeypatch.setattr(service, "bind_student_to_program", bind_mock)

        result = run_async(service.provision_student_for_admissions_compat(tenant_id=1, request=request, actor_id="workflow@system"))

        assert result.student_profile.id == 1001
        assert result.active_primary_program.program_id == 501
        create_mock.assert_not_awaited()
        bind_mock.assert_not_awaited()

    def test_idempotent_retry(
        self,
        run_async,
        db_session,
        monkeypatch: pytest.MonkeyPatch,
        student_profile_factory,
        binding_factory,
    ) -> None:
        service = StudentLifecycleService(db_session)
        request = AdmissionsProvisionStudentRequestSchema(
            person_id=101,
            program_id=501,
            student_number="ADM-1-1001",
            cohort_year=2026,
        )
        existing_profile = student_profile_factory(id=1001, person_id=101)
        existing_primary = binding_factory(student_profile_id=1001, program_id=501, is_primary=True)
        db_session.execute.return_value = ExecuteResult(scalar_one_or_none=existing_profile)

        create_mock = AsyncMock()
        primary_mock = AsyncMock(return_value=existing_primary)
        bind_mock = AsyncMock()
        monkeypatch.setattr(service, "create_student_profile", create_mock)
        monkeypatch.setattr(service, "get_active_primary_program", primary_mock)
        monkeypatch.setattr(service, "bind_student_to_program", bind_mock)

        first = run_async(service.provision_student_for_admissions_compat(tenant_id=1, request=request, actor_id="workflow@system"))
        second = run_async(service.provision_student_for_admissions_compat(tenant_id=1, request=request, actor_id="workflow@system"))

        assert first.student_profile.id == second.student_profile.id
        assert first.active_primary_program.id == second.active_primary_program.id
        bind_mock.assert_not_awaited()


class TestProgramBindingConsistency:
    def test_duplicate_active_primary_bindings_reported(
        self,
        run_async,
        db_session,
        binding_factory,
    ) -> None:
        service = StudentLifecycleService(db_session)
        duplicate_bindings = [
            binding_factory(id=3001, student_profile_id=1001, program_id=501, is_primary=True),
            binding_factory(id=3002, student_profile_id=1001, program_id=502, is_primary=True),
        ]
        db_session.execute.side_effect = [
            ExecuteResult(scalars=[1001]),
            ExecuteResult(scalars=[]),
            ExecuteResult(scalars=duplicate_bindings),
        ]

        result = run_async(service.list_program_binding_consistency_issues(tenant_id=1))

        assert len(result) == 1
        assert result[0].student_profile_id == 1001
        assert result[0].issue_type == "duplicate_active_primary_bindings"
        assert result[0].active_binding_count == 2
        assert result[0].active_primary_count == 2
        assert result[0].program_ids == [501, 502]

    def test_active_bindings_without_primary_reported(
        self,
        run_async,
        db_session,
        binding_factory,
    ) -> None:
        service = StudentLifecycleService(db_session)
        active_bindings = [
            binding_factory(id=3003, student_profile_id=1002, program_id=601, is_primary=False),
            binding_factory(id=3004, student_profile_id=1002, program_id=602, is_primary=False),
        ]
        db_session.execute.side_effect = [
            ExecuteResult(scalars=[]),
            ExecuteResult(scalars=[1002]),
            ExecuteResult(scalars=active_bindings),
        ]

        result = run_async(service.list_program_binding_consistency_issues(tenant_id=1))

        assert len(result) == 1
        assert result[0].student_profile_id == 1002
        assert result[0].issue_type == "active_bindings_without_primary"
        assert result[0].active_binding_count == 2
        assert result[0].active_primary_count == 0
        assert result[0].program_ids == [601, 602]

    def test_no_consistency_issues_returns_empty_list(self, run_async, db_session) -> None:
        service = StudentLifecycleService(db_session)
        db_session.execute.side_effect = [
            ExecuteResult(scalars=[]),
            ExecuteResult(scalars=[]),
        ]

        result = run_async(service.list_program_binding_consistency_issues(tenant_id=1))

        assert result == []
