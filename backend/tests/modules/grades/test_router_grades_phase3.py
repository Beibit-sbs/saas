from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterator
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    MutationResult,
    OptimisticLockConflictError,
)
from app.main import app
from app.modules.grades import service as grades_service
from app.modules.grades.dependencies import get_grades_db
from app.modules.grades.schemas import (
    GradeEnrollmentConsistencyIssueSchema,
    GradeEnrollmentConsistencyReportSchema,
    GradeListResponseSchema,
    GradeReadSchema,
)
from app.modules.rbac import service as rbac_service
from tests.conftest import (
    ADMIN_HEADERS,
    _auth_headers,
    _configure_db_only_role_resolution,
    client,
)


@pytest.fixture(autouse=True)
def _enable_grades_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"grades.read", "grades.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.grades@example.com": ["student"],
        },
    )


@pytest.fixture
def override_grades_db() -> Iterator[MagicMock]:
    session = MagicMock()
    app.dependency_overrides[get_grades_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_grades_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.grades@example.com", ["student"])


def _grade_schema() -> GradeReadSchema:
    now = datetime(2026, 3, 23, 19, 0, 0, tzinfo=UTC)
    return GradeReadSchema(
        id=7001,
        tenant_id=1,
        enrollment_id=4001,
        grade_code="A",
        grade_points=Decimal("4.00"),
        grading_scale_id=9001,
        submitted_by="instructor@example.com",
        submitted_at=now,
        version=1,
        metadata_json={},
    )


def test_submit_grade_success(
    monkeypatch: pytest.MonkeyPatch,
    override_grades_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_submit_grade(self, tenant_id: int, request, actor_id: str):
        assert tenant_id == 1
        assert actor_id == "owner@example.com"
        return MutationResult(entity=_grade_schema())

    monkeypatch.setattr(grades_service.GradeLifecycleService, "submit_grade", fake_submit_grade)

    response = client.post(
        "/api/admin/grades/submit",
        headers=admin_headers,
        json={
            "enrollment_id": 4001,
            "grading_scale_id": 9001,
            "grade_code": "A",
            "grade_points": "4.00",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["grade"]["grade_code"] == "A"


def test_submit_grade_requires_permission(student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/admin/grades/submit",
        headers=student_headers,
        json={
            "enrollment_id": 4001,
            "grading_scale_id": 9001,
            "grade_code": "A",
            "grade_points": "4.00",
        },
    )

    assert response.status_code == 403, response.text


def test_change_grade_optimistic_lock_returns_409(
    monkeypatch: pytest.MonkeyPatch,
    override_grades_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_change_grade(self, tenant_id: int, request, actor_id: str):
        raise OptimisticLockConflictError("Version mismatch")

    monkeypatch.setattr(grades_service.GradeLifecycleService, "change_grade", fake_change_grade)

    response = client.patch(
        "/api/admin/grades/change",
        headers=admin_headers,
        json={
            "enrollment_id": 4001,
            "grading_scale_id": 9001,
            "new_grade_code": "B",
            "new_grade_points": "3.00",
            "expected_version": 99,
        },
    )

    assert response.status_code == 409, response.text


def test_list_course_grades_success(
    monkeypatch: pytest.MonkeyPatch,
    override_grades_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_course_grades(
        self,
        tenant_id: int,
        course_id: int,
        term_id: int | None,
        page: int,
        page_size: int,
        actor_id: str | None = None,
    ):
        assert course_id == 701
        assert page == 1
        assert page_size == 20
        assert actor_id == "owner@example.com"
        return GradeListResponseSchema(total=1, page=1, page_size=20, items=[_grade_schema()])

    monkeypatch.setattr(grades_service.GradeLifecycleService, "list_course_grades", fake_list_course_grades)

    response = client.get("/api/admin/courses/701/grades", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1


def test_get_grade_enrollment_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    override_grades_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_list_consistency(self, tenant_id: int):
        assert tenant_id == 1
        return GradeEnrollmentConsistencyReportSchema(
            enrollment_count=2,
            grade_submission_count=2,
            issue_count=1,
            issues=[
                GradeEnrollmentConsistencyIssueSchema(
                    issue_type="grade_enrollment_mismatch",
                    enrollment_id=4002,
                    grade_submission_id=7002,
                    field="grade_code",
                    expected="B",
                    actual="C",
                )
            ],
        )

    monkeypatch.setattr(
        grades_service.GradeLifecycleService,
        "list_tenant_grade_enrollment_consistency_report",
        fake_list_consistency,
    )

    response = client.get("/api/admin/grades/consistency", headers=admin_headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["issue_count"] == 1
    assert payload["issues"][0]["issue_type"] == "grade_enrollment_mismatch"
