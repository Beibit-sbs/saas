from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.research_science.dependencies import get_research_science_db
from app.modules.research_science.permissions import ALL_PERMISSIONS
from tests.conftest import _auth_headers, client


BASE = "/api/admin/research-science"
VIEWER_HEADERS = _auth_headers("viewer-research-science@example.com", ["viewer"], tenant_id=1)


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="501",
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
    app.dependency_overrides[get_research_science_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_research_science_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_router_surface_count() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    assert len(routes) == 43


@pytest.mark.parametrize("path", ["/health", "/dashboard", "/matrix-summary", "/projects", "/bridges", "/audit"])
def test_no_auth_requires_protection(path: str) -> None:
    assert client.get(f"{BASE}{path}").status_code in (401, 403)


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "bad"])  # type: ignore[list-item]
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": tenant_id}
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 400


def test_viewer_cannot_create_project() -> None:
    resp = client.post(f"{BASE}/projects", headers=VIEWER_HEADERS, json={"project_ref": "RP-1", "title": "Project"})
    assert resp.status_code == 403


@patch("app.modules.research_science.router.service.list_research_projects_service")
def test_list_projects(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, project_ref="RP-1", department_ref=None, program_ref=None, external_ref=None, title="Project", notes=None, status="ACTIVE", human_review_required=True, autonomous_decision=False, provider_integration_enabled=False, external_database_sync_enabled=False, official_verification_enabled=False, hidden_score_present=False, incomplete_data=True, limitations_json=[], metadata_json={}, source_matrix_row_id="RS-101", source_capability_id="RS-101", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)]
    resp = client.get(f"{BASE}/projects", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["project_ref"] == "RP-1"


@patch("app.modules.research_science.router.service.create_research_project_service")
def test_create_project(mock_create):
    mock_create.return_value = SimpleNamespace(id=1, tenant_id=1, project_ref="RP-2", department_ref=None, program_ref=None, external_ref=None, title="Project 2", notes=None, status="DRAFT", human_review_required=True, autonomous_decision=False, provider_integration_enabled=False, external_database_sync_enabled=False, official_verification_enabled=False, hidden_score_present=False, incomplete_data=True, limitations_json=[], metadata_json={}, source_matrix_row_id="RS-101", source_capability_id="RS-101", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.post(f"{BASE}/projects", headers=ADMIN_HEADERS, json={"project_ref": "RP-2", "title": "Project 2"})
    assert resp.status_code == 201
    assert resp.json()["autonomous_decision"] is False


@patch("app.modules.research_science.router.service.get_research_dashboard_service")
def test_dashboard_contract(mock_dashboard):
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "human_review_required": True,
        "autonomous_decision": False,
        "provider_integration_enabled": False,
        "external_database_sync_enabled": False,
        "official_verification_enabled": False,
        "hidden_score_present": False,
        "fake_metrics": False,
        "incomplete_data": True,
        "limitations": [],
        "generated_at": "2026-01-01T00:00:00Z",
        "contract_version": "A-037.2",
        "source_spec_commit": "02b5564",
        "master_matrix_commit": "c79cc31",
        "master_matrix_rows": 467,
        "capability_count": 60,
        "data_source": "computed_from_research_science_metadata",
        "projects_summary": {"ACTIVE": 1},
        "student_research_summary": {},
        "supervision_summary": {},
        "publications_summary": {},
        "conferences_summary": {},
        "grants_summary": {},
        "ethics_summary": {},
        "evidence_summary": {},
        "bridge_summary": {},
        "brain_readiness_summary": {},
        "boundary_summary": {},
    }
    resp = client.get(f"{BASE}/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["fake_metrics"] is False
    assert resp.json()["master_matrix_commit"] == "c79cc31"


@patch("app.modules.research_science.router.service.list_research_audit_events_service")
def test_list_audit(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, event_type="PROJECT_CREATED", source_entity_type="research_project", source_entity_id=1, actor_user_id="actor", previous_status=None, new_status="DRAFT", human_review_required=True, autonomous_decision=False, provider_integration_enabled=False, hidden_score_present=False, payload_json={}, created_at="2026-01-01T00:00:00Z", request_id=None)]
    resp = client.get(f"{BASE}/audit", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["event_type"] == "PROJECT_CREATED"