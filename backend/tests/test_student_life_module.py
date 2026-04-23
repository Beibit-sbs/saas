from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/student-life"


def test_create_and_list_student_life_entities() -> None:
    counseling_resp = client.post(
        f"{BASE}/counseling-cases",
        headers=ADMIN_HEADERS,
        json={
            "case_code": "CSL-2026-01",
            "student_id": "STU-500",
            "concern_type": "anxiety_support",
            "status": "open",
        },
    )
    assert counseling_resp.status_code == 200, counseling_resp.text

    wellbeing_resp = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=ADMIN_HEADERS,
        json={
            "student_id": "STU-500",
            "wellbeing_score": 32,
            "status": "at_risk",
        },
    )
    assert wellbeing_resp.status_code == 200, wellbeing_resp.text

    accessibility_resp = client.post(
        f"{BASE}/accessibility-supports",
        headers=ADMIN_HEADERS,
        json={
            "support_code": "ACC-2026-01",
            "student_id": "STU-500",
            "support_type": "assistive_technology",
            "status": "active",
        },
    )
    assert accessibility_resp.status_code == 200, accessibility_resp.text

    disciplinary_resp = client.post(
        f"{BASE}/disciplinary-cases",
        headers=ADMIN_HEADERS,
        json={
            "incident_code": "DISC-2026-01",
            "student_id": "STU-500",
            "incident_type": "code_of_conduct",
            "severity": "medium",
            "status": "under_review",
        },
    )
    assert disciplinary_resp.status_code == 200, disciplinary_resp.text

    list_resp = client.get(f"{BASE}/counseling-cases", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    assert isinstance(list_resp.json().get("items"), list)


def test_student_life_health_snapshot_counts_risk_indicators() -> None:
    client.post(
        f"{BASE}/wellbeing-checkins",
        headers=ADMIN_HEADERS,
        json={
            "student_id": "STU-801",
            "wellbeing_score": 28,
            "status": "at_risk",
        },
    )
    client.post(
        f"{BASE}/accessibility-supports",
        headers=ADMIN_HEADERS,
        json={
            "support_code": "ACC-2026-02",
            "student_id": "STU-801",
            "support_type": "extended_exam_time",
            "status": "requested",
        },
    )
    client.post(
        f"{BASE}/disciplinary-cases",
        headers=ADMIN_HEADERS,
        json={
            "incident_code": "DISC-2026-02",
            "student_id": "STU-801",
            "incident_type": "attendance_violation",
            "severity": "high",
            "status": "reported",
        },
    )

    health_resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert health_resp.status_code == 200, health_resp.text
    item = health_resp.json()["item"]
    assert item["wellbeing_checkins_total"] >= 1
    assert item["at_risk_wellbeing_checkins"] >= 1
    assert item["accessibility_supports_total"] >= 1
    assert item["active_accessibility_supports"] >= 1
    assert item["disciplinary_cases_total"] >= 1
    assert item["unresolved_disciplinary_cases"] >= 1