from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.enrollments.dependencies import get_enrollments_db
from app.modules.enrollments.models import EnrollmentStatus, EnrollmentType
from app.modules.enrollments.schemas import AcademicTermReadSchema
from app.modules.enrollments.schemas import EnrollmentReadSchema
from app.modules.enrollments.schemas import EnrollmentConsistencyReportSchema
from app.modules.enrollments.service import EnrollmentLifecycleService
from app.modules.rbac import service as rbac_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client


# Non-permitted actor (role "student" lacks enrollments.write) — configured in the
# autouse fixture; used for authorized-denial coverage on the write routes.
DENIED_HEADERS = _auth_headers("student.no.enrollments@example.com", ["student"], tenant_id=1)


@pytest.fixture(autouse=True)
def _enable_enrollments_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"enrollments.read", "enrollments.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.enrollments@example.com": ["student"],
        },
    )


@pytest.fixture
def override_enrollments_db() -> Generator[MagicMock, None, None]:
    session = MagicMock()
    app.dependency_overrides[get_enrollments_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_enrollments_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def _enrollment_schema(
    *,
    enrollment_id: int = 4001,
    tenant_id: int = 1,
    enrollment_status: EnrollmentStatus = EnrollmentStatus.ENROLLED,
    version: int = 1,
    dropped_at: datetime | None = None,
) -> EnrollmentReadSchema:
    now = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
    return EnrollmentReadSchema(
        id=enrollment_id,
        tenant_id=tenant_id,
        student_profile_id=1001,
        course_id=701,
        term_id=1,
        section_id=None,
        enrollment_status=enrollment_status,
        enrollment_type=EnrollmentType.REGULAR,
        enrolled_at=now,
        dropped_at=dropped_at,
        grade_code=None,
        grade_points=None,
        metadata_json={},
        version=version,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=now,
        updated_at=now,
    )


def _term_schema(*, term_id: int = 1, tenant_id: int = 1) -> AcademicTermReadSchema:
    now = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
    return AcademicTermReadSchema(
        id=term_id,
        tenant_id=tenant_id,
        term_code="2026-SPRING",
        term_name="Spring 2026",
        start_date=now,
        end_date=now,
        status="active",
        metadata_json={},
        created_at=now,
        updated_at=now,
    )


def test_post_enrollment_success(
    monkeypatch: pytest.MonkeyPatch,
    override_enrollments_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_enroll_student(self, tenant_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert actor_id == "owner@example.com"
        assert request.student_profile_id == 1001
        assert request.course_id == 701
        assert request.term_id == 1
        return _enrollment_schema(tenant_id=tenant_id)

    monkeypatch.setattr(EnrollmentLifecycleService, "enroll_student", fake_enroll_student)

    response = client.post(
        "/api/admin/enrollments",
        headers=admin_headers,
        json={
            "student_profile_id": 1001,
            "course_id": 701,
            "term_id": 1,
            "section_id": 501,
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["student_profile_id"] == 1001
    assert body["course_id"] == 701
    assert body["term_id"] == 1


def test_get_enrollment_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    override_enrollments_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_consistency(self, tenant_id: int):
        assert tenant_id == 1
        return EnrollmentConsistencyReportSchema(
            enrollment_count=2,
            issue_count=3,
            issues=[
                {
                    "issue_type": "enrollment_missing_student_profile",
                    "enrollment_id": 4002,
                    "student_profile_id": 9999,
                    "course_id": 702,
                    "term_id": 2,
                }
            ],
        )

    monkeypatch.setattr(
        EnrollmentLifecycleService,
        "list_tenant_enrollment_consistency_report",
        fake_consistency,
    )

    response = client.get("/api/admin/enrollments/consistency", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["issue_count"] == 3
    assert body["issues"][0]["issue_type"] == "enrollment_missing_student_profile"


# ---------------------------------------------------------------------------
# A-056.G1.3 — HTTP-route authorized-success + denial for the write routes that the
# G1.2 gate / A-055.ENR-R1 flagged as having NO authorized-success route test
# (change_enrollment_status, drop, create_academic_term). Closes the false-green gap:
# these exercise the full router stack (parse -> permission -> service -> 2xx/response_model
# and the RBAC-denied path), not just the service in isolation.
# ---------------------------------------------------------------------------


def test_patch_status_authorized_success(
    monkeypatch: pytest.MonkeyPatch,
    override_enrollments_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_change_status(self, tenant_id: int, enrollment_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert enrollment_id == 4001
        assert actor_id == "owner@example.com"
        assert request.to_status == EnrollmentStatus.WITHDRAWN
        assert request.expected_version == 1
        return _enrollment_schema(enrollment_status=EnrollmentStatus.WITHDRAWN, version=2)

    monkeypatch.setattr(EnrollmentLifecycleService, "change_enrollment_status", fake_change_status)

    response = client.patch(
        "/api/admin/enrollments/4001/status",
        headers=admin_headers,
        json={"expected_version": 1, "to_status": "withdrawn", "reason": "student withdrawal"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["enrollment_status"] == "withdrawn"
    assert body["version"] == 2


def test_patch_status_denied_for_non_permitted(
    override_enrollments_db: MagicMock,
) -> None:
    # No service monkeypatch: permission_dependency("enrollments.write") must reject first.
    response = client.patch(
        "/api/admin/enrollments/4001/status",
        headers=DENIED_HEADERS,
        json={"expected_version": 1, "to_status": "withdrawn"},
    )
    assert response.status_code == 403, response.text


def test_post_drop_authorized_success(
    monkeypatch: pytest.MonkeyPatch,
    override_enrollments_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    now = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)

    async def fake_drop(self, tenant_id: int, enrollment_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert enrollment_id == 4001
        assert actor_id == "owner@example.com"
        assert request.expected_version == 1
        return _enrollment_schema(
            enrollment_status=EnrollmentStatus.DROPPED, version=2, dropped_at=now
        )

    monkeypatch.setattr(EnrollmentLifecycleService, "drop_enrollment", fake_drop)

    response = client.post(
        "/api/admin/enrollments/4001/drop",
        headers=admin_headers,
        json={"expected_version": 1, "reason": "dropped by advisor"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["enrollment_status"] == "dropped"
    assert body["dropped_at"] is not None


def test_post_drop_denied_for_non_permitted(
    override_enrollments_db: MagicMock,
) -> None:
    response = client.post(
        "/api/admin/enrollments/4001/drop",
        headers=DENIED_HEADERS,
        json={"expected_version": 1},
    )
    assert response.status_code == 403, response.text


def test_post_academic_term_authorized_success(
    monkeypatch: pytest.MonkeyPatch,
    override_enrollments_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_create_term(self, tenant_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert actor_id == "owner@example.com"
        assert request.term_code == "2026-SPRING"
        return _term_schema(tenant_id=tenant_id)

    monkeypatch.setattr(EnrollmentLifecycleService, "create_academic_term", fake_create_term)

    response = client.post(
        "/api/admin/academic-terms",
        headers=admin_headers,
        json={"term_code": "2026-SPRING", "term_name": "Spring 2026", "status": "active"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["term_code"] == "2026-SPRING"
    assert body["status"] == "active"


def test_post_academic_term_denied_for_non_permitted(
    override_enrollments_db: MagicMock,
) -> None:
    response = client.post(
        "/api/admin/academic-terms",
        headers=DENIED_HEADERS,
        json={"term_code": "2026-SPRING", "term_name": "Spring 2026", "status": "active"},
    )
    assert response.status_code == 403, response.text