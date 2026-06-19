from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.finance_procurement_asset.dependencies import get_finance_procurement_asset_db
from app.modules.finance_procurement_asset.permissions import ALL_PERMISSIONS
from tests.conftest import _auth_headers, client


BASE = "/api/admin/finance-procurement-asset"
VIEWER_HEADERS = _auth_headers("viewer-fpa@example.com", ["viewer"], tenant_id=1)


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="701",
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
    app.dependency_overrides[get_finance_procurement_asset_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_finance_procurement_asset_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_router_surface_count() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    assert len(routes) == 56


@pytest.mark.parametrize("path", ["/overview", "/dashboard", "/billing", "/vendors", "/audit-events", "/metadata-contract", "/bridges/student-finance-referrals"])
def test_no_auth_requires_protection(path: str) -> None:
    assert client.get(f"{BASE}{path}").status_code in (401, 403)


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    app.dependency_overrides[get_current_tenant] = lambda: {"id": tenant_id}
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 400


def test_viewer_cannot_create_vendor_metadata() -> None:
    resp = client.post(f"{BASE}/vendors", headers=VIEWER_HEADERS, json={"reference_key": "vendor-1", "title": "Vendor"})
    assert resp.status_code == 403


@patch("app.modules.finance_procurement_asset.router.service.get_dashboard")
def test_dashboard_contract(mock_dashboard):
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "module": "finance_procurement_asset",
        "contract_version": "A-040.2.RUNTIME",
        "source_spec_commit": "c9df3fa",
        "runtime_mode": "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY",
        "data_source": "computed_from_finance_procurement_asset_metadata",
        "fake_metrics": False,
        "fake_finance_data": False,
        "fake_payment_data": False,
        "provider_connected": False,
        "live_bank_sync": False,
        "live_erp_sync": False,
        "payment_execution_enabled": False,
        "automatic_procurement_approval_enabled": False,
        "automatic_budget_approval_enabled": False,
        "automatic_vendor_award_enabled": False,
        "hidden_score_present": False,
        "human_review_required": True,
        "incomplete_data": True,
        "limitations": ["metadata_only_runtime"],
        "summary": {"billing": {"VISIBLE_METADATA_ONLY": 1}},
    }
    resp = client.get(f"{BASE}/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["fake_metrics"] is False
    assert resp.json()["source_spec_commit"] == "c9df3fa"


def test_metadata_contract_endpoint() -> None:
    resp = client.get(f"{BASE}/metadata-contract", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["route_count"] == 56
    assert resp.json()["table_count"] == 24
    assert resp.json()["permission_count"] == 50


def test_safety_boundaries_endpoint() -> None:
    resp = client.get(f"{BASE}/safety-boundaries", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["payment_execution_enabled"] is False
    assert resp.json()["human_review_required"] is True
