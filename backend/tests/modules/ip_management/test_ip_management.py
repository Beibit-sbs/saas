"""Phase VII-VII1: IP management module tests."""
from __future__ import annotations

import pytest

from app.modules.ip_management import service as ip_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_ip_assets_empty(monkeypatch) -> None:
    monkeypatch.setattr(ip_service, "list_entities_for_tenant", lambda name, tid: [])
    assert ip_service.list_ip_assets(tenant_id=1) == []


def test_list_ip_assets_filter_by_type(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "asset_code": "PAT-001",
            "title": "Novel Algorithm",
            "inventor_ids": "INV-1",
            "ip_type": "patent",
            "status": "filed",
            "commercialization_status": "none",
            "licensing_revenue": 0.0,
            "tenant_id": 1,
        },
        {
            "id": 2,
            "asset_code": "TM-001",
            "title": "University Brand",
            "inventor_ids": None,
            "ip_type": "trademark",
            "status": "active",
            "commercialization_status": "none",
            "licensing_revenue": 0.0,
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(ip_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = ip_service.list_ip_assets(tenant_id=1, ip_type="patent")
    assert len(result) == 1
    assert result[0]["asset_code"] == "PAT-001"


def test_list_ip_assets_filter_by_status(monkeypatch) -> None:
    rows = [
        {"id": 1, "asset_code": "PAT-002", "title": "Method X", "ip_type": "patent", "status": "granted", "commercialization_status": "licensed", "licensing_revenue": 5000.0, "tenant_id": 2},
        {"id": 2, "asset_code": "PAT-003", "title": "System Y", "ip_type": "patent", "status": "draft", "commercialization_status": "none", "licensing_revenue": 0.0, "tenant_id": 2},
    ]
    monkeypatch.setattr(ip_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = ip_service.list_ip_assets(tenant_id=2, status="granted")
    assert len(result) == 1
    assert result[0]["asset_code"] == "PAT-002"


def test_get_ip_management_brain_context_strong(monkeypatch) -> None:
    rows = [
        {"id": 1, "asset_code": "PAT-1", "ip_type": "patent", "status": "granted", "commercialization_status": "licensed", "licensing_revenue": 10000.0, "tenant_id": 3},
        {"id": 2, "asset_code": "PAT-2", "ip_type": "patent", "status": "filed", "commercialization_status": "licensed", "licensing_revenue": 5000.0, "tenant_id": 3},
        {"id": 3, "asset_code": "SW-1", "ip_type": "software", "status": "active", "commercialization_status": "none", "licensing_revenue": 0.0, "tenant_id": 3},
    ]
    monkeypatch.setattr(ip_service, "list_entities_for_tenant", lambda name, tid: rows)
    ctx = ip_service.get_ip_management_brain_context(tenant_id=3)
    assert ctx["total_assets"] == 3
    assert ctx["active_patents"] == 2
    assert ctx["commercialized_assets"] == 2
    assert ctx["total_licensing_revenue"] == 15000.0
    assert ctx["portfolio_health"] == "strong"


def test_get_ip_management_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(ip_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = ip_service.get_ip_management_brain_context(tenant_id=1)
    assert ctx["total_assets"] == 0
    assert ctx["commercialization_rate"] == 0.0
    assert ctx["portfolio_health"] == "early_stage"


def test_http_list_ip_assets_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.ip_management.router.list_ip_assets",
        lambda tenant_id, ip_type=None, status=None: [],
    )
    resp = test_client.get("/api/admin/ip-management/assets", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_ip_asset(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 20,
        "asset_code": "PAT-020",
        "title": "Novel Compression Method",
        "inventor_ids": "INV-20",
        "ip_type": "patent",
        "status": "draft",
        "filing_date": None,
        "grant_date": None,
        "commercialization_status": "none",
        "licensing_revenue": None,
        "notes": None,
        "integration_source": None,
        "tenant_id": 1,
    }
    monkeypatch.setattr(
        "app.modules.ip_management.router.create_ip_asset",
        lambda payload, tenant_id: created,
    )
    resp = test_client.post(
        "/api/admin/ip-management/assets",
        json={
            "asset_code": "PAT-020",
            "title": "Novel Compression Method",
            "ip_type": "patent",
            "status": "draft",
        },
        headers=dict(ADMIN_HEADERS),
    )
    assert resp.status_code == 201
    assert resp.json()["record"]["id"] == 20


def test_http_brain_context_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "ip_management",
        "tenant_id": 1,
        "total_assets": 10,
        "active_patents": 5,
        "commercialized_assets": 4,
        "total_licensing_revenue": 50000.0,
        "commercialization_rate": 0.4,
        "portfolio_health": "strong",
    }
    monkeypatch.setattr(
        "app.modules.ip_management.router.get_ip_management_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/ip-management/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "ip_management"
    assert body["portfolio_health"] == "strong"
    assert body["active_patents"] == 5
