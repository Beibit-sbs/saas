from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.hr_staff_governance.dependencies import get_hr_staff_governance_db
from app.modules.hr_staff_governance.permissions import ALL_PERMISSIONS
from tests.conftest import _auth_headers, client


BASE = "/api/admin/hr-staff-governance"
VIEWER_HEADERS = _auth_headers("viewer-hr-staff-governance@example.com", ["viewer"], tenant_id=1)


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
    app.dependency_overrides[get_hr_staff_governance_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_hr_staff_governance_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_router_surface_count() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    assert len(routes) == 62


@pytest.mark.parametrize("path", ["/health", "/overview", "/dashboard", "/staff-profiles", "/recruitment-requests", "/audit"])
def test_no_auth_requires_protection(path: str) -> None:
    assert client.get(f"{BASE}{path}").status_code in (401, 403)


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": tenant_id}
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 400


def test_viewer_cannot_create_staff_profile() -> None:
    resp = client.post(f"{BASE}/staff-profiles", headers=VIEWER_HEADERS, json={"staff_ref": "HR-1", "full_name": "Ada Lovelace"})
    assert resp.status_code == 403


@patch("app.modules.hr_staff_governance.router.service.get_hr_dashboard_summary")
def test_dashboard_contract(mock_dashboard):
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "generated_at": "2026-01-01T00:00:00Z",
        "contract_version": "A-039.2",
        "source_spec_commit": "09e968b",
        "source_product_map_commit": "eaff24f",
        "source_vertical_selection_commit": "449a407",
        "runtime_mode": "METADATA_EVIDENCE_HUMAN_REVIEW_ONLY",
        "data_source": "computed_from_hr_staff_governance_metadata",
        "fake_metrics": False,
        "fake_hr_data": False,
        "incomplete_data": True,
        "human_review_required": True,
        "provider_connected": False,
        "live_provider_sync": False,
        "payroll_execution_enabled": False,
        "automatic_decision_enabled": False,
        "hidden_score_present": False,
        "limitation_flags": ["metadata_only_foundation"],
        "limitations": ["metadata_only_foundation"],
        "staff_lifecycle_summary": {"DRAFT": 1},
        "recruitment_readiness": {},
        "onboarding_progress": {},
        "employee_record_completeness": {},
        "leave_request_review_status": {},
        "training_certification_risk": {},
        "disciplinary_human_review_queue": {},
        "offboarding_access_review": {},
        "workload_bridge_visibility": {},
        "payroll_readiness_profile": {},
        "provider_readiness_status": {},
    }
    resp = client.get(f"{BASE}/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["fake_metrics"] is False
    assert resp.json()["source_spec_commit"] == "09e968b"