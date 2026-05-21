from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from app.modules.student_lifecycle.permissions import ALL_PERMISSIONS
from tests.conftest import _auth_headers, client


BASE = "/api/admin/student-lifecycle"
VIEWER_HEADERS = _auth_headers("viewer-student-lifecycle@example.com", ["viewer"], tenant_id=1)


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="201",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=sorted(ALL_PERMISSIONS),
    )
    return {"Authorization": f"Bearer {token}"}


ADMIN_HEADERS = _admin_headers()


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_student_lifecycle_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_student_lifecycle_db, None)


def test_router_surface_count() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    assert len(routes) == 44


def test_no_auth_requires_protection() -> None:
    assert client.get(f"{BASE}/applicants").status_code in (401, 403)
    assert client.get(f"{BASE}/dashboard").status_code in (401, 403)


@patch("app.modules.student_lifecycle.router.service.list_applicants_service")
def test_list_applicants(mock_list):
    mock_list.return_value = [
        SimpleNamespace(
            id=1,
            tenant_id=1,
            applicant_code="APP-1",
            program_interest="CS",
            entry_term="2026-FALL",
            notes=None,
            status="DRAFT",
            human_review_required=True,
            automated_decision=False,
            provider_integration_enabled=False,
            limitations_json=[],
            source_available=False,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            archived_at=None,
        )
    ]
    resp = client.get(f"{BASE}/applicants", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()[0]["applicant_code"] == "APP-1"


@patch("app.modules.student_lifecycle.router.service.create_applicant_service")
def test_create_applicant(mock_create):
    mock_create.return_value = SimpleNamespace(
        id=1,
        tenant_id=1,
        applicant_code="APP-2",
        program_interest="Economics",
        entry_term="2026-FALL",
        notes=None,
        status="DRAFT",
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=[],
        source_available=False,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        archived_at=None,
    )
    resp = client.post(f"{BASE}/applicants", headers=ADMIN_HEADERS, json={"applicant_code": "APP-2", "program_interest": "Economics"})
    assert resp.status_code == 201
    assert resp.json()["automated_decision"] is False


@patch("app.modules.student_lifecycle.router.service.create_student_profile_service")
def test_create_student_profile(mock_create):
    mock_create.return_value = SimpleNamespace(
        id=2,
        tenant_id=1,
        student_code="STU-1",
        source_applicant_id=1,
        program_code="CS",
        notes=None,
        status="PROFILE_CREATED",
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=[],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        archived_at=None,
    )
    resp = client.post(f"{BASE}/students", headers=ADMIN_HEADERS, json={"student_code": "STU-1", "source_applicant_id": 1})
    assert resp.status_code == 201
    assert resp.json()["student_code"] == "STU-1"


@patch("app.modules.student_lifecycle.router.service.create_student_enrollment_service")
def test_create_enrollment(mock_create):
    mock_create.return_value = SimpleNamespace(
        id=3,
        tenant_id=1,
        student_id=2,
        term_code="2026-FALL",
        notes=None,
        status="DRAFT",
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=[],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        archived_at=None,
    )
    resp = client.post(f"{BASE}/enrollment", headers=ADMIN_HEADERS, json={"student_id": 2, "term_code": "2026-FALL"})
    assert resp.status_code == 201
    assert resp.json()["term_code"] == "2026-FALL"


@patch("app.modules.student_lifecycle.router.service.generate_transcript_preview_service")
def test_transcript_preview_is_unofficial(mock_create):
    mock_create.return_value = SimpleNamespace(
        id=4,
        tenant_id=1,
        student_id=2,
        academic_record_id=7,
        status="GENERATED_UNOFFICIAL_PREVIEW",
        official_document=False,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        preview_payload_json={"preview": True},
        limitations_json=[],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    resp = client.post(f"{BASE}/transcripts/preview", headers=ADMIN_HEADERS, json={"student_id": 2, "academic_record_id": 7, "preview_payload": {"preview": True}})
    assert resp.status_code == 201
    assert resp.json()["official_document"] is False


@patch("app.modules.student_lifecycle.router.service.get_student_lifecycle_dashboard_service")
def test_dashboard_contract_flags(mock_dashboard):
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "generated_at": "2026-01-01T00:00:00Z",
        "fake_metrics": False,
        "data_source": "computed_from_student_lifecycle_metadata",
        "incomplete_data": False,
        "limitations": [],
        "applicant_counts_by_status": {"DRAFT": 1},
        "student_counts_by_status": {"ACTIVE": 1},
        "enrollment_counts_by_status": {"ENROLLED": 1},
        "transcript_preview_counts": {"GENERATED_UNOFFICIAL_PREVIEW": 1},
        "degree_progress_counts": {"INCOMPLETE_DATA": 1},
        "request_counts_by_status": {"SUBMITTED": 1},
        "appeal_counts_by_status": {"REVIEWER_REVIEW": 1},
        "intervention_counts_by_status": {"CONTINUED": 1},
        "human_review_required_count": 5,
        "provider_integration_enabled": False,
        "automated_decision_count": 0,
        "hidden_score_present": False,
    }
    resp = client.get(f"{BASE}/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["fake_metrics"] is False
    assert resp.json()["hidden_score_present"] is False


@patch("app.modules.student_lifecycle.router.service.get_student_lifecycle_health_service")
def test_health_returns_module_info(mock_health):
    mock_health.return_value = {
        "tenant_id": 1,
        "generated_at": "2026-01-01T00:00:00Z",
        "module_name": "student_lifecycle",
        "route_count": 44,
        "table_count": 14,
        "fake_metrics": False,
        "data_source": "computed_from_student_lifecycle_metadata",
        "incomplete_data": False,
        "limitations": [],
        "provider_integration_enabled": False,
        "automated_decision_count": 0,
        "hidden_score_present": False,
    }
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["module_name"] == "student_lifecycle"


def test_viewer_cannot_create_applicant() -> None:
    resp = client.post(f"{BASE}/applicants", headers=VIEWER_HEADERS, json={"applicant_code": "APP-9"})
    assert resp.status_code == 403
