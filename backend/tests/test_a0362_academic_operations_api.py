from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.academic_operations.permissions import ALL_PERMISSIONS
from app.modules.auth.token_service import create_access_token
from app.core.tenant import get_current_tenant
from tests.conftest import _auth_headers, client


BASE = "/api/admin/academic-operations"
VIEWER_HEADERS = _auth_headers("viewer-academic-operations@example.com", ["viewer"], tenant_id=1)


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="301",
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
    app.dependency_overrides[get_academic_operations_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_academic_operations_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_router_surface_count() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    assert len(routes) == 40


@pytest.mark.parametrize("path", ["/health", "/dashboard", "/matrix-summary", "/academic-groups", "/bridges", "/audit"])
def test_no_auth_requires_protection(path: str) -> None:
    assert client.get(f"{BASE}{path}").status_code in (401, 403)


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "bad"])  # type: ignore[list-item]
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": tenant_id}
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 400


def test_viewer_cannot_create_academic_group() -> None:
    resp = client.post(f"{BASE}/academic-groups", headers=VIEWER_HEADERS, json={"group_code": "GRP-1", "group_name": "Group"})
    assert resp.status_code == 403


@patch("app.modules.academic_operations.router.service.list_academic_groups_service")
def test_list_academic_groups(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, group_code="GRP-1", group_name="Group", external_ref=None, notes=None, status="ACTIVE", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="VRT-301", source_capability_id="VRT-301", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)]
    resp = client.get(f"{BASE}/academic-groups", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["group_code"] == "GRP-1"


@patch("app.modules.academic_operations.router.service.create_academic_group_service")
def test_create_academic_group(mock_create):
    mock_create.return_value = SimpleNamespace(id=1, tenant_id=1, group_code="GRP-2", group_name="Group 2", external_ref=None, notes=None, status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="VRT-301", source_capability_id="VRT-301", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.post(f"{BASE}/academic-groups", headers=ADMIN_HEADERS, json={"group_code": "GRP-2", "group_name": "Group 2"})
    assert resp.status_code == 201
    assert resp.json()["automated_decision"] is False


@patch("app.modules.academic_operations.router.service.get_academic_group_service")
def test_get_academic_group(mock_get):
    mock_get.return_value = SimpleNamespace(id=1, tenant_id=1, group_code="GRP-3", group_name="Group 3", external_ref=None, notes=None, status="ACTIVE", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="VRT-301", source_capability_id="VRT-301", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.get(f"{BASE}/academic-groups/1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["group_name"] == "Group 3"


@patch("app.modules.academic_operations.router.service.update_academic_group_service")
def test_update_academic_group(mock_update):
    mock_update.return_value = SimpleNamespace(id=1, tenant_id=1, group_code="GRP-4", group_name="Updated Group", external_ref=None, notes=None, status="ACTIVE", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="VRT-301", source_capability_id="VRT-301", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.patch(f"{BASE}/academic-groups/1", headers=ADMIN_HEADERS, json={"group_name": "Updated Group"})
    assert resp.status_code == 200
    assert resp.json()["group_name"] == "Updated Group"


@patch("app.modules.academic_operations.router.service.get_academic_operations_dashboard_service")
def test_dashboard_contract(mock_dashboard):
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "fake_metrics": False,
        "data_source": "computed_from_academic_operations_metadata",
        "master_matrix_commit": "c79cc31",
        "master_matrix_rows": 467,
        "incomplete_data": True,
        "limitations": [],
        "counts": {"academic_groups": 1},
        "canonical_bridge_counts": {"student_lifecycle": 1},
    }
    resp = client.get(f"{BASE}/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["fake_metrics"] is False
    assert resp.json()["master_matrix_commit"] == "c79cc31"


@patch("app.modules.academic_operations.router.service.get_academic_operations_health_service")
def test_health_contract(mock_health):
    mock_health.return_value = {
        "tenant_id": 1,
        "module": "academic_operations",
        "target_level": "L3",
        "foundation_status": "MATRIX_GUIDED_CANONICAL_AWARE_BACKEND_FOUNDATION",
        "duplicate_module_policy": "REUSE_CANONICALS_AND_BRIDGE_ONLY",
        "provider_integration_enabled": False,
        "platonus_sync_enabled": False,
        "sis_sync_enabled": False,
        "hidden_score_present": False,
        "fake_metrics": False,
        "incomplete_data": True,
        "limitations": [],
        "route_count": 39,
        "table_count": 19,
    }
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["module"] == "academic_operations"


@patch("app.modules.academic_operations.router.service.get_academic_operations_matrix_summary_service")
def test_matrix_summary_contract(mock_matrix):
    mock_matrix.return_value = {
        "master_matrix_commit": "c79cc31",
        "master_matrix_rows": 467,
        "contract_version": "A-036.2",
        "target_level": "L3",
        "duplicate_module_policy": "REUSE_CANONICALS_AND_BRIDGE_ONLY",
        "true_new_modules": ["academic_group_management"],
        "canonical_reuse_map": {"course_catalog": "course_catalog_management"},
        "bridge_map": {"student_lifecycle": "academic_operations_to_student_lifecycle_bridge"},
        "forbidden_runtime_claims": ["official_grade_publication"],
        "required_limitations": ["metadata_only_foundation"],
    }
    resp = client.get(f"{BASE}/matrix-summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["master_matrix_rows"] == 467


@patch("app.modules.academic_operations.router.service.get_canonical_reuse_summary_service")
def test_canonical_reuse_summary(mock_summary):
    mock_summary.return_value = {"tenant_id": 1, "bridge_counts": {"student_lifecycle": 2}, "canonical_reuse_map": {"course_catalog": "course_catalog_management"}, "bridge_map": {}, "reuse_policy": "REUSE_EXISTING_CANONICAL_MODULES_ONLY", "duplicate_policy": "REUSE_CANONICALS_AND_BRIDGE_ONLY"}
    resp = client.get(f"{BASE}/canonical-reuse-summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["bridge_counts"]["student_lifecycle"] == 2


@patch("app.modules.academic_operations.router.service.list_canonical_module_bridges_service")
def test_list_bridges(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, bridge_type="student_lifecycle", canonical_module_ref="academic_records", external_ref=None, metadata_json={}, status="ACTIVE", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="BRG-101", source_capability_id="BRG-101", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)]
    resp = client.get(f"{BASE}/bridges", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["bridge_type"] == "student_lifecycle"


@patch("app.modules.academic_operations.router.service.create_canonical_module_bridge_service")
def test_create_bridge(mock_create):
    mock_create.return_value = SimpleNamespace(id=1, tenant_id=1, bridge_type="document_workflow", canonical_module_ref="document_workflow", external_ref=None, metadata_json={}, status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="BRG-102", source_capability_id="BRG-102", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.post(f"{BASE}/bridges", headers=ADMIN_HEADERS, json={"bridge_type": "document_workflow", "canonical_module_ref": "document_workflow", "metadata": {}})
    assert resp.status_code == 201
    assert resp.json()["canonical_module_ref"] == "document_workflow"


@patch("app.modules.academic_operations.router.service.list_evidence_metadata_service")
def test_list_evidence(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, entity_type="gradebook_metadata", entity_id=1, evidence_kind="note", external_ref=None, metadata_json={}, status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="VRT-315", source_capability_id="VRT-315", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)]
    resp = client.get(f"{BASE}/evidence", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["entity_type"] == "gradebook_metadata"


@patch("app.modules.academic_operations.router.service.attach_evidence_metadata_service")
def test_create_evidence(mock_create):
    mock_create.return_value = SimpleNamespace(id=1, tenant_id=1, entity_type="gradebook_metadata", entity_id=1, evidence_kind="note", external_ref=None, metadata_json={}, status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False, platonus_sync_enabled=False, sis_sync_enabled=False, hidden_score_present=False, fake_metrics=False, official_grade_publication_enabled=False, automated_grading_enabled=False, automatic_sanction_enabled=False, incomplete_data=True, limitations_json=[], source_matrix_row_id="VRT-315", source_capability_id="VRT-315", created_by_user_id="actor", updated_by_user_id="actor", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z", archived_at=None)
    resp = client.post(f"{BASE}/evidence", headers=ADMIN_HEADERS, json={"entity_type": "gradebook_metadata", "entity_id": 1, "evidence_kind": "note", "metadata": {}})
    assert resp.status_code == 201
    assert resp.json()["evidence_kind"] == "note"


@patch("app.modules.academic_operations.router.service.list_audit_events_service")
def test_list_audit(mock_list):
    mock_list.return_value = [SimpleNamespace(id=1, tenant_id=1, entity_type="academic_group", entity_id=1, event_type="ACADEMIC_GROUP_CREATED", action="create_academic_group", actor_user_id="actor", previous_status=None, new_status="DRAFT", human_review_required=True, automated_decision=False, provider_integration_enabled=False, payload_json={}, created_at="2026-01-01T00:00:00Z")]
    resp = client.get(f"{BASE}/audit", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()[0]["event_type"] == "ACADEMIC_GROUP_CREATED"