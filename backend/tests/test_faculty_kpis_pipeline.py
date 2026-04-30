"""Phase X-X1: Faculty Performance KPI pipeline tests."""
from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/faculty-performance-kpis"


def _make_kpi(suffix: str = "X1") -> dict:
    return {
        "faculty_id": f"FAC-X1-{suffix}",
        "name": f"Dr. Faculty {suffix}",
        "department_id": "DEPT-X1-001",
        "kpi_period": "2025-Q4",
        "teaching_score": 85.0,
        "research_score": 78.0,
        "service_score": 90.0,
        "overall_score": 84.0,
        "status": "satisfactory",
    }


def _seed_active_contract(faculty_id: str, tenant_id: int = 1) -> None:
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("faculty_contracts", {})
        _state.counters.setdefault("faculty_contracts", 0)
        _state.counters["faculty_contracts"] += 1
        cid = _state.counters["faculty_contracts"]
        _state.data["faculty_contracts"][cid] = {
            "id": cid,
            "faculty_id": faculty_id,
            "contract_type": "full_time",
            "status": "active",
            "tenant_id": str(tenant_id),
        }


def test_create_kpi_and_get_by_id() -> None:
    payload = _make_kpi("ID1")
    _seed_active_contract(payload["faculty_id"])
    created = client.post(BASE, headers=ADMIN_HEADERS, json=payload)
    assert created.status_code == 200, created.text
    kpi_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/{kpi_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == kpi_id
    assert resp.json()["item"]["faculty_id"] == "FAC-X1-ID1"


def test_get_kpi_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_list_kpis_returns_records() -> None:
    payload1 = _make_kpi("LIST1")
    payload2 = _make_kpi("LIST2")
    _seed_active_contract(payload1["faculty_id"])
    _seed_active_contract(payload2["faculty_id"])
    client.post(BASE, headers=ADMIN_HEADERS, json=payload1)
    client.post(BASE, headers=ADMIN_HEADERS, json=payload2)

    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["items"]) >= 2


def test_update_kpi_status_to_needs_improvement() -> None:
    payload = _make_kpi("ST1")
    _seed_active_contract(payload["faculty_id"])
    created = client.post(BASE, headers=ADMIN_HEADERS, json=payload)
    assert created.status_code == 200, created.text
    kpi_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/{kpi_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "needs_improvement"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "needs_improvement"


def test_update_kpi_status_to_on_probation() -> None:
    payload = _make_kpi("ST2")
    _seed_active_contract(payload["faculty_id"])
    created = client.post(BASE, headers=ADMIN_HEADERS, json=payload)
    assert created.status_code == 200, created.text
    kpi_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/{kpi_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "on_probation"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "on_probation"


def test_update_kpi_status_not_found_returns_404() -> None:
    resp = client.patch(
        f"{BASE}/999999/status",
        headers=ADMIN_HEADERS,
        json={"status": "needs_improvement"},
    )
    assert resp.status_code == 404


def test_create_kpi_with_low_score_succeeds() -> None:
    """Low overall_score should trigger brain signal but still return 200."""
    kpi = _make_kpi("BRAIN1")
    kpi["overall_score"] = 45.0
    kpi["status"] = "needs_improvement"
    _seed_active_contract(kpi["faculty_id"])

    resp = client.post(BASE, headers=ADMIN_HEADERS, json=kpi)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["overall_score"] == 45.0


def test_create_kpi_preserves_scores() -> None:
    kpi = _make_kpi("SCORE1")
    kpi["teaching_score"] = 92.5
    kpi["research_score"] = 88.0
    kpi["service_score"] = 75.0
    kpi["overall_score"] = 85.5
    _seed_active_contract(kpi["faculty_id"])

    resp = client.post(BASE, headers=ADMIN_HEADERS, json=kpi)
    assert resp.status_code == 200, resp.text
    item = resp.json()["item"]
    assert item["teaching_score"] == 92.5
    assert item["research_score"] == 88.0
    assert item["overall_score"] == 85.5


def test_list_kpis_filtered_by_department() -> None:
    kpi_a = _make_kpi("DEPT1")
    kpi_a["department_id"] = "DEPT-FILTER-A"
    kpi_b = _make_kpi("DEPT2")
    kpi_b["department_id"] = "DEPT-FILTER-B"
    _seed_active_contract(kpi_a["faculty_id"])
    _seed_active_contract(kpi_b["faculty_id"])
    client.post(BASE, headers=ADMIN_HEADERS, json=kpi_a)
    client.post(BASE, headers=ADMIN_HEADERS, json=kpi_b)

    resp = client.get(f"{BASE}?department_id=DEPT-FILTER-A", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    for item in resp.json()["items"]:
        assert item["department_id"] == "DEPT-FILTER-A"
