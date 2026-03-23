from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.main import app
from app.modules.students import service as students_service
from app.modules.students.dependencies import get_students_db
from app.modules.students.models import StudentStatus
from app.modules.students.router import _raise_students_http_error
from app.modules.rbac import service as rbac_service
from app.modules.students.schemas import (
    StudentProfileListResponseSchema,
    StudentProfileReadSchema,
    StudentProgramBindingReadSchema,
)
from tests.conftest import (
    ADMIN_HEADERS,
    _auth_headers,
    _configure_db_only_role_resolution,
    client,
)


@pytest.fixture(autouse=True)
def _enable_students_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"students.read", "students.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.students@example.com": ["student"],
        },
    )


@pytest.fixture
def override_students_db() -> MagicMock:
    session = MagicMock()
    app.dependency_overrides[get_students_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_students_db, None)


@pytest.fixture
def auth_headers_factory():
    return _auth_headers


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers(auth_headers_factory) -> dict[str, str]:
    return auth_headers_factory("student.no.students@example.com", ["student"])


@pytest.fixture
def tenant_factory():
    def _factory(tenant_id: int = 1, headers: dict[str, str] | None = None) -> dict[str, str]:
        base = dict(headers or ADMIN_HEADERS)
        base["X-Tenant-ID"] = str(tenant_id)
        return base

    return _factory


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr(students_service, "log_admin_action", mock)
    return mock


def _profile_schema(*, student_id: int, tenant_id: int = 1, status: StudentStatus = StudentStatus.ADMITTED) -> StudentProfileReadSchema:
    now = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
    return StudentProfileReadSchema(
        id=student_id,
        tenant_id=tenant_id,
        person_id=101,
        student_number=f"ADM-{tenant_id}-{student_id}",
        cohort_year=2026,
        academic_level=None,
        current_status=status,
        admission_source="admissions_workflow",
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
    )


def _binding_schema(*, binding_id: int = 3001, student_id: int = 1001, program_id: int = 501) -> StudentProgramBindingReadSchema:
    now = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
    return StudentProgramBindingReadSchema(
        id=binding_id,
        tenant_id=1,
        student_profile_id=student_id,
        program_id=program_id,
        is_primary=True,
        binding_state="active",
        started_at=now,
        ended_at=None,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# 1) POST /api/admin/students
# ---------------------------------------------------------------------------

def test_post_students_success(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
    audit_mock: MagicMock,
) -> None:
    async def fake_create_student_profile(self, tenant_id: int, request, created_by: str):
        assert tenant_id == 1
        assert created_by == "owner@example.com"
        assert request.person_id == 101
        # tenant_id from payload must never be used by router
        assert request.metadata_json.get("tenant_id") == 999
        return _profile_schema(student_id=1001, tenant_id=tenant_id)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "create_student_profile",
        fake_create_student_profile,
    )

    response = client.post(
        "/api/admin/students",
        headers=admin_headers,
        json={
            "person_id": 101,
            "student_number": "ADM-1-1001",
            "cohort_year": 2026,
            "metadata_json": {"tenant_id": 999},
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["id"] == 1001
    # Router should not write audit directly.
    assert audit_mock.call_count == 0


def test_post_students_invalid_payload_returns_400(
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/admin/students",
        headers=admin_headers,
        json={"student_number": "ADM-1-1001", "cohort_year": 2026},
    )

    assert response.status_code == 400, response.text


def test_post_students_missing_permission_returns_403(
    student_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/admin/students",
        headers=student_headers,
        json={
            "person_id": 101,
            "student_number": "ADM-1-1001",
            "cohort_year": 2026,
        },
    )

    assert response.status_code == 403, response.text


def test_post_students_person_not_found_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_student_profile(self, tenant_id: int, request, created_by: str):
        raise TenantResourceNotFoundError(f"Person {request.person_id} not found or does not belong to tenant {tenant_id}")

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "create_student_profile",
        fake_create_student_profile,
    )

    response = client.post(
        "/api/admin/students",
        headers=admin_headers,
        json={"person_id": 999, "student_number": "ADM-1-1999", "cohort_year": 2026},
    )

    assert response.status_code == 404, response.text


def test_post_students_duplicate_student_returns_409(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_student_profile(self, tenant_id: int, request, created_by: str):
        raise IntegrityError("duplicate key value violates unique constraint", None, None)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "create_student_profile",
        fake_create_student_profile,
    )

    response = client.post(
        "/api/admin/students",
        headers=admin_headers,
        json={"person_id": 101, "student_number": "ADM-1-1001", "cohort_year": 2026},
    )

    assert response.status_code == 409, response.text


# ---------------------------------------------------------------------------
# 2) GET /api/admin/students/{student_id}
# ---------------------------------------------------------------------------

def test_get_student_success(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_student_profile(self, tenant_id: int, student_profile_id: int):
        assert tenant_id == 1
        assert student_profile_id == 1001
        return _profile_schema(student_id=student_profile_id, tenant_id=tenant_id)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "get_student_profile",
        fake_get_student_profile,
    )

    response = client.get("/api/admin/students/1001", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["id"] == 1001


def test_get_student_not_found_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_student_profile(self, tenant_id: int, student_profile_id: int):
        raise TenantResourceNotFoundError("student not found")

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "get_student_profile",
        fake_get_student_profile,
    )

    response = client.get("/api/admin/students/9999", headers=admin_headers)

    assert response.status_code == 404, response.text


def test_get_student_cross_tenant_isolation_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_student_profile(self, tenant_id: int, student_profile_id: int):
        raise TenantResourceNotFoundError(
            f"Student profile {student_profile_id} not found or does not belong to tenant {tenant_id}"
        )

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "get_student_profile",
        fake_get_student_profile,
    )

    response = client.get("/api/admin/students/1001", headers=admin_headers)

    assert response.status_code == 404, response.text


def test_get_student_missing_permission_returns_403(student_headers: dict[str, str]) -> None:
    response = client.get("/api/admin/students/1001", headers=student_headers)

    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# 3) GET /api/admin/students
# ---------------------------------------------------------------------------

def test_list_students_success(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_student_profiles(self, tenant_id: int, *, page: int, page_size: int, status=None, person_id=None):
        assert tenant_id == 1
        return StudentProfileListResponseSchema(
            total=1,
            page=page,
            page_size=page_size,
            items=[_profile_schema(student_id=1001, tenant_id=tenant_id)],
        )

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "list_student_profiles",
        fake_list_student_profiles,
    )

    response = client.get("/api/admin/students?page=1&page_size=20", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == 1001


def test_list_students_pagination_works(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_student_profiles(self, tenant_id: int, *, page: int, page_size: int, status=None, person_id=None):
        assert page == 2
        assert page_size == 5
        return StudentProfileListResponseSchema(total=7, page=page, page_size=page_size, items=[])

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "list_student_profiles",
        fake_list_student_profiles,
    )

    response = client.get("/api/admin/students?page=2&page_size=5", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 5


def test_list_students_status_filter_works(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_student_profiles(self, tenant_id: int, *, page: int, page_size: int, status=None, person_id=None):
        assert status == StudentStatus.ACTIVE
        return StudentProfileListResponseSchema(total=0, page=page, page_size=page_size, items=[])

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "list_student_profiles",
        fake_list_student_profiles,
    )

    response = client.get("/api/admin/students?status=active", headers=admin_headers)

    assert response.status_code == 200, response.text


def test_list_students_tenant_isolation_enforced(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    tenant_factory,
) -> None:
    headers = tenant_factory(tenant_id=1, headers=ADMIN_HEADERS)

    async def fake_list_student_profiles(self, tenant_id: int, *, page: int, page_size: int, status=None, person_id=None):
        # tenant_id must come from trusted context only
        assert tenant_id == 1
        return StudentProfileListResponseSchema(total=0, page=page, page_size=page_size, items=[])

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "list_student_profiles",
        fake_list_student_profiles,
    )

    response = client.get("/api/admin/students", headers=headers)

    assert response.status_code == 200, response.text


def test_list_students_missing_permission_returns_403(student_headers: dict[str, str]) -> None:
    response = client.get("/api/admin/students", headers=student_headers)

    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# 4) PATCH /api/admin/students/{student_id}/status
# ---------------------------------------------------------------------------

def test_patch_status_valid_transition_returns_200(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_change_student_status(self, tenant_id: int, student_profile_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert student_profile_id == 1001
        assert request.to_status == StudentStatus.ACTIVE
        return _profile_schema(student_id=student_profile_id, tenant_id=tenant_id, status=StudentStatus.ACTIVE)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "change_student_status",
        fake_change_student_status,
    )

    response = client.patch(
        "/api/admin/students/1001/status",
        headers=admin_headers,
        json={"expected_version": 1, "to_status": "active", "reason": "activated"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["current_status"] == "active"


def test_patch_status_invalid_transition_returns_400(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_change_student_status(self, tenant_id: int, student_profile_id: int, request, actor_id: str):
        raise DomainValidationError("status transition is not allowed")

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "change_student_status",
        fake_change_student_status,
    )

    response = client.patch(
        "/api/admin/students/1001/status",
        headers=admin_headers,
        json={"expected_version": 1, "to_status": "withdrawn"},
    )

    assert response.status_code == 400, response.text


def test_patch_status_optimistic_lock_conflict_returns_409(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_change_student_status(self, tenant_id: int, student_profile_id: int, request, actor_id: str):
        raise OptimisticLockConflictError("Version mismatch")

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "change_student_status",
        fake_change_student_status,
    )

    response = client.patch(
        "/api/admin/students/1001/status",
        headers=admin_headers,
        json={"expected_version": 1, "to_status": "active"},
    )

    assert response.status_code == 409, response.text


def test_patch_status_student_not_found_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_change_student_status(self, tenant_id: int, student_profile_id: int, request, actor_id: str):
        raise TenantResourceNotFoundError("student not found")

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "change_student_status",
        fake_change_student_status,
    )

    response = client.patch(
        "/api/admin/students/9999/status",
        headers=admin_headers,
        json={"expected_version": 1, "to_status": "active"},
    )

    assert response.status_code == 404, response.text


def test_patch_status_rbac_denied_returns_403(student_headers: dict[str, str]) -> None:
    response = client.patch(
        "/api/admin/students/1001/status",
        headers=student_headers,
        json={"expected_version": 1, "to_status": "active"},
    )

    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# 5) POST /api/admin/students/{student_id}/program-bindings
# ---------------------------------------------------------------------------

def test_post_program_bindings_success_and_path_id_overrides_body(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_bind_student_to_program(self, tenant_id: int, request, actor_id: str):
        assert tenant_id == 1
        # Router must force student_profile_id from path, not body.
        assert request.student_profile_id == 1001
        return _binding_schema(student_id=1001, program_id=request.program_id)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "bind_student_to_program",
        fake_bind_student_to_program,
    )

    response = client.post(
        "/api/admin/students/1001/program-bindings",
        headers=admin_headers,
        json={
            "student_profile_id": 9999,
            "program_id": 501,
            "is_primary": True,
            "binding_state": "active",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["student_profile_id"] == 1001


def test_post_program_bindings_duplicate_primary_returns_409(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_bind_student_to_program(self, tenant_id: int, request, actor_id: str):
        raise IntegrityError("duplicate primary binding", None, None)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "bind_student_to_program",
        fake_bind_student_to_program,
    )

    response = client.post(
        "/api/admin/students/1001/program-bindings",
        headers=admin_headers,
        json={
            "student_profile_id": 555,
            "program_id": 501,
            "is_primary": True,
            "binding_state": "active",
        },
    )

    assert response.status_code == 409, response.text


def test_post_program_bindings_program_not_in_tenant_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_bind_student_to_program(self, tenant_id: int, request, actor_id: str):
        raise TenantResourceNotFoundError("Program 999 not found or does not belong to tenant 1")

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "bind_student_to_program",
        fake_bind_student_to_program,
    )

    response = client.post(
        "/api/admin/students/1001/program-bindings",
        headers=admin_headers,
        json={
            "student_profile_id": 555,
            "program_id": 999,
            "is_primary": True,
            "binding_state": "active",
        },
    )

    assert response.status_code == 404, response.text


def test_post_program_bindings_invalid_payload_returns_400(
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/admin/students/1001/program-bindings",
        headers=admin_headers,
        json={"is_primary": True, "binding_state": "active"},
    )

    assert response.status_code == 400, response.text


def test_post_program_bindings_rbac_denied_returns_403(student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/admin/students/1001/program-bindings",
        headers=student_headers,
        json={"program_id": 501, "is_primary": True, "binding_state": "active"},
    )

    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# 6) GET /api/admin/students/{student_id}/program
# ---------------------------------------------------------------------------

def test_get_active_program_success(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_active_primary_program(self, tenant_id: int, student_profile_id: int):
        assert tenant_id == 1
        assert student_profile_id == 1001
        return _binding_schema(student_id=1001, program_id=501)

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "get_active_primary_program",
        fake_get_active_primary_program,
    )

    response = client.get("/api/admin/students/1001/program", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["program_id"] == 501


def test_get_active_program_no_binding_returns_null(
    monkeypatch: pytest.MonkeyPatch,
    override_students_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_active_primary_program(self, tenant_id: int, student_profile_id: int):
        return None

    monkeypatch.setattr(
        students_service.StudentLifecycleService,
        "get_active_primary_program",
        fake_get_active_primary_program,
    )

    response = client.get("/api/admin/students/1001/program", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json() is None


def test_get_active_program_rbac_denied_returns_403(student_headers: dict[str, str]) -> None:
    response = client.get("/api/admin/students/1001/program", headers=student_headers)

    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# Additional router-level validations
# ---------------------------------------------------------------------------

def test_students_db_dependency_fail_closed_returns_503(admin_headers: dict[str, str]) -> None:
    sentinel = object()
    original_students = getattr(app.state, "students_session_factory", sentinel)
    original_profiles = getattr(app.state, "profiles_session_factory", sentinel)

    app.state.students_session_factory = None
    app.state.profiles_session_factory = None

    try:
        response = client.get("/api/admin/students", headers=admin_headers)
        assert response.status_code == 503, response.text
    finally:
        if original_students is sentinel:
            delattr(app.state, "students_session_factory")
        else:
            app.state.students_session_factory = original_students

        if original_profiles is sentinel:
            delattr(app.state, "profiles_session_factory")
        else:
            app.state.profiles_session_factory = original_profiles


# ---------------------------------------------------------------------------
# Error-mapping helper validation
# ---------------------------------------------------------------------------

def test_students_router_error_mapping_helper() -> None:
    assert _raise_students_http_error(PermissionError("forbidden")).status_code == 403
    assert _raise_students_http_error(TenantResourceNotFoundError("missing")).status_code == 404
    assert _raise_students_http_error(DomainValidationError("invalid")).status_code == 400
    assert _raise_students_http_error(OptimisticLockConflictError("Version mismatch")).status_code == 409
    assert _raise_students_http_error(IntegrityError("conflict", None, None)).status_code == 409
