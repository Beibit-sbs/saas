from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/student-life"


def _seed_enrollment_string_student(student_id: str, tenant_id: int = 1) -> None:
    """Seed enrollment with string student_id to satisfy _check_student_is_enrolled_for_disciplinary."""
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("enrollments", {})
        _state.counters.setdefault("enrollments", 0)
        _state.counters["enrollments"] += 1
        eid = _state.counters["enrollments"]
        _state.data["enrollments"][eid] = {
            "id": eid,
            "student_id": student_id,
            "course_id": 1,
            "semester": "Fall 2025",
            "status": "active",
            "tenant_id": str(tenant_id),
        }


def _sl_headers(*permissions: str) -> dict:
    token = create_access_token(
        user_id="sl.owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=list(permissions),
    )
    return {"Authorization": f"Bearer {token}"}


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

    _seed_enrollment_string_student("STU-500")
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
    _seed_enrollment_string_student("STU-801")
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


# ---------------------------------------------------------------------------
# Auth / permission guards
# ---------------------------------------------------------------------------


def test_student_life_endpoints_require_auth() -> None:
    """All GET/POST endpoints must reject unauthenticated requests with 401."""
    paths = [
        ("GET", f"{BASE}/health"),
        ("GET", f"{BASE}/counseling-cases"),
        ("GET", f"{BASE}/wellbeing-checkins"),
        ("GET", f"{BASE}/accessibility-supports"),
        ("GET", f"{BASE}/disciplinary-cases"),
    ]
    for method, path in paths:
        resp = getattr(client, method.lower())(path)
        assert resp.status_code == 401, f"{method} {path} should be 401, got {resp.status_code}"


def test_student_life_endpoints_require_read_permission() -> None:
    """Tokens with no student_life permission must receive 403."""
    no_perm_headers = _sl_headers("other.read")
    paths = [
        f"{BASE}/health",
        f"{BASE}/counseling-cases",
        f"{BASE}/wellbeing-checkins",
        f"{BASE}/accessibility-supports",
        f"{BASE}/disciplinary-cases",
    ]
    for path in paths:
        resp = client.get(path, headers=no_perm_headers)
        assert resp.status_code == 403, f"GET {path} should be 403, got {resp.status_code}"


def test_student_life_write_requires_write_permission() -> None:
    """Read-only token must not be able to create entities (403 on all POST)."""
    read_only = _sl_headers("student_life.read")
    posts = [
        (f"{BASE}/counseling-cases", {"case_code": "CSL-AUTH-01", "student_id": "STU-99", "concern_type": "test"}),
        (f"{BASE}/wellbeing-checkins", {"student_id": "STU-99", "wellbeing_score": 50}),
        (f"{BASE}/accessibility-supports", {"support_code": "ACC-AUTH-01", "student_id": "STU-99", "support_type": "test"}),
        (f"{BASE}/disciplinary-cases", {"incident_code": "DISC-AUTH-01", "student_id": "STU-99", "incident_type": "test", "severity": "low"}),
    ]
    for path, payload in posts:
        resp = client.post(path, headers=read_only, json=payload)
        assert resp.status_code == 403, f"POST {path} should be 403, got {resp.status_code}"


# ---------------------------------------------------------------------------
# List endpoints round-trip (create → appear in list)
# ---------------------------------------------------------------------------


def test_wellbeing_checkins_list_returns_created_item() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    create_resp = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=rw,
        json={"student_id": "STU-LIST-WB-01", "wellbeing_score": 45, "status": "watch"},
    )
    assert create_resp.status_code == 200, create_resp.text
    created_id = create_resp.json()["item"]["id"]

    list_resp = client.get(f"{BASE}/wellbeing-checkins", headers=rw)
    assert list_resp.status_code == 200, list_resp.text
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert created_id in ids


def test_accessibility_supports_list_returns_created_item() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    create_resp = client.post(
        f"{BASE}/accessibility-supports",
        headers=rw,
        json={
            "support_code": "ACC-LIST-01",
            "student_id": "STU-LIST-ACC-01",
            "support_type": "sign_language",
            "status": "active",
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    created_id = create_resp.json()["item"]["id"]

    list_resp = client.get(f"{BASE}/accessibility-supports", headers=rw)
    assert list_resp.status_code == 200, list_resp.text
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert created_id in ids


def test_disciplinary_cases_list_returns_created_item() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    _seed_enrollment_string_student("STU-LIST-DISC-01")
    create_resp = client.post(
        f"{BASE}/disciplinary-cases",
        headers=rw,
        json={
            "incident_code": "DISC-LIST-01",
            "student_id": "STU-LIST-DISC-01",
            "incident_type": "academic_dishonesty",
            "severity": "high",
            "status": "under_review",
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    created_id = create_resp.json()["item"]["id"]

    list_resp = client.get(f"{BASE}/disciplinary-cases", headers=rw)
    assert list_resp.status_code == 200, list_resp.text
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert created_id in ids


def test_counseling_cases_list_returns_created_item() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    create_resp = client.post(
        f"{BASE}/counseling-cases",
        headers=rw,
        json={
            "case_code": "CSL-LIST-01",
            "student_id": "STU-LIST-CSL-01",
            "concern_type": "grief_support",
            "status": "open",
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    created_id = create_resp.json()["item"]["id"]

    list_resp = client.get(f"{BASE}/counseling-cases", headers=rw)
    assert list_resp.status_code == 200, list_resp.text
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert created_id in ids


# ---------------------------------------------------------------------------
# Validation / rejection cases
# ---------------------------------------------------------------------------


def test_wellbeing_checkin_rejects_out_of_range_score() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    over_resp = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=rw,
        json={"student_id": "STU-VAL-01", "wellbeing_score": 101},
    )
    assert over_resp.status_code == 422, over_resp.text

    under_resp = client.post(
        f"{BASE}/wellbeing-checkins",
        headers=rw,
        json={"student_id": "STU-VAL-01", "wellbeing_score": -1},
    )
    assert under_resp.status_code == 422, under_resp.text


def test_counseling_case_rejects_missing_required_fields() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    resp = client.post(
        f"{BASE}/counseling-cases",
        headers=rw,
        json={"student_id": "STU-VAL-02"},  # missing case_code + concern_type
    )
    assert resp.status_code == 422, resp.text


def test_disciplinary_case_rejects_missing_severity() -> None:
    rw = _sl_headers("student_life.read", "student_life.write")

    resp = client.post(
        f"{BASE}/disciplinary-cases",
        headers=rw,
        json={
            "incident_code": "DISC-VAL-01",
            "student_id": "STU-VAL-03",
            "incident_type": "policy_breach",
            # missing severity
        },
    )
    assert resp.status_code == 422, resp.text


def test_student_life_health_endpoint_shape() -> None:
    """Health response must contain all expected keys with correct types."""
    resp = client.get(f"{BASE}/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    item = resp.json()["item"]
    expected_keys = {
        "counseling_cases_total",
        "open_counseling_cases",
        "wellbeing_checkins_total",
        "at_risk_wellbeing_checkins",
        "accessibility_supports_total",
        "active_accessibility_supports",
        "disciplinary_cases_total",
        "unresolved_disciplinary_cases",
    }
    missing = expected_keys - item.keys()
    assert not missing, f"Health snapshot missing keys: {missing}"
    for key in expected_keys:
        assert isinstance(item[key], int), f"{key} should be int, got {type(item[key])}"
