"""Unit tests for academic integrity router."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.academic_integrity import router as academic_integrity_router
from app.modules.academic_integrity.schemas import IntegrityCaseStatus


@pytest.fixture
def mock_service(monkeypatch):
    """Mock academic integrity service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_tenant(monkeypatch):
    """Mock tenant context."""
    tenant = SimpleNamespace(id=1)
    return tenant


@pytest.fixture
def admin_headers() -> dict[str, str]:
    from tests.conftest import ADMIN_HEADERS

    return dict(ADMIN_HEADERS)


@pytest.fixture
def test_app():
    from tests.conftest import app

    return app


@pytest.fixture
def test_client():
    from tests.conftest import client

    return client


@pytest.fixture
def dependency_overrides(mock_service, mock_tenant, test_app):
    test_app.dependency_overrides[academic_integrity_router.get_service] = lambda: mock_service
    test_app.dependency_overrides[academic_integrity_router.get_current_tenant] = lambda: mock_tenant
    try:
        yield
    finally:
        test_app.dependency_overrides.pop(academic_integrity_router.get_service, None)
        test_app.dependency_overrides.pop(academic_integrity_router.get_current_tenant, None)


def test_list_integrity_cases(
    mock_service,
    dependency_overrides,
    admin_headers: dict[str, str],
    test_client,
):
    """Test listing integrity cases."""
    cases = [
        {
            "id": "case-1",
            "student_id": "student-1",
            "course_id": "course-1",
            "assignment_id": None,
            "case_type": "plagiarism",
            "description": "High similarity detected in submission",
            "evidence_url": "https://example.com/report",
            "priority": "high",
            "status": IntegrityCaseStatus.FLAGGED.value,
            "resolution_notes": None,
            "recommended_action": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "created_by": "owner@example.com",
            "tenant_id": "test-tenant-123",
        }
    ]

    mock_service.list_integrity_cases.return_value = {
        "cases": cases,
        "total": 1,
        "page": 1,
        "page_size": 20,
    }

    response = test_client.get(
        "/api/admin/academic-integrity/cases?page=1&page_size=20",
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["cases"]) == 1
    assert data["cases"][0]["case_type"] == "plagiarism"
    assert data["cases"][0]["status"] == IntegrityCaseStatus.FLAGGED.value


def test_create_integrity_case(
    mock_service,
    dependency_overrides,
    admin_headers: dict[str, str],
    test_client,
):
    """Test creating an integrity case."""
    new_case = {
        "id": "case-new",
        "student_id": "student-1",
        "course_id": "course-1",
        "assignment_id": "assignment-1",
        "case_type": "plagiarism",
        "description": "High similarity detected in submission",
        "evidence_url": "https://example.com/report",
        "priority": "high",
        "status": IntegrityCaseStatus.FLAGGED.value,
        "resolution_notes": None,
        "recommended_action": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "created_by": "owner@example.com",
        "tenant_id": "test-tenant-123",
    }

    mock_service.create_integrity_case.return_value = new_case

    payload = {
        "student_id": "student-1",
        "course_id": "course-1",
        "assignment_id": "assignment-1",
        "case_type": "plagiarism",
        "description": "High similarity detected in submission",
        "evidence_url": "https://example.com/report",
        "priority": "high",
    }

    response = test_client.post(
        "/api/admin/academic-integrity/cases",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["case"]["student_id"] == "student-1"
    assert data["case"]["status"] == IntegrityCaseStatus.FLAGGED.value


def test_update_case_status(
    mock_service,
    dependency_overrides,
    admin_headers: dict[str, str],
    test_client,
):
    """Test updating case status."""
    updated_case = {
        "id": "case-1",
        "student_id": "student-1",
        "course_id": "course-1",
        "assignment_id": None,
        "case_type": "plagiarism",
        "description": "High similarity detected",
        "evidence_url": "https://example.com/report",
        "priority": "high",
        "status": IntegrityCaseStatus.UNDER_REVIEW.value,
        "resolution_notes": "Awaiting student response",
        "recommended_action": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "created_by": "owner@example.com",
        "tenant_id": "test-tenant-123",
    }

    mock_service.update_integrity_case_status.return_value = updated_case

    payload = {
        "status": IntegrityCaseStatus.UNDER_REVIEW.value,
        "resolution_notes": "Awaiting student response",
    }

    response = test_client.patch(
        "/api/admin/academic-integrity/cases/case-1/status",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["case"]["status"] == IntegrityCaseStatus.UNDER_REVIEW.value
    assert data["case"]["resolution_notes"] == "Awaiting student response"
