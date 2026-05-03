"""Phase LXXVI — Plans Management Router tests (20 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.plans.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

MODULE = "app.modules.plans.router"


# ─── helpers ──────────────────────────────────────────────────────────────────


def _plan(
    id_: int = 1,
    code: str = "free",
    name: str = "Free",
    description: str = "Starter plan",
    active: bool = True,
) -> dict:
    return {"id": id_, "code": code, "name": name, "description": description, "active": active}


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/billing/plans — list_all_plans
# ═══════════════════════════════════════════════════════════════════════════════


def test_list_plans_returns_active_only_by_default():
    active_rows = [_plan(1, "free", "Free"), _plan(2, "pro", "Pro")]
    with patch(f"{MODULE}.list_plans", return_value=active_rows) as mock:
        resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["plans"]) == 2
    assert body["plans"][0]["code"] == "free"
    mock.assert_called_once_with(include_inactive=False)


def test_list_plans_include_inactive_true():
    all_rows = [_plan(1), _plan(2, "old", "Old Plan", active=False)]
    with patch(f"{MODULE}.list_plans", return_value=all_rows) as mock:
        resp = client.get("/api/billing/plans?include_inactive=true")
    assert resp.status_code == 200
    assert len(resp.json()["plans"]) == 2
    mock.assert_called_once_with(include_inactive=True)


def test_list_plans_empty_list():
    with patch(f"{MODULE}.list_plans", return_value=[]):
        resp = client.get("/api/billing/plans")
    assert resp.status_code == 200
    assert resp.json()["plans"] == []


def test_list_plans_response_shape():
    rows = [_plan(1, "basic", "Basic", "Entry plan")]
    with patch(f"{MODULE}.list_plans", return_value=rows):
        resp = client.get("/api/billing/plans")
    plan = resp.json()["plans"][0]
    assert set(plan.keys()) == {"id", "code", "name", "description", "active"}


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/billing/plans — create_new_plan
# ═══════════════════════════════════════════════════════════════════════════════


def test_create_plan_success():
    new_row = _plan(5, "enterprise", "Enterprise", "Enterprise plan")
    with patch(f"{MODULE}.create_plan", return_value=new_row) as mock:
        resp = client.post(
            "/api/billing/plans",
            json={"code": "enterprise", "name": "Enterprise", "description": "Enterprise plan"},
        )
    assert resp.status_code == 201
    assert resp.json()["plan"]["code"] == "enterprise"
    mock.assert_called_once()


def test_create_plan_duplicate_code_returns_400():
    with patch(f"{MODULE}.create_plan", side_effect=ValueError("plan code already exists")):
        resp = client.post(
            "/api/billing/plans",
            json={"code": "free", "name": "Free Duplicate"},
        )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_create_plan_missing_required_fields_returns_422():
    resp = client.post("/api/billing/plans", json={"description": "no code or name"})
    assert resp.status_code == 422


def test_create_plan_returns_plan_wrapper():
    new_row = _plan(10, "starter", "Starter")
    with patch(f"{MODULE}.create_plan", return_value=new_row):
        resp = client.post("/api/billing/plans", json={"code": "starter", "name": "Starter"})
    assert resp.status_code == 201
    body = resp.json()
    assert "plan" in body
    assert body["plan"]["id"] == 10


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/billing/plans/stats — get_plans_stats
# ═══════════════════════════════════════════════════════════════════════════════


def test_stats_returns_counts():
    all_rows = [_plan(1), _plan(2), _plan(3, active=False)]
    with patch(f"{MODULE}.list_plans", return_value=all_rows):
        resp = client.get("/api/billing/plans/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["active"] == 2
    assert body["inactive"] == 1


def test_stats_all_active():
    rows = [_plan(1), _plan(2), _plan(3), _plan(4)]
    with patch(f"{MODULE}.list_plans", return_value=rows):
        resp = client.get("/api/billing/plans/stats")
    body = resp.json()
    assert body["total"] == 4
    assert body["inactive"] == 0


def test_stats_empty():
    with patch(f"{MODULE}.list_plans", return_value=[]):
        resp = client.get("/api/billing/plans/stats")
    body = resp.json()
    assert body == {"total": 0, "active": 0, "inactive": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/billing/plans/{plan_id} — get_plan
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_plan_by_id_success():
    row = _plan(1, "free", "Free")
    with patch(f"{MODULE}.get_plan_by_id", return_value=row):
        resp = client.get("/api/billing/plans/1")
    assert resp.status_code == 200
    assert resp.json()["plan"]["code"] == "free"


def test_get_plan_not_found_returns_404():
    with patch(f"{MODULE}.get_plan_by_id", return_value=None):
        resp = client.get("/api/billing/plans/999")
    assert resp.status_code == 404


def test_get_plan_invalid_id_rejected():
    resp = client.get("/api/billing/plans/0")
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# PATCH /api/billing/plans/{plan_id} — update_existing_plan
# ═══════════════════════════════════════════════════════════════════════════════


def test_update_plan_success():
    existing = _plan(1, "free", "Free Old")
    updated = _plan(1, "free", "Free Updated")
    with patch(f"{MODULE}.get_plan_by_id", return_value=existing):
        with patch(f"{MODULE}.update_plan", return_value=updated):
            resp = client.patch("/api/billing/plans/1", json={"name": "Free Updated"})
    assert resp.status_code == 200
    assert resp.json()["plan"]["name"] == "Free Updated"


def test_update_plan_not_found_returns_404():
    with patch(f"{MODULE}.get_plan_by_id", return_value=None):
        resp = client.patch("/api/billing/plans/999", json={"name": "New"})
    assert resp.status_code == 404


def test_update_plan_invalid_id_returns_422():
    resp = client.patch("/api/billing/plans/0", json={"name": "New"})
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /api/billing/plans/{plan_id} — deactivate_plan
# ═══════════════════════════════════════════════════════════════════════════════


def test_deactivate_plan_success():
    active_plan = _plan(1, "free", "Free", active=True)
    with patch(f"{MODULE}.get_plan_by_id", return_value=active_plan):
        with patch(f"{MODULE}.update_plan", return_value={**active_plan, "active": False}):
            resp = client.delete("/api/billing/plans/1")
    assert resp.status_code == 204


def test_deactivate_plan_not_found_returns_404():
    with patch(f"{MODULE}.get_plan_by_id", return_value=None):
        resp = client.delete("/api/billing/plans/999")
    assert resp.status_code == 404


def test_deactivate_plan_already_inactive_returns_409():
    inactive_plan = _plan(1, "free", "Free", active=False)
    with patch(f"{MODULE}.get_plan_by_id", return_value=inactive_plan):
        resp = client.delete("/api/billing/plans/1")
    assert resp.status_code == 409


def test_deactivate_plan_invalid_id_returns_422():
    resp = client.delete("/api/billing/plans/0")
    assert resp.status_code == 422
