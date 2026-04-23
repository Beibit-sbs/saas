from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/procurement"


def test_create_and_list_procurement_entities() -> None:
    vendor_resp = client.post(
        f"{BASE}/vendors",
        headers=ADMIN_HEADERS,
        json={
            "vendor_code": "VEN-001",
            "name": "North Campus Supplies",
            "category": "laboratory",
            "sla_breach_rate": 0.02,
            "on_time_delivery_rate": 0.98,
            "status": "active",
        },
    )
    assert vendor_resp.status_code == 200, vendor_resp.text

    contract_resp = client.post(
        f"{BASE}/contracts",
        headers=ADMIN_HEADERS,
        json={
            "contract_code": "CON-001",
            "vendor_code": "VEN-001",
            "title": "Microscope maintenance agreement",
            "risk_score": 0.15,
            "sla_target_met": True,
            "status": "active",
        },
    )
    assert contract_resp.status_code == 200, contract_resp.text

    asset_resp = client.post(
        f"{BASE}/assets",
        headers=ADMIN_HEADERS,
        json={
            "asset_code": "AST-001",
            "title": "Cryogenic freezer",
            "asset_category": "equipment",
            "status": "available",
        },
    )
    assert asset_resp.status_code == 200, asset_resp.text

    inventory_resp = client.post(
        f"{BASE}/inventory-items",
        headers=ADMIN_HEADERS,
        json={
            "item_code": "INV-001",
            "title": "Chemistry gloves",
            "current_stock": 32,
            "reorder_point": 20,
            "daily_usage_rate": 4,
            "lead_time_days": 5,
            "auto_reorder_enabled": True,
            "status": "healthy",
        },
    )
    assert inventory_resp.status_code == 200, inventory_resp.text

    list_resp = client.get(f"{BASE}/vendors", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    assert isinstance(list_resp.json().get("items"), list)

    inventory_list_resp = client.get(f"{BASE}/inventory-items", headers=ADMIN_HEADERS)
    assert inventory_list_resp.status_code == 200, inventory_list_resp.text
    assert isinstance(inventory_list_resp.json().get("items"), list)


def test_procurement_health_snapshot_counts_risk_indicators() -> None:
    client.post(
        f"{BASE}/vendors",
        headers=ADMIN_HEADERS,
        json={
            "vendor_code": "VEN-002",
            "name": "West Procurement Group",
            "category": "it",
            "sla_breach_rate": 0.24,
            "on_time_delivery_rate": 0.72,
            "status": "under_review",
        },
    )
    client.post(
        f"{BASE}/contracts",
        headers=ADMIN_HEADERS,
        json={
            "contract_code": "CON-002",
            "vendor_code": "VEN-002",
            "title": "Network refresh contract",
            "risk_score": 0.88,
            "sla_target_met": False,
            "status": "expiring",
        },
    )
    client.post(
        f"{BASE}/assets",
        headers=ADMIN_HEADERS,
        json={
            "asset_code": "AST-002",
            "title": "Core switch",
            "asset_category": "network",
            "status": "maintenance",
        },
    )
    client.post(
        f"{BASE}/inventory-items",
        headers=ADMIN_HEADERS,
        json={
            "item_code": "INV-002",
            "title": "Lab pipettes",
            "current_stock": 9,
            "reorder_point": 12,
            "daily_usage_rate": 2,
            "lead_time_days": 4,
            "auto_reorder_enabled": True,
            "status": "critical",
        },
    )

    health_resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert health_resp.status_code == 200, health_resp.text
    item = health_resp.json()["item"]
    assert item["vendors_total"] >= 1
    assert item["vendors_sla_breached"] >= 1
    assert item["contracts_total"] >= 1
    assert item["at_risk_contracts"] >= 1
    assert item["contracts_high_risk"] >= 1
    assert item["assets_total"] >= 1
    assert item["constrained_assets"] >= 1
    assert item["inventory_items_total"] >= 1
    assert item["low_stock_items"] >= 1
    assert item["projected_stockouts_7d"] >= 1
    assert item["auto_reorder_candidates"] >= 1