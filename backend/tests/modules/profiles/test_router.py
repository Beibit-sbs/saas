from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.main import app
from app.modules.profiles import service as profiles_service
from app.modules.profiles.dependencies import get_profiles_db
from app.modules.profiles.router import _raise_profile_http_error
from app.modules.profiles.schemas import (
    DepartmentReadSchema,
    FacultyReadSchema,
    PersonListResponseSchema,
    PersonReadSchema,
    ProgramReadSchema,
    StudentReadSchema,
)
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


@pytest.fixture
def override_profiles_db() -> Generator[MagicMock, None, None]:
    session = MagicMock()
    app.dependency_overrides[get_profiles_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_profiles_db, None)


def test_create_person_endpoint_dispatches_trusted_tenant(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_create_person(self, tenant_id: int, request, created_by: str) -> PersonReadSchema:
        assert tenant_id == 1
        assert created_by == "owner@example.com"
        assert request.email == "profiles.person@example.edu"
        return PersonReadSchema(
            id=101,
            tenant_id=tenant_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            external_person_key=request.external_person_key,
            status=request.status,
            metadata_json=request.metadata_json,
            version=1,
            created_by=created_by,
            created_at="2026-03-22T12:00:00Z",
            updated_at="2026-03-22T12:00:00Z",
        )

    monkeypatch.setattr(profiles_service.PersonService, "create_person", fake_create_person)

    response = client.post(
        "/api/admin/profiles/people",
        headers=ADMIN_HEADERS,
        json={
            "email": "profiles.person@example.edu",
            "first_name": "Profile",
            "last_name": "Person",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["tenant_id"] == 1


def test_list_people_endpoint_is_rbac_protected(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_list_persons(self, tenant_id: int, **kwargs) -> PersonListResponseSchema:
        return PersonListResponseSchema(total=0, page=1, page_size=20, items=[])

    monkeypatch.setattr(profiles_service.PersonService, "list_persons", fake_list_persons)

    auditor_headers = _auth_headers("auditor.example", ["auditor"])
    student_headers = _auth_headers("student.example", ["student"])

    allowed = client.get("/api/admin/profiles/people", headers=auditor_headers)
    denied = client.get("/api/admin/profiles/people", headers=student_headers)

    assert allowed.status_code == 200, allowed.text
    assert denied.status_code == 403, denied.text


def test_get_person_maps_tenant_scoped_not_found_to_404(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_get_person(self, tenant_id: int, person_id: int):
        raise TenantResourceNotFoundError(f"Person {person_id} not found or does not belong to tenant {tenant_id}")

    monkeypatch.setattr(profiles_service.PersonService, "get_person", fake_get_person)

    response = client.get("/api/admin/profiles/people/999", headers=ADMIN_HEADERS)

    assert response.status_code == 404, response.text


def test_patch_person_version_conflict_maps_to_409(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_update_person(self, tenant_id: int, person_id: int, request, updated_by: str):
        raise OptimisticLockConflictError("Version mismatch: expected 2, but current version is 3")

    monkeypatch.setattr(profiles_service.PersonService, "update_person", fake_update_person)

    response = client.patch(
        "/api/admin/profiles/people/101",
        headers=ADMIN_HEADERS,
        json={"version": 2, "first_name": "Updated"},
    )

    assert response.status_code == 409, response.text


def test_create_program_invalid_payload_maps_to_400(override_profiles_db: MagicMock) -> None:
    response = client.post(
        "/api/admin/profiles/programs",
        headers=ADMIN_HEADERS,
        json={"title": "Incomplete"},
    )

    assert response.status_code == 400, response.text


def test_create_student_maps_tenant_not_found_to_404(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_create_student(self, tenant_id: int, request, created_by: str):
        raise TenantResourceNotFoundError(f"Program {request.program_id} not found or does not belong to tenant {tenant_id}")

    monkeypatch.setattr(profiles_service.StudentService, "create_student", fake_create_student)

    response = client.post(
        "/api/admin/profiles/students",
        headers=ADMIN_HEADERS,
        json={"person_id": 101, "program_id": 301, "student_number": "S-100", "cohort_year": 2026},
    )

    assert response.status_code == 404, response.text


def test_create_faculty_endpoint_uses_profiles_write_permission(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_create_faculty(self, tenant_id: int, request, created_by: str) -> FacultyReadSchema:
        return FacultyReadSchema(
            id=501,
            tenant_id=tenant_id,
            person_id=request.person_id,
            department_id=request.department_id,
            faculty_number=request.faculty_number,
            academic_title=request.academic_title,
            status=request.status,
            metadata_json=request.metadata_json,
            version=1,
            created_by=created_by,
            created_at="2026-03-22T12:00:00Z",
            updated_at="2026-03-22T12:00:00Z",
        )

    monkeypatch.setattr(profiles_service.FacultyService, "create_faculty", fake_create_faculty)

    response = client.post(
        "/api/admin/profiles/faculty",
        headers=ADMIN_HEADERS,
        json={"person_id": 101, "department_id": 201, "faculty_number": "F-100"},
    )

    assert response.status_code == 201, response.text


def test_list_departments_endpoint_uses_profiles_read_permission(monkeypatch: pytest.MonkeyPatch, override_profiles_db: MagicMock) -> None:
    async def fake_list_departments(self, tenant_id: int, page: int = 1, page_size: int = 50, unit_type: str | None = None):
        return {
            "total": 1,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": 201,
                    "tenant_id": tenant_id,
                    "code": "ENG",
                    "name": "Engineering",
                    "unit_type": "department",
                    "parent_department_id": None,
                    "head_person_id": None,
                    "email": None,
                    "phone": None,
                    "location": None,
                    "status": "active",
                    "metadata_json": {},
                    "version": 1,
                    "created_by": "owner@example.com",
                    "created_at": "2026-03-22T12:00:00Z",
                    "updated_at": "2026-03-22T12:00:00Z",
                }
            ],
        }

    monkeypatch.setattr(profiles_service.DepartmentService, "list_departments", fake_list_departments)

    student_headers = _auth_headers("student.example", ["student"])
    allowed = client.get("/api/admin/profiles/departments", headers=ADMIN_HEADERS)
    denied = client.get("/api/admin/profiles/departments", headers=student_headers)

    assert allowed.status_code == 200, allowed.text
    assert denied.status_code == 403, denied.text


def test_profiles_db_dependency_fails_closed_with_503() -> None:
    original = getattr(app.state, "profiles_session_factory", None)
    app.state.profiles_session_factory = None
    try:
        response = client.get("/api/admin/profiles/people", headers=ADMIN_HEADERS)
        assert response.status_code == 503, response.text
    finally:
        app.state.profiles_session_factory = original


def test_router_error_mapping_helper_behaves_consistently() -> None:
    assert _raise_profile_http_error(PermissionError("forbidden")).status_code == 403
    assert _raise_profile_http_error(TenantResourceNotFoundError("resource missing")).status_code == 404
    assert _raise_profile_http_error(OptimisticLockConflictError("Version mismatch")).status_code == 409
    assert _raise_profile_http_error(ValueError("Invalid profile payload")).status_code == 400