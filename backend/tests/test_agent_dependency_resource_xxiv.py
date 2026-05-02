"""Phase XXIV — Agent Dependency & Resource Control tests.

XXIV1: Step dependencies + ready-queue
XXIV2: Task resource budgeting
XXIV3: Outcome feedback + summary
"""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service
from tests.conftest import client


def _headers() -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.dashboard.read", "admin.dashboard.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _headers_read() -> dict[str, str]:
    token = create_access_token(
        user_id="viewer@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.dashboard.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _reset() -> None:
    brain_core_service.__init__()


def _create_task(tenant_id: int = 1) -> dict:
    resp = client.post(
        f"/api/admin/brain/agent/tasks?tenant_id={tenant_id}&workflow_type=intervention_followup",
        headers=_headers(),
    )
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# XXIV1 — Step Dependencies & Ready Queue
# ---------------------------------------------------------------------------

class TestXXIV1StepDependencies:
    def test_set_step_dependencies_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        steps = task["steps"]
        step_a = steps[0]["step_id"]
        step_b = steps[1]["step_id"] if len(steps) > 1 else step_a

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_b}/dependencies",
            json={"depends_on": [step_a]},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["step_id"] == step_b
        assert step_a in data["depends_on"]

    def test_ready_queue_reflects_dependencies(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        steps = task["steps"]
        step_a = steps[0]["step_id"]

        # All steps have no dependencies → all pending steps should be ready
        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/ready-queue",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert "ready_steps" in data
        assert isinstance(data["ready_count"], int)
        # Step A is pending with no deps → must appear in ready queue
        ready_ids = [s["step_id"] for s in data["ready_steps"]]
        assert step_a in ready_ids

    def test_set_dependencies_invalid_dep_returns_422(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step_id = task["steps"][0]["step_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/dependencies",
            json={"depends_on": ["nonexistent-step-xyz"]},
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXIV2 — Task Resource Budgeting
# ---------------------------------------------------------------------------

class TestXXIV2ResourceBudgeting:
    def test_set_resource_budget_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/resources",
            json={"token_limit": 10000, "cost_limit_usd": 2.5},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["token_limit"] == 10000
        assert data["cost_limit_usd"] == 2.5

    def test_get_resource_usage_returns_budget_info(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        # Set budget first
        client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/resources",
            json={"token_limit": 5000, "cost_limit_usd": 1.0},
            headers=_headers(),
        )

        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/resources",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["token_limit"] == 5000
        assert data["cost_limit_usd"] == 1.0
        assert data["budget_set"] is True
        assert data["tokens_used"] == 0
        assert data["cost_usd"] == 0.0

    def test_set_resource_budget_invalid_returns_422(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/resources",
            json={"token_limit": -1, "cost_limit_usd": 0.0},
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXIV3 — Outcome Feedback & Summary
# ---------------------------------------------------------------------------

class TestXXIV3OutcomeFeedback:
    def test_record_outcome_feedback_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/feedback",
            json={"quality_score": 0.85, "notes": "Completed ahead of schedule"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["quality_score"] == 0.85
        assert "recorded_at" in data

    def test_outcome_summary_aggregates_feedback(self) -> None:
        _reset()
        task1 = _create_task(tenant_id=1)
        task2 = _create_task(tenant_id=1)

        client.post(
            f"/api/admin/brain/agent/tasks/{task1['task_id']}/feedback",
            json={"quality_score": 0.9, "notes": ""},
            headers=_headers(),
        )
        client.post(
            f"/api/admin/brain/agent/tasks/{task2['task_id']}/feedback",
            json={"quality_score": 0.7, "notes": "minor issues"},
            headers=_headers(),
        )

        resp = client.get(
            "/api/admin/brain/agent/outcomes/1",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 1
        assert data["tasks_with_feedback"] == 2
        assert data["avg_quality_score"] is not None
        assert 0.79 < data["avg_quality_score"] < 0.81  # avg of 0.9 and 0.7

    def test_record_feedback_invalid_score_returns_422(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/feedback",
            json={"quality_score": 1.5, "notes": "out of range"},
            headers=_headers(),
        )
        assert resp.status_code == 422
