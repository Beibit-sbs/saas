from __future__ import annotations

from datetime import date, timedelta

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/research"


def test_create_and_list_research_grants() -> None:
    payload = {
        "grant_code": "GR-2026-01",
        "title": "AI for Education",
        "pi_faculty_id": "FAC-900",
        "deadline": (date.today() + timedelta(days=12)).isoformat(),
        "funding_amount": 150000,
        "status": "active",
    }
    create_resp = client.post(f"{BASE}/grants", headers=ADMIN_HEADERS, json=payload)
    assert create_resp.status_code == 200, create_resp.text
    assert create_resp.json()["item"]["grant_code"] == "GR-2026-01"

    list_resp = client.get(f"{BASE}/grants", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    assert isinstance(list_resp.json().get("items"), list)


def test_research_health_snapshot_counts_risk_indicators() -> None:
    grant_payload = {
        "grant_code": "GR-2026-02",
        "title": "STEM Labs",
        "pi_faculty_id": "FAC-901",
        "deadline": (date.today() + timedelta(days=8)).isoformat(),
        "funding_amount": 85000,
        "status": "active",
    }
    publication_payload = {
        "publication_code": "PUB-2026-11",
        "title": "Adaptive Learning Outcomes",
        "lead_author_id": "FAC-901",
        "target_venue": "Journal of Applied AI",
        "last_activity_days": 120,
        "status": "submitted",
    }

    grant_resp = client.post(f"{BASE}/grants", headers=ADMIN_HEADERS, json=grant_payload)
    assert grant_resp.status_code == 200, grant_resp.text

    publication_resp = client.post(f"{BASE}/publications", headers=ADMIN_HEADERS, json=publication_payload)
    assert publication_resp.status_code == 200, publication_resp.text

    lab_resp = client.post(
        f"{BASE}/labs",
        headers=ADMIN_HEADERS,
        json={"lab_code": "LAB-01", "name": "Bioinformatics Core", "status": "active"},
    )
    assert lab_resp.status_code == 200, lab_resp.text

    ip_resp = client.post(
        f"{BASE}/ip-assets",
        headers=ADMIN_HEADERS,
        json={"asset_code": "IP-001", "title": "Adaptive Rubric Engine", "status": "filed"},
    )
    assert ip_resp.status_code == 200, ip_resp.text

    health_resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert health_resp.status_code == 200, health_resp.text

    item = health_resp.json()["item"]
    assert item["grants_total"] >= 1
    assert item["grants_near_deadline"] >= 1
    assert item["grant_pipeline_at_risk"] >= 1
    assert item["publications_total"] >= 1
    assert item["stalled_publications"] >= 1
    assert item["publication_tracking_alerts"] >= 1
    assert item["labs_total"] >= 1
    assert item["labs_with_low_utilization"] >= 1
    assert item["lab_utilization_rate"] >= 0
    assert item["ip_assets_total"] >= 1


def test_list_labs_and_ip_assets_endpoints_return_lists() -> None:
    labs_resp = client.get(f"{BASE}/labs", headers=ADMIN_HEADERS)
    assert labs_resp.status_code == 200, labs_resp.text
    assert isinstance(labs_resp.json().get("items"), list)

    ip_resp = client.get(f"{BASE}/ip-assets", headers=ADMIN_HEADERS)
    assert ip_resp.status_code == 200, ip_resp.text
    assert isinstance(ip_resp.json().get("items"), list)


def test_create_and_list_research_experiments() -> None:
    create_resp = client.post(
        f"{BASE}/experiments",
        headers=ADMIN_HEADERS,
        json={
            "experiment_code": "EXP-2026-01",
            "title": "Retention Intervention Pilot",
            "lab_code": "LAB-01",
            "principal_investigator_id": "FAC-777",
            "status": "running",
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    assert create_resp.json()["item"]["experiment_code"] == "EXP-2026-01"

    list_resp = client.get(f"{BASE}/experiments", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json().get("items")
    assert isinstance(items, list)
    assert any(item["experiment_code"] == "EXP-2026-01" for item in items)
