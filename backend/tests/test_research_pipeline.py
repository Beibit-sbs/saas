from __future__ import annotations

from datetime import date, timedelta

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/research"


def _make_grant(suffix: str = "P3") -> dict:
    return {
        "grant_code": f"GR-P3-{suffix}",
        "title": f"P3-1 Pipeline Grant {suffix}",
        "pi_faculty_id": "FAC-P3-001",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
        "funding_amount": 200000,
        "status": "planned",
    }


def test_create_grant_and_get_by_id() -> None:
    created = client.post(f"{BASE}/grants", headers=ADMIN_HEADERS, json=_make_grant("ID1"))
    assert created.status_code == 200, created.text
    grant_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/grants/{grant_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == grant_id
    assert resp.json()["item"]["grant_code"] == "GR-P3-ID1"


def test_get_grant_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/grants/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_update_grant_status_planned_to_active() -> None:
    created = client.post(f"{BASE}/grants", headers=ADMIN_HEADERS, json=_make_grant("ST1"))
    assert created.status_code == 200, created.text
    grant_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/grants/{grant_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "active"


def test_update_grant_status_active_to_submitted() -> None:
    grant = _make_grant("ST2")
    grant["status"] = "active"
    created = client.post(f"{BASE}/grants", headers=ADMIN_HEADERS, json=grant)
    assert created.status_code == 200, created.text
    grant_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/grants/{grant_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "submitted"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "submitted"


def test_update_grant_status_not_found_returns_404() -> None:
    resp = client.patch(
        f"{BASE}/grants/999999/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert resp.status_code == 404


def test_update_publication_status() -> None:
    pub = {
        "publication_code": "PUB-P3-01",
        "title": "P3-1 Publication Registry Test",
        "lead_author_id": "FAC-P3-002",
        "target_venue": "Nature Research",
        "last_activity_days": 5,
        "status": "draft",
    }
    created = client.post(f"{BASE}/publications", headers=ADMIN_HEADERS, json=pub)
    assert created.status_code == 200, created.text
    pub_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/publications/{pub_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "submitted"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "submitted"


def test_get_publication_by_id() -> None:
    pub = {
        "publication_code": "PUB-P3-02",
        "title": "P3-1 Get Publication Test",
        "lead_author_id": "FAC-P3-003",
        "target_venue": "Science",
        "last_activity_days": 3,
        "status": "draft",
    }
    created = client.post(f"{BASE}/publications", headers=ADMIN_HEADERS, json=pub)
    assert created.status_code == 200, created.text
    pub_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/publications/{pub_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["publication_code"] == "PUB-P3-02"


def test_update_lab_status() -> None:
    lab = {
        "lab_code": "LAB-P3-01",
        "name": "P3-1 Lab Operations Test Lab",
        "status": "active",
    }
    created = client.post(f"{BASE}/labs", headers=ADMIN_HEADERS, json=lab)
    assert created.status_code == 200, created.text
    lab_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/labs/{lab_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "maintenance"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "maintenance"


def test_get_lab_by_id() -> None:
    lab = {
        "lab_code": "LAB-P3-02",
        "name": "P3-1 Get Lab Test",
        "status": "active",
    }
    created = client.post(f"{BASE}/labs", headers=ADMIN_HEADERS, json=lab)
    assert created.status_code == 200, created.text
    lab_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/labs/{lab_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["lab_code"] == "LAB-P3-02"


def test_create_experiment_and_get_by_id() -> None:
    exp = {
        "experiment_code": "EXP-P3-01",
        "title": "P3-2 Experiment Test",
        "lab_code": "LAB-P3-001",
        "principal_investigator_id": "FAC-P3-004",
        "status": "planned",
    }
    created = client.post(f"{BASE}/experiments", headers=ADMIN_HEADERS, json=exp)
    assert created.status_code == 200, created.text
    exp_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/experiments/{exp_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["experiment_code"] == "EXP-P3-01"


def test_update_experiment_status() -> None:
    exp = {
        "experiment_code": "EXP-P3-02",
        "title": "P3-2 Experiment Status Test",
        "lab_code": "LAB-P3-002",
        "principal_investigator_id": "FAC-P3-004",
        "status": "planned",
    }
    created = client.post(f"{BASE}/experiments", headers=ADMIN_HEADERS, json=exp)
    assert created.status_code == 200, created.text
    exp_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/experiments/{exp_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "running"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "running"


def test_get_experiment_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/experiments/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_get_publication_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/publications/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_update_publication_status_draft_to_submitted() -> None:
    pub = {
        "publication_code": "PUB-P3-03",
        "title": "P3-3 Publication Draft Submission Test",
        "lead_author_id": "FAC-P3-003",
        "target_venue": "Journal of Science",
        "last_activity_days": 5,
        "status": "draft",
    }
    created = client.post(f"{BASE}/publications", headers=ADMIN_HEADERS, json=pub)
    assert created.status_code == 200, created.text
    pub_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/publications/{pub_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "submitted"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "submitted"


def test_get_lab_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/labs/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_update_lab_status_inactive_to_active() -> None:
    lab = {
        "lab_code": "LAB-P3-03",
        "name": "P3-4 Lab Reactivation Test",
        "status": "inactive",
    }
    created = client.post(f"{BASE}/labs", headers=ADMIN_HEADERS, json=lab)
    assert created.status_code == 200, created.text
    lab_id = created.json()["item"]["id"]

    resp = client.patch(
        f"{BASE}/labs/{lab_id}/status",
        headers=ADMIN_HEADERS,
        json={"status": "active"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "active"
