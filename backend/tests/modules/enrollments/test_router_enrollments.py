from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.enrollments.dependencies import get_enrollments_db
from app.modules.enrollments.models import EnrollmentStatus, EnrollmentType
from app.modules.enrollments.schemas import EnrollmentReadSchema
from app.modules.enrollments.service import EnrollmentLifecycleService
from app.modules.rbac import service as rbac_service
from tests.conftest import ADMIN_HEADERS, _configure_db_only_role_resolution, client


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


def _enrollment_schema(*, enrollment_id: int = 4001, tenant_id: int = 1) -> EnrollmentReadSchema:
    now = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
    return EnrollmentReadSchema(
        id=enrollment_id,
        tenant_id=tenant_id,
        student_profile_id=1001,
        course_id=701,
        term_id=1,
        enrollment_status=EnrollmentStatus.ENROLLED,
        enrollment_type=EnrollmentType.REGULAR,
        enrolled_at=now,
        dropped_at=None,
        grade_code=None,
        grade_points=None,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
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
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["student_profile_id"] == 1001
    assert body["course_id"] == 701
    assert body["term_id"] == 1