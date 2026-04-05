"""
Profiles Integration Validation Suite
====================================
Validation scope
----------------
Layer tested:   FastAPI lifespan wiring + router + dependency injection + RBAC
Layer mocked:   SQLAlchemy Session (MagicMock), service methods (monkeypatch)
Not tested:     real database I/O, Alembic migrations, psycopg driver

Recommended integration test files
----------------------------------
- tests/modules/profiles/test_router.py
- tests/modules/profiles/test_integration.py

Required fixtures
-----------------
- override_profiles_db: overrides get_profiles_db with a MagicMock Session
- reset_shared_state: inherited autouse fixture from tests/conftest.py
- auth helpers from tests/conftest.py for admin and denied-role requests

Covered cases
-------------
1. Startup with DATABASE_URL wires app.state.profiles_session_factory.
2. Startup without DATABASE_URL keeps the factory unset and preserves fail-closed behaviour.
3. Every Profiles endpoint returns HTTP 503 when the session factory is unavailable.
4. Happy-path smoke for People, Departments, Programs, Students, and Faculty when DB is overridden.
5. RBAC denied path and tenant-safe not-found / forbidden mappings.
6. Real dependency lifecycle closes the per-request Session on success and on error.

Validation commands
-------------------
- JWT_SECRET='<set-test-jwt-secret>' docker compose --env-file ../../infra/.env exec -T backend pytest tests/modules/profiles/test_integration.py -q
- JWT_SECRET='<set-test-jwt-secret>' docker compose --env-file ../../infra/.env exec -T backend pytest tests/modules/profiles -q
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.main import app
from app.modules.profiles import service as profiles_service
from app.modules.profiles.dependencies import get_profiles_db
from app.modules.profiles.schemas import (
    DegreeType,
    DepartmentReadSchema,
    FacultyReadSchema,
    PersonListResponseSchema,
    PersonReadSchema,
    ProfileStatus,
    ProgramReadSchema,
    StudentReadSchema,
)
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


_NOW = datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc)
_MISSING = object()


def _person_read(**overrides) -> PersonReadSchema:
    base = dict(
        id=101,
        tenant_id=1,
        email="profiles.person@example.edu",
        first_name="Profile",
        last_name="Person",
        phone=None,
        external_person_key=None,
        status=ProfileStatus.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return PersonReadSchema(**base)


def _department_read(**overrides) -> DepartmentReadSchema:
    base = dict(
        id=201,
        tenant_id=1,
        code="CS",
        name="Computer Science",
        parent_department_id=None,
        status=ProfileStatus.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return DepartmentReadSchema(**base)


def _program_read(**overrides) -> ProgramReadSchema:
    base = dict(
        id=301,
        tenant_id=1,
        department_id=201,
        code="BSCS",
        title="BSc Computer Science",
        degree_type=DegreeType.BACHELOR,
        status=ProfileStatus.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return ProgramReadSchema(**base)


def _student_read(**overrides) -> StudentReadSchema:
    base = dict(
        id=401,
        tenant_id=1,
        person_id=101,
        program_id=301,
        student_number="S-100",
        cohort_year=2026,
        status=ProfileStatus.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return StudentReadSchema(**base)


def _faculty_read(**overrides) -> FacultyReadSchema:
    base = dict(
        id=501,
        tenant_id=1,
        person_id=101,
        department_id=201,
        faculty_number="F-100",
        academic_title="Professor",
        status=ProfileStatus.ACTIVE,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return FacultyReadSchema(**base)


def _preserve_state_factories() -> tuple[object, object, object, object, object]:
    return (
        getattr(app.state, "admissions_session_factory", _MISSING),
        getattr(app.state, "profiles_session_factory", _MISSING),
        getattr(app.state, "students_session_factory", _MISSING),
        getattr(app.state, "grades_session_factory", _MISSING),
        getattr(app.state, "workflows_session_factory", _MISSING),
    )


def _restore_state_factories(
    original_admissions: object,
    original_profiles: object,
    original_students: object,
    original_grades: object,
    original_workflows: object,
) -> None:
    if original_admissions is _MISSING:
        try:
            del app.state.admissions_session_factory
        except (AttributeError, KeyError):
            pass
    else:
        app.state.admissions_session_factory = original_admissions

    if original_profiles is _MISSING:
        try:
            del app.state.profiles_session_factory
        except (AttributeError, KeyError):
            pass
    else:
        app.state.profiles_session_factory = original_profiles

    if original_students is _MISSING:
        try:
            del app.state.students_session_factory
        except (AttributeError, KeyError):
            pass
    else:
        app.state.students_session_factory = original_students

    if original_grades is _MISSING:
        try:
            del app.state.grades_session_factory
        except (AttributeError, KeyError):
            pass
    else:
        app.state.grades_session_factory = original_grades

    if original_workflows is _MISSING:
        try:
            del app.state.workflows_session_factory
        except (AttributeError, KeyError):
            pass
    else:
        app.state.workflows_session_factory = original_workflows


@pytest.fixture()
def override_profiles_db() -> Generator[MagicMock, None, None]:
    session = MagicMock(name="profiles_db_session")
    app.dependency_overrides[get_profiles_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_profiles_db, None)


class TestStartupWithDatabaseUrl:
    def test_profiles_session_factory_is_set_on_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql://db/testdb")
        original_admissions, original_profiles, original_students, original_grades, original_workflows = _preserve_state_factories()
        fake_profiles_factory = MagicMock(name="profiles_session_factory")

        try:
            with (
                patch("app.main.build_engine", return_value=MagicMock(name="engine")) as mock_build,
                patch(
                    "app.main.make_session_factory",
                    side_effect=[
                        MagicMock(name="admissions_factory"),
                        fake_profiles_factory,
                        MagicMock(name="students_session_factory"),
                        MagicMock(name="grades_session_factory"),
                        MagicMock(name="workflows_session_factory"),
                    ],
                ) as mock_factory,
            ):
                with TestClient(app, raise_server_exceptions=False):
                    assert app.state.profiles_session_factory is fake_profiles_factory
                    mock_build.assert_called_once()
                    assert mock_factory.call_count == 5
        finally:
            _restore_state_factories(original_admissions, original_profiles, original_students, original_grades, original_workflows)


class TestStartupWithoutDatabaseUrl:
    def test_profiles_app_starts_without_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        original_admissions, original_profiles, original_students, original_grades, original_workflows = _preserve_state_factories()

        try:
            with patch("app.main.build_engine", side_effect=RuntimeError("DATABASE_URL is not set")):
                with TestClient(app, raise_server_exceptions=False) as test_client:
                    response = test_client.get("/api/admin/profiles/people", headers=ADMIN_HEADERS)
                    assert response.status_code == 503, response.text
                    assert app.state.profiles_session_factory is None
        finally:
            _restore_state_factories(original_admissions, original_profiles, original_students, original_grades, original_workflows)

    def test_profiles_startup_warning_is_logged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        original_admissions, original_profiles, original_students, original_grades, original_workflows = _preserve_state_factories()

        try:
            with patch("app.main.logger") as mock_logger:
                with patch("app.main.build_engine", side_effect=RuntimeError("DATABASE_URL is not set")):
                    with TestClient(app, raise_server_exceptions=False):
                        pass
            warning_messages = [str(call) for call in mock_logger.warning.call_args_list]
            assert any("profiles database not configured" in msg for msg in warning_messages)
        finally:
            _restore_state_factories(original_admissions, original_profiles, original_students, original_grades, original_workflows)


class TestFailClosedBehavior:
    @pytest.fixture(autouse=True)
    def _clear_factory(self) -> Generator[None, None, None]:
        original = getattr(app.state, "profiles_session_factory", _MISSING)
        app.state.profiles_session_factory = None
        try:
            yield
        finally:
            if original is _MISSING:
                try:
                    del app.state.profiles_session_factory
                except AttributeError:
                    pass
            else:
                app.state.profiles_session_factory = original

    def test_create_person_returns_503(self) -> None:
        response = client.post(
            "/api/admin/profiles/people",
            headers=ADMIN_HEADERS,
            json={"email": "fail.closed@example.edu", "first_name": "Fail", "last_name": "Closed"},
        )
        assert response.status_code == 503, response.text

    def test_list_people_returns_503(self) -> None:
        response = client.get("/api/admin/profiles/people", headers=ADMIN_HEADERS)
        assert response.status_code == 503, response.text

    def test_get_person_returns_503(self) -> None:
        response = client.get("/api/admin/profiles/people/101", headers=ADMIN_HEADERS)
        assert response.status_code == 503, response.text

    def test_patch_person_returns_503(self) -> None:
        response = client.patch(
            "/api/admin/profiles/people/101",
            headers=ADMIN_HEADERS,
            json={"version": 1, "first_name": "Updated"},
        )
        assert response.status_code == 503, response.text

    def test_create_department_returns_503(self) -> None:
        response = client.post(
            "/api/admin/profiles/departments",
            headers=ADMIN_HEADERS,
            json={"code": "CS", "name": "Computer Science"},
        )
        assert response.status_code == 503, response.text

    def test_create_program_returns_503(self) -> None:
        response = client.post(
            "/api/admin/profiles/programs",
            headers=ADMIN_HEADERS,
            json={"department_id": 201, "code": "BSCS", "title": "BSc CS", "degree_type": "bachelor"},
        )
        assert response.status_code == 503, response.text

    def test_create_student_returns_503(self) -> None:
        response = client.post(
            "/api/admin/profiles/students",
            headers=ADMIN_HEADERS,
            json={"person_id": 101, "program_id": 301, "student_number": "S-100", "cohort_year": 2026},
        )
        assert response.status_code == 503, response.text

    def test_create_faculty_returns_503(self) -> None:
        response = client.post(
            "/api/admin/profiles/faculty",
            headers=ADMIN_HEADERS,
            json={"person_id": 101, "department_id": 201, "faculty_number": "F-100"},
        )
        assert response.status_code == 503, response.text


class TestHappyPathEndpoints:
    def test_create_person_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _person_read(email=request.email, first_name=request.first_name, last_name=request.last_name)

        monkeypatch.setattr(profiles_service.PersonService, "create_person", fake_create)

        response = client.post(
            "/api/admin/profiles/people",
            headers=ADMIN_HEADERS,
            json={
                "email": "happy.person@example.edu",
                "first_name": "Happy",
                "last_name": "Person",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["tenant_id"] == 1

    def test_list_people_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_list(self, tenant_id, **kwargs):
            return PersonListResponseSchema(total=1, page=1, page_size=20, items=[_person_read()])

        monkeypatch.setattr(profiles_service.PersonService, "list_persons", fake_list)

        response = client.get("/api/admin/profiles/people", headers=ADMIN_HEADERS)
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 1

    def test_get_person_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_get(self, tenant_id, person_id):
            return _person_read(id=person_id)

        monkeypatch.setattr(profiles_service.PersonService, "get_person", fake_get)

        response = client.get("/api/admin/profiles/people/101", headers=ADMIN_HEADERS)
        assert response.status_code == 200, response.text
        assert response.json()["id"] == 101

    def test_patch_person_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_update(self, tenant_id, person_id, request, updated_by):
            return _person_read(id=person_id, first_name=request.first_name or "Profile")

        monkeypatch.setattr(profiles_service.PersonService, "update_person", fake_update)

        response = client.patch(
            "/api/admin/profiles/people/101",
            headers=ADMIN_HEADERS,
            json={"version": 1, "first_name": "Updated"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["first_name"] == "Updated"

    def test_create_department_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _department_read(code=request.code, name=request.name)

        monkeypatch.setattr(profiles_service.DepartmentService, "create_department", fake_create)

        response = client.post(
            "/api/admin/profiles/departments",
            headers=ADMIN_HEADERS,
            json={"code": "CS", "name": "Computer Science"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["code"] == "CS"

    def test_create_program_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _program_read(department_id=request.department_id, code=request.code, title=request.title)

        monkeypatch.setattr(profiles_service.ProgramService, "create_program", fake_create)

        response = client.post(
            "/api/admin/profiles/programs",
            headers=ADMIN_HEADERS,
            json={"department_id": 201, "code": "BSCS", "title": "BSc CS", "degree_type": "bachelor"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["department_id"] == 201

    def test_create_student_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _student_read(person_id=request.person_id, program_id=request.program_id)

        monkeypatch.setattr(profiles_service.StudentService, "create_student", fake_create)

        response = client.post(
            "/api/admin/profiles/students",
            headers=ADMIN_HEADERS,
            json={"person_id": 101, "program_id": 301, "student_number": "S-100", "cohort_year": 2026},
        )
        assert response.status_code == 201, response.text
        assert response.json()["student_number"] == "S-100"

    def test_create_faculty_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _faculty_read(person_id=request.person_id, department_id=request.department_id)

        monkeypatch.setattr(profiles_service.FacultyService, "create_faculty", fake_create)

        response = client.post(
            "/api/admin/profiles/faculty",
            headers=ADMIN_HEADERS,
            json={"person_id": 101, "department_id": 201, "faculty_number": "F-100"},
        )
        assert response.status_code == 201, response.text
        assert response.json()["faculty_number"] == "F-100"


class TestRouterSafety:
    def test_rbac_denied_path_returns_403(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_list(self, tenant_id, **kwargs):
            return PersonListResponseSchema(total=0, page=1, page_size=20, items=[])

        monkeypatch.setattr(profiles_service.PersonService, "list_persons", fake_list)

        student_headers = _auth_headers("student.example", ["student"])
        response = client.get("/api/admin/profiles/people", headers=student_headers)
        assert response.status_code == 403, response.text

    def test_tenant_safe_not_found_maps_to_404(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_get(self, tenant_id, person_id):
            raise TenantResourceNotFoundError(
                f"Person {person_id} not found or does not belong to tenant {tenant_id}"
            )

        monkeypatch.setattr(profiles_service.PersonService, "get_person", fake_get)

        response = client.get("/api/admin/profiles/people/999", headers=ADMIN_HEADERS)
        assert response.status_code == 404, response.text

    def test_forbidden_mapping_returns_403(
        self, monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            raise PermissionError("department creation forbidden")

        monkeypatch.setattr(profiles_service.DepartmentService, "create_department", fake_create)

        response = client.post(
            "/api/admin/profiles/departments",
            headers=ADMIN_HEADERS,
            json={"code": "CS", "name": "Computer Science"},
        )
        assert response.status_code == 403, response.text


class TestDbDependencyLifecycle:
    def test_session_close_called_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        session = MagicMock(name="profiles_session_success")
        factory = MagicMock(name="profiles_factory_success", return_value=session)
        original = getattr(app.state, "profiles_session_factory", None)
        app.state.profiles_session_factory = factory

        async def fake_list(self, tenant_id, **kwargs):
            return PersonListResponseSchema(total=0, page=1, page_size=20, items=[])

        monkeypatch.setattr(profiles_service.PersonService, "list_persons", fake_list)

        try:
            response = client.get("/api/admin/profiles/people", headers=ADMIN_HEADERS)
            assert response.status_code == 200, response.text
        finally:
            app.state.profiles_session_factory = original

        session.close.assert_called_once()

    def test_session_close_called_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        session = MagicMock(name="profiles_session_error")
        factory = MagicMock(name="profiles_factory_error", return_value=session)
        original = getattr(app.state, "profiles_session_factory", None)
        app.state.profiles_session_factory = factory

        async def fake_get(self, tenant_id, person_id):
            raise TenantResourceNotFoundError(
                f"Person {person_id} not found or does not belong to tenant {tenant_id}"
            )

        monkeypatch.setattr(profiles_service.PersonService, "get_person", fake_get)

        try:
            response = client.get("/api/admin/profiles/people/101", headers=ADMIN_HEADERS)
            assert response.status_code == 404, response.text
        finally:
            app.state.profiles_session_factory = original

        session.close.assert_called_once()

    def test_fail_closed_path_does_not_open_session(self) -> None:
        original = getattr(app.state, "profiles_session_factory", None)
        app.state.profiles_session_factory = None
        try:
            response = client.get("/api/admin/profiles/people", headers=ADMIN_HEADERS)
            assert response.status_code == 503, response.text
        finally:
            app.state.profiles_session_factory = original
