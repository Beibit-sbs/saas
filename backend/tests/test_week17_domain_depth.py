"""Week 17 — Domain Depth: Financial Aid Eligibility Amount-Cap Guard + Disbursement Side Effect.

Tests:
  W17.1 - Source guard: _AID_TYPE_MAX_AMOUNT and _ensure_disbursement_record present
  W17.2 - Stipend above cap (>5000) returns 422
  W17.3 - Approved→Disbursed transition auto-creates financial_aid_disbursements record
  W17.4 - Multiple disbursement calls for same aid record do not duplicate (idempotent)
"""
from __future__ import annotations

import inspect

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/financial-aid"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week17.financialaid@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["financial_aid.read", "financial_aid.write"],
        )
    )
}


def _seed_enrollment(student_id: int, tenant_id: int = 1) -> None:
    """Seed an active enrollment to satisfy Title IV SAP guard."""
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
            "semester": "Spring 2026",
            "status": "active",
            "tenant_id": str(tenant_id),
        }


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("financial_aid_records", "financial_aid_disbursements", "enrollments"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _create_aid_record(aid_type: str, amount: float, term: str = "2026-spring") -> dict:
    _seed_enrollment(42)
    resp = client.post(
        BASE,
        headers=HEADERS,
        json={
            "student_id": 42,
            "aid_type": aid_type,
            "amount": amount,
            "currency": "USD",
            "term": term,
        },
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W17.1 – Source guard
# ---------------------------------------------------------------------------

def test_w17_source_contains_amount_cap_guard_and_disbursement_helper() -> None:
    from app.modules.financial_aid import service as financial_aid_service

    src = inspect.getsource(financial_aid_service)
    assert "_AID_TYPE_MAX_AMOUNT" in src, (
        "_AID_TYPE_MAX_AMOUNT dict must exist in financial_aid service"
    )
    assert "exceeds maximum amount" in src, (
        "Amount cap violation message must be present in service"
    )
    assert "_ensure_disbursement_record" in src, (
        "_ensure_disbursement_record cross-module helper must exist in service"
    )


# ---------------------------------------------------------------------------
# W17.2 – Stipend above cap → 422
# ---------------------------------------------------------------------------

def test_w17_stipend_above_cap_returns_422() -> None:
    _seed_enrollment(10)
    resp = client.post(
        BASE,
        headers=HEADERS,
        json={
            "student_id": 10,
            "aid_type": "stipend",
            "amount": 9999.00,   # max is 5000
            "currency": "USD",
            "term": "2026-spring",
        },
    )
    assert resp.status_code == 422, resp.text
    assert "exceeds maximum amount" in resp.text


# ---------------------------------------------------------------------------
# W17.3 – Disbursed transition auto-creates disbursement record
# ---------------------------------------------------------------------------

def test_w17_disbursement_auto_creates_disbursement_record() -> None:
    from app.modules.university_core import shared as university_shared

    # Create the aid record
    created = _create_aid_record("scholarship", 10_000.00)
    record_id = created["item"]["id"]

    # Approve it first (pending → approved)
    resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=HEADERS,
        json={"status": "approved"},
    )
    assert resp.status_code == 200, resp.text

    # Disburse it (approved → disbursed)
    resp = client.patch(
        f"{BASE}/{record_id}/status",
        headers=HEADERS,
        json={"status": "disbursed"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "disbursed"

    # Verify disbursement record was auto-created
    with university_shared._state_lock:
        disbursements = list(
            university_shared._state.data.get("financial_aid_disbursements", {}).values()
        )

    matching = [
        d for d in disbursements
        if str(d.get("integration_source")) == "financial_aid_disbursement"
        and str(d.get("source_entity_id")) == str(record_id)
    ]
    assert len(matching) == 1, (
        f"Expected exactly 1 disbursement record, got {len(matching)}"
    )
    disb = matching[0]
    assert disb["aid_type"] == "scholarship"
    assert float(disb["amount"]) == 10_000.00
    assert disb["status"] == "processed"


# ---------------------------------------------------------------------------
# W17.4 – Idempotency: calling helper twice does not duplicate record
# ---------------------------------------------------------------------------

def test_w17_repeated_disbursements_do_not_duplicate_record() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.financial_aid.service import _ensure_disbursement_record

    aid_record_id = 99999
    aid_record = {
        "student_id": 7,
        "aid_type": "grant",
        "amount": 5000.0,
        "currency": "USD",
        "term": "2026-fall",
    }

    # Call three times with same aid_record_id
    for _ in range(3):
        _ensure_disbursement_record(1, aid_record_id, aid_record)

    with university_shared._state_lock:
        disbursements = list(
            university_shared._state.data.get("financial_aid_disbursements", {}).values()
        )

    matching = [
        d for d in disbursements
        if str(d.get("integration_source")) == "financial_aid_disbursement"
        and str(d.get("source_entity_id")) == str(aid_record_id)
    ]
    assert len(matching) == 1, (
        f"Idempotency violated: expected 1 disbursement record, got {len(matching)}"
    )
