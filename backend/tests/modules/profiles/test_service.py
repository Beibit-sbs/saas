from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    OptimisticLockConflictError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.profiles.schemas import (
    DepartmentCreateSchema,
    FacultyCreateSchema,
    PersonCreateSchema,
    PersonUpdateSchema,
    ProgramCreateSchema,
    StudentCreateSchema,
)
from app.modules.profiles.service import (
    DepartmentService,
    FacultyService,
    PersonService,
    ProgramService,
    StudentService,
)


def make_execute_result(*, scalar_one_or_none=None, scalar_one=None, scalars_all=None):
    result = MagicMock(name="execute_result")
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalar_one is not None:
        result.scalar_one.return_value = scalar_one
    if scalars_all is not None:
        scalars = MagicMock(name="scalars_result")
        scalars.all.return_value = scalars_all
        result.scalars.return_value = scalars
    return result


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.profiles.service.log_admin_action", mock)
    return mock


class TestPersonService:
    def test_create_person_success_writes_audit(self, db_session: MagicMock, audit_mock: MagicMock) -> None:
        service = PersonService(db_session)
        request = PersonCreateSchema(
            email="student@example.edu",
            first_name="Ada",
            last_name="Lovelace",
            status="active",
        )

        result = _run(service.create_person(tenant_id=1, request=request, created_by="owner@example.com"))

        assert result.tenant_id == 1
        assert result.email == "student@example.edu"
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        audit_mock.assert_called_once()
        assert audit_mock.call_args.kwargs["action"] == "profiles.person.created"

    def test_create_person_rejects_missing_tenant(self, db_session: MagicMock) -> None:
        service = PersonService(db_session)
        request = PersonCreateSchema(
            email="student@example.edu",
            first_name="Ada",
            last_name="Lovelace",
        )

        with pytest.raises(TenantRequiredError):
            _run(service.create_person(tenant_id=None, request=request, created_by="owner@example.com"))

    def test_get_person_cross_tenant_is_not_found(self, db_session: MagicMock) -> None:
        service = PersonService(db_session)
        db_session.execute.return_value = make_execute_result(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.get_person(tenant_id=1, person_id=999))

    def test_update_person_version_mismatch_conflict(self, db_session: MagicMock, person_factory) -> None:
        service = PersonService(db_session)
        db_session.execute.return_value = make_execute_result(scalar_one_or_none=person_factory(version=3))

        with pytest.raises(OptimisticLockConflictError):
            _run(
                service.update_person(
                    tenant_id=1,
                    person_id=101,
                    request=PersonUpdateSchema(version=2, first_name="Grace"),
                    updated_by="owner@example.com",
                )
            )

    def test_update_person_success_writes_audit(self, db_session: MagicMock, audit_mock: MagicMock, person_factory) -> None:
        service = PersonService(db_session)
        person = person_factory(version=1)
        db_session.execute.return_value = make_execute_result(scalar_one_or_none=person)

        result = _run(
            service.update_person(
                tenant_id=1,
                person_id=person.id,
                request=PersonUpdateSchema(version=1, first_name="Grace"),
                updated_by="owner@example.com",
            )
        )

        assert result.first_name == "Grace"
        assert result.version == 2
        db_session.commit.assert_called_once()
        assert audit_mock.call_args.kwargs["action"] == "profiles.person.updated"

    def test_list_persons_returns_paginated_items(self, db_session: MagicMock, person_factory) -> None:
        service = PersonService(db_session)
        db_session.execute.side_effect = [
            make_execute_result(scalar_one=2),
            make_execute_result(scalars_all=[person_factory(id=101), person_factory(id=102)]),
        ]

        result = _run(service.list_persons(tenant_id=1, page=1, page_size=20))

        assert result.total == 2
        assert len(result.items) == 2


class TestDepartmentService:
    def test_create_department_success_writes_audit(self, db_session: MagicMock, audit_mock: MagicMock) -> None:
        service = DepartmentService(db_session)
        request = DepartmentCreateSchema(code="ENG", name="Engineering")

        result = _run(service.create_department(tenant_id=1, request=request, created_by="owner@example.com"))

        assert result.code == "ENG"
        db_session.commit.assert_called_once()
        assert audit_mock.call_args.kwargs["action"] == "profiles.department.created"

    def test_create_department_parent_must_be_in_same_tenant(self, db_session: MagicMock, department_factory) -> None:
        service = DepartmentService(db_session)
        request = DepartmentCreateSchema(code="MATH", name="Mathematics", parent_department_id=777)
        db_session.execute.return_value = make_execute_result(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.create_department(tenant_id=1, request=request, created_by="owner@example.com"))

    def test_list_departments_returns_paginated_items(self, db_session: MagicMock, department_factory) -> None:
        service = DepartmentService(db_session)
        db_session.execute.side_effect = [
            make_execute_result(scalar_one=2),
            make_execute_result(scalars_all=[department_factory(id=201), department_factory(id=202)]),
        ]

        result = _run(service.list_departments(tenant_id=1, page=1, page_size=20))

        assert result.total == 2
        assert len(result.items) == 2


class TestProgramService:
    def test_create_program_success_writes_audit(self, db_session: MagicMock, audit_mock: MagicMock, department_factory) -> None:
        service = ProgramService(db_session)
        request = ProgramCreateSchema(
            department_id=201,
            code="CS-BSC",
            title="Computer Science",
            degree_type="bachelor",
        )
        db_session.execute.return_value = make_execute_result(scalar_one_or_none=department_factory(id=201, tenant_id=1))

        result = _run(service.create_program(tenant_id=1, request=request, created_by="owner@example.com"))

        assert result.department_id == 201
        assert audit_mock.call_args.kwargs["action"] == "profiles.program.created"

    def test_create_program_department_must_belong_to_tenant(self, db_session: MagicMock) -> None:
        service = ProgramService(db_session)
        request = ProgramCreateSchema(
            department_id=999,
            code="BIO-BSC",
            title="Biology",
            degree_type="bachelor",
        )
        db_session.execute.return_value = make_execute_result(scalar_one_or_none=None)

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.create_program(tenant_id=1, request=request, created_by="owner@example.com"))


class TestStudentService:
    def test_create_student_success_writes_audit(
        self,
        db_session: MagicMock,
        audit_mock: MagicMock,
        person_factory,
        program_factory,
    ) -> None:
        service = StudentService(db_session)
        request = StudentCreateSchema(person_id=101, program_id=301, student_number="S-100", cohort_year=2026)
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            make_execute_result(scalar_one_or_none=program_factory(id=301, tenant_id=1)),
            make_execute_result(scalar_one_or_none=None),
        ]

        result = _run(service.create_student(tenant_id=1, request=request, created_by="owner@example.com"))

        assert result.person_id == 101
        assert audit_mock.call_args.kwargs["action"] == "profiles.student.created"

    def test_create_student_person_must_belong_to_tenant(self, db_session: MagicMock, program_factory) -> None:
        service = StudentService(db_session)
        request = StudentCreateSchema(person_id=101, program_id=301, student_number="S-100", cohort_year=2026)
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=None),
            make_execute_result(scalar_one_or_none=program_factory(id=301, tenant_id=1)),
            make_execute_result(scalar_one_or_none=None),
        ]

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.create_student(tenant_id=1, request=request, created_by="owner@example.com"))

    def test_create_student_program_must_belong_to_tenant(self, db_session: MagicMock, person_factory) -> None:
        service = StudentService(db_session)
        request = StudentCreateSchema(person_id=101, program_id=301, student_number="S-100", cohort_year=2026)
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            make_execute_result(scalar_one_or_none=None),
            make_execute_result(scalar_one_or_none=None),
        ]

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.create_student(tenant_id=1, request=request, created_by="owner@example.com"))

    def test_create_student_duplicate_role_rejected(
        self,
        db_session: MagicMock,
        person_factory,
        program_factory,
        student_factory,
    ) -> None:
        service = StudentService(db_session)
        request = StudentCreateSchema(person_id=101, program_id=301, student_number="S-100", cohort_year=2026)
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            make_execute_result(scalar_one_or_none=program_factory(id=301, tenant_id=1)),
            make_execute_result(scalar_one_or_none=student_factory(person_id=101, tenant_id=1)),
        ]

        with pytest.raises(ValueError, match="Student role already exists"):
            _run(service.create_student(tenant_id=1, request=request, created_by="owner@example.com"))


class TestFacultyService:
    def test_create_faculty_success_writes_audit(
        self,
        db_session: MagicMock,
        audit_mock: MagicMock,
        person_factory,
        department_factory,
    ) -> None:
        service = FacultyService(db_session)
        request = FacultyCreateSchema(person_id=101, department_id=201, faculty_number="F-100")
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            make_execute_result(scalar_one_or_none=department_factory(id=201, tenant_id=1)),
            make_execute_result(scalar_one_or_none=None),
        ]

        result = _run(service.create_faculty(tenant_id=1, request=request, created_by="owner@example.com"))

        assert result.department_id == 201
        assert audit_mock.call_args.kwargs["action"] == "profiles.faculty.created"

    def test_create_faculty_person_must_belong_to_tenant(self, db_session: MagicMock, department_factory) -> None:
        service = FacultyService(db_session)
        request = FacultyCreateSchema(person_id=101, department_id=201, faculty_number="F-100")
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=None),
            make_execute_result(scalar_one_or_none=department_factory(id=201, tenant_id=1)),
            make_execute_result(scalar_one_or_none=None),
        ]

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.create_faculty(tenant_id=1, request=request, created_by="owner@example.com"))

    def test_create_faculty_department_must_belong_to_tenant(self, db_session: MagicMock, person_factory) -> None:
        service = FacultyService(db_session)
        request = FacultyCreateSchema(person_id=101, department_id=201, faculty_number="F-100")
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            make_execute_result(scalar_one_or_none=None),
            make_execute_result(scalar_one_or_none=None),
        ]

        with pytest.raises(TenantResourceNotFoundError):
            _run(service.create_faculty(tenant_id=1, request=request, created_by="owner@example.com"))

    def test_create_faculty_duplicate_role_rejected(
        self,
        db_session: MagicMock,
        person_factory,
        department_factory,
        faculty_factory,
    ) -> None:
        service = FacultyService(db_session)
        request = FacultyCreateSchema(person_id=101, department_id=201, faculty_number="F-100")
        db_session.execute.side_effect = [
            make_execute_result(scalar_one_or_none=person_factory(id=101, tenant_id=1)),
            make_execute_result(scalar_one_or_none=department_factory(id=201, tenant_id=1)),
            make_execute_result(scalar_one_or_none=faculty_factory(person_id=101, tenant_id=1)),
        ]

        with pytest.raises(ValueError, match="Faculty role already exists"):
            _run(service.create_faculty(tenant_id=1, request=request, created_by="owner@example.com"))
