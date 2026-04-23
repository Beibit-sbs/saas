from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/operations"


def test_create_and_list_operations_entities() -> None:
    facility_resp = client.post(
        f"{BASE}/facility-issues",
        headers=ADMIN_HEADERS,
        json={
            "facility_code": "BLDG-A-HVAC",
            "issue_type": "hvac_failure",
            "severity": "high",
            "status": "reported",
        },
    )
    assert facility_resp.status_code == 200, facility_resp.text

    work_order_resp = client.post(
        f"{BASE}/work-orders",
        headers=ADMIN_HEADERS,
        json={
            "work_order_code": "WO-2026-01",
            "facility_code": "BLDG-A-HVAC",
            "summary": "Repair air handling unit",
            "status": "open",
        },
    )
    assert work_order_resp.status_code == 200, work_order_resp.text

    cleaning_resp = client.post(
        f"{BASE}/cleaning-checks",
        headers=ADMIN_HEADERS,
        json={
            "room_code": "LAB-201",
            "scheduled_slot": "2026-04-22T08:00Z",
            "status": "missed",
        },
    )
    assert cleaning_resp.status_code == 200, cleaning_resp.text

    readiness_resp = client.post(
        f"{BASE}/room-readiness",
        headers=ADMIN_HEADERS,
        json={
            "room_code": "LAB-201",
            "building_code": "BLDG-A",
            "status": "needs_cleaning",
        },
    )
    assert readiness_resp.status_code == 200, readiness_resp.text

    maintenance_resp = client.post(
        f"{BASE}/maintenance-assets",
        headers=ADMIN_HEADERS,
        json={
            "asset_code": "MA-001",
            "facility_code": "BLDG-A-HVAC",
            "asset_type": "hvac",
            "health_score": 38,
            "days_since_maintenance": 95,
            "expected_service_interval_days": 90,
            "status": "monitored",
        },
    )
    assert maintenance_resp.status_code == 200, maintenance_resp.text

    utility_resp = client.post(
        f"{BASE}/utility-readings",
        headers=ADMIN_HEADERS,
        json={
            "meter_code": "MTR-001",
            "building_code": "BLDG-A",
            "utility_type": "electricity",
            "usage_value": 148,
            "baseline_value": 100,
            "status": "spike",
        },
    )
    assert utility_resp.status_code == 200, utility_resp.text

    list_resp = client.get(f"{BASE}/facility-issues", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    assert isinstance(list_resp.json().get("items"), list)

    maintenance_list = client.get(f"{BASE}/maintenance-assets", headers=ADMIN_HEADERS)
    assert maintenance_list.status_code == 200, maintenance_list.text
    assert isinstance(maintenance_list.json().get("items"), list)

    utility_list = client.get(f"{BASE}/utility-readings", headers=ADMIN_HEADERS)
    assert utility_list.status_code == 200, utility_list.text
    assert isinstance(utility_list.json().get("items"), list)


def test_operations_health_snapshot_counts_risk_indicators() -> None:
    client.post(
        f"{BASE}/facility-issues",
        headers=ADMIN_HEADERS,
        json={
            "facility_code": "BLDG-B-POWER",
            "issue_type": "power_fault",
            "severity": "critical",
            "status": "in_progress",
        },
    )
    client.post(
        f"{BASE}/cleaning-checks",
        headers=ADMIN_HEADERS,
        json={
            "room_code": "ROOM-12",
            "scheduled_slot": "2026-04-22T10:00Z",
            "status": "missed",
        },
    )
    client.post(
        f"{BASE}/room-readiness",
        headers=ADMIN_HEADERS,
        json={
            "room_code": "ROOM-12",
            "building_code": "BLDG-B",
            "status": "maintenance_required",
        },
    )
    client.post(
        f"{BASE}/maintenance-assets",
        headers=ADMIN_HEADERS,
        json={
            "asset_code": "MA-002",
            "facility_code": "BLDG-B-POWER",
            "asset_type": "transformer",
            "health_score": 30,
            "days_since_maintenance": 140,
            "expected_service_interval_days": 120,
            "status": "monitored",
        },
    )
    client.post(
        f"{BASE}/utility-readings",
        headers=ADMIN_HEADERS,
        json={
            "meter_code": "MTR-202",
            "building_code": "BLDG-B",
            "utility_type": "water",
            "usage_value": 245,
            "baseline_value": 180,
            "status": "spike",
        },
    )

    health_resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert health_resp.status_code == 200, health_resp.text
    item = health_resp.json()["item"]
    assert item["facilities_total"] >= 1
    assert item["open_facility_issues"] >= 1
    assert item["missed_cleaning_checks"] >= 1
    assert item["rooms_total"] >= 1
    assert item["rooms_not_ready"] >= 1
    assert item["maintenance_assets_total"] >= 1
    assert item["predictive_maintenance_due"] >= 1
    assert item["utility_readings_total"] >= 1
    assert item["utility_anomaly_readings"] >= 1