"""Week 24 — Domain Depth: Expense Controls Approval/Policy Engine.

Tests:
  W24.1 - Source guard: _EXPENSE_CATEGORY_MAX_ACTIVE and _ensure_expense_policy_review_record present
  W24.2 - Exceeding active 'equipment' expense cap returns 422
  W24.3 - Creating a high-value expense (>=5000) auto-creates expense_policy_review_records entry
  W24.4 - Multiple _ensure_expense_policy_review_record calls for same record are idempotent
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/expense-controls"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week24.expense@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["finance.read", "finance.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("expense_records", "cost_centers", "expense_policy_review_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_cost_center(budget_limit: float = 999999.0) -> dict:
    payload = {
        "name": f"CC-{_uid()}",
        "code": f"CC{_uid()}",
        "budget_limit": budget_limit,
        "currency": "USD",
        "active": True,
    }
    resp = client.post(f"{BASE}/cost-centers", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["record"]


def _create_expense(cost_center_id: int, category: str = "equipment", amount: float = 100.0) -> dict:
    payload = {
        "cost_center_id": cost_center_id,
        "category": category,
        "amount": amount,
        "currency": "USD",
        "status": "pending",
    }
    resp = client.post(f"{BASE}/expenses", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W24.1 – Source guard
# ---------------------------------------------------------------------------

def test_w24_source_contains_category_cap_and_policy_helper() -> None:
    from app.modules.expense_controls import service as ec_service

    src = inspect.getsource(ec_service)
    assert "_EXPENSE_CATEGORY_MAX_ACTIVE" in src, (
        "_EXPENSE_CATEGORY_MAX_ACTIVE dict must exist in expense_controls service"
    )
    assert "_ensure_expense_policy_review_record" in src, (
        "_ensure_expense_policy_review_record helper must exist in expense_controls service"
    )


# ---------------------------------------------------------------------------
# W24.2 – Cap guard: exceeding active 'equipment' expenses → 422
# ---------------------------------------------------------------------------

def test_w24_equipment_cap_exceeded_returns_422() -> None:
    """equipment max=2; third pending expense must return 422."""
    cc = _create_cost_center()
    cc_id = int(cc["id"])
    # create 2 equipment records (cap=2)
    _create_expense(cc_id, category="equipment", amount=100.0)
    _create_expense(cc_id, category="equipment", amount=100.0)
    # third must fail
    payload = {
        "cost_center_id": cc_id,
        "category": "equipment",
        "amount": 100.0,
        "currency": "USD",
        "status": "pending",
    }
    resp = client.post(f"{BASE}/expenses", headers=HEADERS, json=payload)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "cap exceeded" in resp.text.lower() or "equipment" in resp.text.lower()


# ---------------------------------------------------------------------------
# W24.3 – High-value expense auto-creates policy review record
# ---------------------------------------------------------------------------

def test_w24_high_value_expense_creates_policy_review_record() -> None:
    """Creating an expense with amount>=5000 should auto-create a policy review record."""
    from app.modules.university_core import shared as university_shared

    cc = _create_cost_center(budget_limit=999999.0)
    cc_id = int(cc["id"])

    _create_expense(cc_id, category="travel", amount=6000.0)

    with university_shared._state_lock:
        reviews = list(
            university_shared._state.data.get("expense_policy_review_records", {}).values()
        )
    assert len(reviews) >= 1, "Policy review record should be auto-created for high-value expense"
    assert any(r.get("integration_source") == "expense_policy" for r in reviews)


# ---------------------------------------------------------------------------
# W24.4 – Idempotency of _ensure_expense_policy_review_record
# ---------------------------------------------------------------------------

def test_w24_policy_review_record_is_idempotent() -> None:
    """Calling _ensure_expense_policy_review_record multiple times for same record → exactly 1 entry."""
    from app.modules.expense_controls.service import _ensure_expense_policy_review_record
    from app.modules.university_core import shared as university_shared

    fake_record = {"id": "9999", "category": "travel", "cost_center_id": "1", "amount": 8000.0}
    tenant_id = 1

    _ensure_expense_policy_review_record(fake_record, tenant_id)
    _ensure_expense_policy_review_record(fake_record, tenant_id)
    _ensure_expense_policy_review_record(fake_record, tenant_id)

    with university_shared._state_lock:
        reviews = [
            r for r in university_shared._state.data.get("expense_policy_review_records", {}).values()
            if str(r.get("source_entity_id") or "") == "9999"
            and str(r.get("integration_source") or "") == "expense_policy"
        ]
    assert len(reviews) == 1, f"Expected exactly 1 review record, got {len(reviews)}"
