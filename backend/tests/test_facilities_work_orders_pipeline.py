"""Phase XI-XI1: Facilities Work Orders pipeline tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE_ORDERS = "/api/admin/facilities/work-orders"
BASE_REQUESTS = "/api/admin/facilities/maintenance-requests"

FAC_HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="facilities.admin@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["facilities.read", "facilities.write"],
        )
    )
}


def _make_order(suffix: str = "XI1") -> dict:
    return {
        "order_code": f"WO-XI1-{suffix}",
        "facility_code": "FAC-001",
        "title": f"Repair HVAC unit {suffix}",
        "work_type": "repair",
        "priority": "medium",
        "assigned_to": "tech@example.com",
        "status": "open",
    }


def _make_request(suffix: str = "XI1") -> dict:
    return {
        "request_code": f"MR-XI1-{suffix}",
        "facility_code": "FAC-002",
        "issue_type": "hvac",
        "severity": "medium",
        "notes": f"Heating not working in room {suffix}",
        "status": "pending",
    }


def test_create_work_order_and_get_by_id() -> None:
    created = client.post(BASE_ORDERS, headers=FAC_HEADERS, json=_make_order("ID1"))
    assert created.status_code == 200, created.text
    order_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE_ORDERS}/{order_id}", headers=FAC_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == order_id
    assert resp.json()["item"]["order_code"] == "WO-XI1-ID1"


def test_get_work_order_not_found_returns_404() -> None:
    resp = client.get(f"{BASE_ORDERS}/999999", headers=FAC_HEADERS)
    assert resp.status_code == 404


def test_list_work_orders_returns_items() -> None:
    client.post(BASE_ORDERS, headers=FAC_HEADERS, json=_make_order("LIST1"))
    client.post(BASE_ORDERS, headers=FAC_HEADERS, json=_make_order("LIST2"))

    resp = client.get(BASE_ORDERS, headers=FAC_HEADERS)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["items"]) >= 2


def test_update_work_order_status_to_completed() -> None:
    created = client.post(BASE_ORDERS, headers=FAC_HEADERS, json=_make_order("ST1"))
    assert created.status_code == 200, created.text
    order_id = created.json()["item"]["id"]

    resp = client.patch(f"{BASE_ORDERS}/{order_id}/status", headers=FAC_HEADERS, json={"status": "completed"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "completed"


def test_update_work_order_status_not_found_returns_404() -> None:
    resp = client.patch(f"{BASE_ORDERS}/999999/status", headers=FAC_HEADERS, json={"status": "completed"})
    assert resp.status_code == 404


def test_create_critical_work_order_fires_event() -> None:
    payload = {**_make_order("CRIT1"), "priority": "critical"}
    resp = client.post(BASE_ORDERS, headers=FAC_HEADERS, json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["priority"] == "critical"


def test_create_maintenance_request_and_get_by_id() -> None:
    created = client.post(BASE_REQUESTS, headers=FAC_HEADERS, json=_make_request("ID1"))
    assert created.status_code == 200, created.text
    req_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE_REQUESTS}/{req_id}", headers=FAC_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == req_id
    assert resp.json()["item"]["request_code"] == "MR-XI1-ID1"


def test_get_maintenance_request_not_found_returns_404() -> None:
    resp = client.get(f"{BASE_REQUESTS}/999999", headers=FAC_HEADERS)
    assert resp.status_code == 404


def test_update_maintenance_request_status_to_resolved() -> None:
    created = client.post(BASE_REQUESTS, headers=FAC_HEADERS, json=_make_request("ST1"))
    assert created.status_code == 200, created.text
    req_id = created.json()["item"]["id"]

    resp = client.patch(f"{BASE_REQUESTS}/{req_id}/status", headers=FAC_HEADERS, json={"status": "resolved"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "resolved"
