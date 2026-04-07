from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.main import app
from app.modules.degree_progress import service as degree_progress_service
from app.modules.degree_progress.dependencies import get_degree_progress_db
from app.modules.degree_progress.schemas import DegreeProgressSchema, GraduationEligibilitySchema, RequirementStatusSchema
from app.modules.rbac import service as rbac_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client


@pytest.fixture(autouse=True)
def _enable_degree_progress_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"degree_progress.read"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.degree@example.com": ["student"],
        },
    )


@pytest.fixture
def override_degree_progress_db() -> MagicMock:
    session = MagicMock()
    app.dependency_overrides[get_degree_progress_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_degree_progress_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.degree@example.com", ["student"])


def _progress() -> DegreeProgressSchema:
    return DegreeProgressSchema(
        student_profile_id=1001,
        program_id=701,
        requirement_id=6001,
        requirement_name="BSCS Core",
        credits_earned=120,
        minimum_credits=120,
        gpa=Decimal("3.10"),
        minimum_gpa=Decimal("2.00"),
        completed_requirements=[
            RequirementStatusSchema(
                requirement_item_id=6101,
                course_id=101,
                required=True,
                credits=3,
                completed=True,
            )
        ],
        remaining_requirements=[],
        graduation_eligible=True,
    )


def test_get_degree_progress_success(
    monkeypatch: pytest.MonkeyPatch,
    override_degree_progress_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_eval(self, tenant_id: int, *, student_profile_id: int, actor_id: str):
        return _progress()

    monkeypatch.setattr(degree_progress_service.DegreeProgressService, "evaluate_degree_progress", fake_eval)

    response = client.get("/api/admin/students/1001/degree-progress", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["graduation_eligible"] is True


def test_get_graduation_eligibility_success(
    monkeypatch: pytest.MonkeyPatch,
    override_degree_progress_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_eligible(self, tenant_id: int, *, student_profile_id: int, actor_id: str):
        return GraduationEligibilitySchema(
            student_profile_id=student_profile_id,
            eligible=True,
            credits_earned=120,
            minimum_credits=120,
            gpa=Decimal("3.10"),
            minimum_gpa=Decimal("2.00"),
            remaining_required_items=0,
        )

    monkeypatch.setattr(degree_progress_service.DegreeProgressService, "is_student_eligible_for_graduation", fake_eligible)

    response = client.get("/api/admin/students/1001/graduation-eligibility", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["eligible"] is True


def test_get_degree_progress_tenant_isolation_404(
    monkeypatch: pytest.MonkeyPatch,
    override_degree_progress_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_eval(self, tenant_id: int, *, student_profile_id: int, actor_id: str):
        raise TenantResourceNotFoundError("student not found for tenant")

    monkeypatch.setattr(degree_progress_service.DegreeProgressService, "evaluate_degree_progress", fake_eval)

    response = client.get("/api/admin/students/1001/degree-progress", headers=admin_headers)
    assert response.status_code == 404, response.text


def test_degree_progress_requires_permission(student_headers: dict[str, str]) -> None:
    response = client.get("/api/admin/students/1001/degree-progress", headers=student_headers)
    assert response.status_code == 403, response.text
