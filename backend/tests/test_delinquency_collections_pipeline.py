"""Phase X-X3: Delinquency & Collections pipeline tests."""
from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client

BASE = "/api/admin/delinquency-collections"


def _make_record(suffix: str = "X3", days_overdue: int = 30) -> dict:
    return {
        "student_id": f"STU-X3-{suffix}",
        "invoice_code": f"INV-X3-{suffix}",
        "amount_due": 1500.0,
        "days_overdue": days_overdue,
        "escalation_stage": "stage_1",
        "status": "open",
    }


def _seed_enrollment_string_student(student_id: str, tenant_id: int = 1) -> None:
    """Seed enrollment record with string student_id to satisfy _check_student_has_enrollment_history."""
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


def _create_record(suffix: str = "X3", days_overdue: int = 30, extra: dict | None = None):
    """Seed enrollment and create delinquency record."""
    payload = {**_make_record(suffix, days_overdue), **(extra or {})}
    _seed_enrollment_string_student(payload["student_id"])
    return client.post(BASE, headers=ADMIN_HEADERS, json=payload)


def test_create_record_and_get_by_id() -> None:
    created = _create_record("ID1")
    assert created.status_code == 200, created.text
    rec_id = created.json()["item"]["id"]

    resp = client.get(f"{BASE}/{rec_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["id"] == rec_id
    assert resp.json()["item"]["invoice_code"] == "INV-X3-ID1"


def test_get_record_not_found_returns_404() -> None:
    resp = client.get(f"{BASE}/999999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_list_records_returns_items() -> None:
    _create_record("LIST1")
    _create_record("LIST2")

    resp = client.get(BASE, headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["items"]) >= 2


def test_update_status_to_resolved() -> None:
    created = _create_record("ST1")
    assert created.status_code == 200, created.text
    rec_id = created.json()["item"]["id"]

    resp = client.patch(f"{BASE}/{rec_id}/status", headers=ADMIN_HEADERS, json={"status": "resolved"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "resolved"


def test_update_status_not_found_returns_404() -> None:
    resp = client.patch(f"{BASE}/999999/status", headers=ADMIN_HEADERS, json={"status": "resolved"})
    assert resp.status_code == 404


def test_update_escalation_stage() -> None:
    created = _create_record("ESC1")
    assert created.status_code == 200, created.text
    rec_id = created.json()["item"]["id"]

    resp = client.patch(f"{BASE}/{rec_id}/escalation", headers=ADMIN_HEADERS, json={"escalation_stage": "stage_3"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["escalation_stage"] == "stage_3"


def test_update_escalation_not_found_returns_404() -> None:
    resp = client.patch(f"{BASE}/999999/escalation", headers=ADMIN_HEADERS, json={"escalation_stage": "legal"})
    assert resp.status_code == 404


def test_create_record_with_critical_overdue_succeeds() -> None:
    """Records with 90+ days overdue should still create (brain signal fires)."""
    resp = _create_record("CRIT1", days_overdue=120)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["days_overdue"] == 120


def test_list_records_filtered_by_status() -> None:
    _create_record("FILT1", extra={"status": "in_review"})
    _create_record("FILT2", extra={"status": "open"})

    resp = client.get(f"{BASE}?status=in_review", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    for item in resp.json()["items"]:
        assert item["status"] == "in_review"

