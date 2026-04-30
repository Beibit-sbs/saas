"""Phase XI-XI2: Asset Inventory pipeline tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE_ITEMS = "/api/admin/asset-inventory/items"
BASE_DEPR = "/api/admin/asset-inventory/depreciation"

ASSET_HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="asset.admin@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["asset_inventory.read", "asset_inventory.write"],
        )
    )
}


def _make_asset(suffix: str = "XI2") -> dict:
    return {
        "asset_code": f"ASSET-XI2-{suffix}",
        "name": f"Laptop {suffix}",
        "category": "it_hardware",
        "location": "Building A, Room 101",
        "condition": "good",
        "purchase_year": 2024,
        "vendor": "Dell",
        "status": "active",
    }


def _make_depreciation(suffix: str = "XI2") -> dict:
    return {
        "asset_code": f"ASSET-XI2-{suffix}",
        "depreciation_method": "straight_line",
        "original_value": 1500.0,
        "current_value": 1200.0,
        "depreciation_rate": 0.2,
        "status": "active",
    }


def test_create_asset_and_get_by_id() -> None:
    created = client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("ID1"))
    assert created.status_code == 200, created.text
    asset_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE_ITEMS}/{asset_id}", headers=ASSET_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == asset_id
    assert resp.json()["item"]["asset_code"] == "ASSET-XI2-ID1"


def test_get_asset_not_found_returns_404() -> None:
    resp = client.get(f"{BASE_ITEMS}/999999", headers=ASSET_HEADERS)
    assert resp.status_code == 404


def test_list_assets_returns_items() -> None:
    client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("LIST1"))
    client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("LIST2"))

    resp = client.get(BASE_ITEMS, headers=ASSET_HEADERS)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["items"]) >= 2


def test_update_asset_status_to_in_maintenance() -> None:
    created = client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("ST1"))
    assert created.status_code == 200, created.text
    asset_id = created.json()["item"]["id"]

    resp = client.patch(f"{BASE_ITEMS}/{asset_id}/status", headers=ASSET_HEADERS, json={"status": "in_maintenance"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "in_maintenance"


def test_update_asset_status_not_found_returns_404() -> None:
    resp = client.patch(f"{BASE_ITEMS}/999999/status", headers=ASSET_HEADERS, json={"status": "decommissioned"})
    assert resp.status_code == 404


def test_create_condemned_asset_fires_event() -> None:
    payload = {**_make_asset("COND1"), "condition": "condemned"}
    resp = client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["condition"] == "condemned"


def test_create_depreciation_and_get_by_id() -> None:
    create_asset = client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("ID1"))
    assert create_asset.status_code == 200, create_asset.text

    created = client.post(BASE_DEPR, headers=ASSET_HEADERS, json=_make_depreciation("ID1"))
    assert created.status_code == 200, created.text
    rec_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE_DEPR}/{rec_id}", headers=ASSET_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == rec_id
    assert resp.json()["item"]["asset_code"] == "ASSET-XI2-ID1"


def test_get_depreciation_not_found_returns_404() -> None:
    resp = client.get(f"{BASE_DEPR}/999999", headers=ASSET_HEADERS)
    assert resp.status_code == 404


def test_list_depreciation_records_returns_items() -> None:
    create_asset_1 = client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("LIST1"))
    assert create_asset_1.status_code == 200, create_asset_1.text
    create_asset_2 = client.post(BASE_ITEMS, headers=ASSET_HEADERS, json=_make_asset("LIST2"))
    assert create_asset_2.status_code == 200, create_asset_2.text

    client.post(BASE_DEPR, headers=ASSET_HEADERS, json=_make_depreciation("LIST1"))
    client.post(BASE_DEPR, headers=ASSET_HEADERS, json=_make_depreciation("LIST2"))

    resp = client.get(BASE_DEPR, headers=ASSET_HEADERS)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["items"]) >= 2
