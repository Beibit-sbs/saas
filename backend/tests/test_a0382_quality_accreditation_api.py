from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db
from app.modules.quality_accreditation.permissions import ALL_PERMISSIONS
from tests.conftest import _auth_headers, client


BASE = "/api/admin/quality-accreditation"
VIEWER_HEADERS = _auth_headers("viewer-quality-accreditation@example.com", ["viewer"], tenant_id=1)


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="601",
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
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_router_surface_count() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    assert len(routes) == 70


@pytest.mark.parametrize("path", ["/health", "/overview", "/dashboard", "/frameworks", "/bridges", "/audit"])
def test_no_auth_requires_protection(path: str) -> None:
    assert client.get(f"{BASE}{path}").status_code in (401, 403)


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": tenant_id}
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 400


def test_viewer_cannot_create_framework() -> None:
    resp = client.post(f"{BASE}/frameworks", headers=VIEWER_HEADERS, json={"framework_ref": "QF-1", "title": "Framework"})
    assert resp.status_code == 403


@patch("app.modules.quality_accreditation.router.service.list_resource_service")
def test_list_frameworks(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, framework_ref="QF-1", title="Framework", description=None, status="ACTIVE_METADATA_ONLY", human_review_required=True, official_accreditation_approval_enabled=False, official_ministry_submission_enabled=False, official_ranking_claim_enabled=False, automatic_accreditation_decision_enabled=False, provider_integration_enabled=False, external_database_sync_enabled=False, hidden_score_present=False, autonomous_decision=False, incomplete_data=True, limitations_json=[], metadata_json={}, source_capability_id="QA-101", source_family_id="QA-F1", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)]
    resp = client.get(f"{BASE}/frameworks", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["framework_ref"] == "QF-1"


@patch("app.modules.quality_accreditation.router.service.create_resource_service")
def test_create_framework(mock_create):
    mock_create.return_value = SimpleNamespace(id=1, tenant_id=1, framework_ref="QF-2", title="Framework 2", description=None, status="DRAFT", human_review_required=True, official_accreditation_approval_enabled=False, official_ministry_submission_enabled=False, official_ranking_claim_enabled=False, automatic_accreditation_decision_enabled=False, provider_integration_enabled=False, external_database_sync_enabled=False, hidden_score_present=False, autonomous_decision=False, incomplete_data=True, limitations_json=[], metadata_json={}, source_capability_id="QA-101", source_family_id="QA-F1", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.post(f"{BASE}/frameworks", headers=ADMIN_HEADERS, json={"framework_ref": "QF-2", "title": "Framework 2"})
    assert resp.status_code == 201
    assert resp.json()["autonomous_decision"] is False


@patch("app.modules.quality_accreditation.router.service.get_quality_dashboard_service")
def test_dashboard_contract(mock_dashboard):
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "human_review_required": True,
        "official_accreditation_approval_enabled": False,
        "official_ministry_submission_enabled": False,
        "official_ranking_claim_enabled": False,
        "automatic_accreditation_decision_enabled": False,
        "provider_integration_enabled": False,
        "external_database_sync_enabled": False,
        "hidden_score_present": False,
        "autonomous_decision": False,
        "fake_metrics": False,
        "incomplete_data": True,
        "limitations": [],
        "generated_at": "2026-01-01T00:00:00Z",
        "contract_version": "A-038.2",
        "source_spec_commit": "ad2cad9",
        "source_product_map_commit": "1253e19",
        "source_vertical_selection_commit": "7da0c70",
        "master_matrix_commit": "c79cc31",
        "master_matrix_rows": 467,
        "detailed_capability_count": 44,
        "capability_family_count": 10,
        "data_source": "computed_from_quality_accreditation_metadata",
        "frameworks_summary": {"ACTIVE_METADATA_ONLY": 1},
        "standards_summary": {},
        "evidence_summary": {},
        "readiness_summary": {},
        "self_assessment_summary": {},
        "improvement_summary": {},
        "audit_summary": {},
        "program_review_summary": {},
        "bridge_summary": {},
        "brain_signal_summary": {},
        "boundary_summary": {},
    }
    resp = client.get(f"{BASE}/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["fake_metrics"] is False
    assert resp.json()["master_matrix_commit"] == "c79cc31"


@patch("app.modules.quality_accreditation.router.service.list_quality_audit_events_service")
def test_list_audit(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, event_type="FRAMEWORK_CREATED", source_entity_type="quality_framework", source_entity_id=1, actor_user_id="actor", previous_status=None, new_status="DRAFT", human_review_required=True, provider_integration_enabled=False, hidden_score_present=False, payload_json={}, created_at="2026-01-01T00:00:00Z")]
    resp = client.get(f"{BASE}/audit", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["event_type"] == "FRAMEWORK_CREATED"