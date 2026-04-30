"""Phase X-X2: HR/Payroll pipeline tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/hr-payroll"
HR_HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="hr.owner@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["hr.read", "hr.write"],
        )
    )
}


def _make_employee(suffix: str = "X2") -> dict:
    return {
        "employee_code": f"EMP-X2-{suffix}",
        "full_name": f"Employee {suffix}",
        "department_id": "DEPT-HR-001",
        "role_title": "Lecturer",
        "status": "active",
    }


def _make_cycle(suffix: str = "X2") -> dict:
    return {
        "cycle_code": f"PAY-X2-{suffix}",
        "period_label": "2025-12",
        "total_gross": 50000.0,
        "total_net": 42000.0,
        "employee_count": 10,
        "status": "DRAFT",
    }


def test_create_employee_and_get_by_id() -> None:
    created = client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("ID1"))
    assert created.status_code == 200, created.text
    emp_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/employees/{emp_id}", headers=HR_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == emp_id
    assert resp.json()["item"]["employee_code"] == "EMP-X2-ID1"


def test_get_employee_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/employees/999999", headers=HR_HEADERS)
    assert resp.status_code == 404


def test_list_employees_returns_records() -> None:
    client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("LIST1"))
    client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("LIST2"))

    resp = client.get(f"{BASE}/employees", headers=HR_HEADERS)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["items"]) >= 2


def test_update_employee_status_to_on_leave() -> None:
    created = client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("ST1"))
    assert created.status_code == 200, created.text
    emp_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/employees/{emp_id}/status",
        headers=HR_HEADERS,
        json={"status": "on_leave"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "on_leave"


def test_update_employee_status_not_found_returns_404() -> None:
    resp = client.patch(
        f"{BASE}/employees/999999/status",
        headers=HR_HEADERS,
        json={"status": "on_leave"},
    )
    assert resp.status_code == 404


def test_create_payroll_cycle_and_get_by_id() -> None:
    employee_resp = client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("CYCLE1"))
    assert employee_resp.status_code == 200, employee_resp.text
    created = client.post(f"{BASE}/cycles", headers=HR_HEADERS, json=_make_cycle("ID1"))
    assert created.status_code == 200, created.text
    cycle_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/cycles/{cycle_id}", headers=HR_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == cycle_id
    assert resp.json()["item"]["cycle_code"] == "PAY-X2-ID1"


def test_get_payroll_cycle_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/cycles/999999", headers=HR_HEADERS)
    assert resp.status_code == 404


def test_update_payroll_cycle_status_happy_path_to_paid() -> None:
    employee_resp = client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("CYCLE2"))
    assert employee_resp.status_code == 200, employee_resp.text
    created = client.post(f"{BASE}/cycles", headers=HR_HEADERS, json=_make_cycle("ST1"))
    assert created.status_code == 200, created.text
    cycle_id = created.json()["item"]["id"]

    calculating = client.patch(
        f"{BASE}/cycles/{cycle_id}/status",
        headers=HR_HEADERS,
        json={"status": "CALCULATING"},
    )
    assert calculating.status_code == 200, calculating.text
    assert calculating.json()["item"]["status"] == "CALCULATING"

    approved = client.patch(
        f"{BASE}/cycles/{cycle_id}/status",
        headers=HR_HEADERS,
        json={"status": "APPROVED"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["item"]["status"] == "APPROVED"

    paid = client.patch(
        f"{BASE}/cycles/{cycle_id}/status",
        headers=HR_HEADERS,
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["item"]["status"] == "PAID"


def test_update_payroll_cycle_status_rejects_invalid_transition() -> None:
    employee_resp = client.post(f"{BASE}/employees", headers=HR_HEADERS, json=_make_employee("CYCLE3"))
    assert employee_resp.status_code == 200, employee_resp.text
    created = client.post(f"{BASE}/cycles", headers=HR_HEADERS, json=_make_cycle("INV1"))
    assert created.status_code == 200, created.text
    cycle_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/cycles/{cycle_id}/status",
        headers=HR_HEADERS,
        json={"status": "PAID"},
    )
    assert resp.status_code == 422, resp.text
    assert "Invalid payroll cycle transition" in resp.json()["detail"]


def test_update_payroll_cycle_status_not_found_returns_404() -> None:
    resp = client.patch(
        f"{BASE}/cycles/999999/status",
        headers=HR_HEADERS,
        json={"status": "CALCULATING"},
    )
    assert resp.status_code == 404


def test_create_employee_offboarding_triggers_brain_signal() -> None:
    emp = _make_employee("BRAIN1")
    emp["status"] = "offboarding"

    resp = client.post(f"{BASE}/employees", headers=HR_HEADERS, json=emp)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "offboarding"
