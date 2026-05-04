"""A-011.1 — Brain core payload/path tenant_id validation tests.

Validates that all brain_core simulation and mutation endpoints reject requests
where the payload/path tenant_id does not match the authenticated token's tenant.
"""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client


def _headers(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["admin.dashboard.read", "admin.dashboard.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _reset() -> None:
    from app.modules.brain_core.service import brain_core_service
    brain_core_service.__init__()


# ---------------------------------------------------------------------------
# payload-based: matching tenant_id → 200
# ---------------------------------------------------------------------------

def test_simulate_student_risk_matching_tenant_200() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/simulate/student-risk",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 1,
            "student_id": "STU-VALTEST-001",
            "attendance_rate": 0.55,
            "grade_trend": "declining",
        },
    )
    assert resp.status_code == 200, resp.text


def test_simulate_student_risk_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/simulate/student-risk",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 2,  # mismatch: token has tenant=1
            "student_id": "STU-VALTEST-002",
            "attendance_rate": 0.55,
            "grade_trend": "declining",
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_predict_risk_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/predict",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,  # mismatch
            "event_type": "academic.attendance_risk.detected",
            "entity_id": "STU-PREDICT-VALTEST",
            "history": [{"score": 0.5}],
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_detect_anomalies_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/anomalies",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,  # mismatch
            "metric_name": "attendance_gap_days",
            "values": [2, 3, 19],
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_optimize_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/optimize",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,  # mismatch
            "domain_signals": [],
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_simulate_what_if_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/simulate/what-if",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,  # mismatch
            "event_type": "academic.attendance_risk.detected",
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


# ---------------------------------------------------------------------------
# path-based: matching tenant → 200, mismatched → 403
# ---------------------------------------------------------------------------

def test_list_signals_matching_tenant_200() -> None:
    _reset()
    resp = client.get(
        "/api/admin/brain/tenants/1/signals",
        headers=_headers(tenant_id=1),
    )
    assert resp.status_code == 200, resp.text


def test_list_signals_mismatched_tenant_403() -> None:
    _reset()
    resp = client.get(
        "/api/admin/brain/tenants/2/signals",  # path=2, token=1
        headers=_headers(tenant_id=1),
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_list_decisions_mismatched_tenant_403() -> None:
    _reset()
    resp = client.get(
        "/api/admin/brain/tenants/2/decisions",  # path=2, token=1
        headers=_headers(tenant_id=1),
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


# ---------------------------------------------------------------------------
# misc simulation endpoints: tenant injection denied
# ---------------------------------------------------------------------------

def test_simulate_thesis_delay_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/simulate/thesis-delay",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,
            "student_id": "STU-THESIS-001",
            "thesis_id": "THS-001",
            "days_since_last_milestone": 30,
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_simulate_payment_overdue_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/simulate/payment-overdue",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,
            "student_id": "STU-PAY-001",
            "delinquency_days": 30,
            "balance_due": 1000.0,
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"


def test_apply_learning_mismatched_tenant_403() -> None:
    _reset()
    resp = client.post(
        "/api/admin/brain/learning/apply",
        headers=_headers(tenant_id=1),
        json={
            "tenant_id": 99,
            "actor": "ops@brain",
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "tenant_id_mismatch"
