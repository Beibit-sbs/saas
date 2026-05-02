"""Phase XXII — Agent Execution Governance tests.

XXII1: Queue claim API
XXII2: Step complete/fail with retry policy
XXII3: SLA breach reporting
XXII4: Queue metrics endpoint
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

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


def _headers_read_only() -> dict[str, str]:
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


def _create_task() -> dict:
    resp = client.post(
        "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=intervention_followup",
        headers=_headers(),
    )
    assert resp.status_code == 200
    return resp.json()


class TestXXII1QueueClaim:
    def test_claim_next_step_success(self):
        _reset()
        _create_task()

        resp = client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "claimed"
        assert data["worker_id"] == "worker-a"
        assert data["step_name"] == "assess"

    def test_claim_none_available(self):
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "none_available"

    def test_claim_dependency_enforced(self):
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step0 = task["steps"][0]["step_id"]

        # Claim step0 and complete it, then step1 should become claimable
        claim1 = client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )
        assert claim1.json()["step_id"] == step0

        complete = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step0}/complete?worker_id=worker-a&success=true",
            headers=_headers(),
        )
        assert complete.status_code == 200
        assert complete.json()["status"] == "completed"

        claim2 = client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-b",
            headers=_headers(),
        )
        assert claim2.status_code == 200
        assert claim2.json()["step_name"] == "act"


class TestXXII2CompletionRetry:
    def test_complete_step_success(self):
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        claim = client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        ).json()

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{claim['step_id']}/complete?worker_id=worker-a&success=true",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["step_status"] == "done"

    def test_complete_step_retry_then_blocked(self):
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step0 = task["steps"][0]["step_id"]

        # Claim once
        client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )

        # Fail 3 times (max_retries=2 -> blocked on third)
        r1 = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step0}/complete?worker_id=worker-a&success=false&error_code=e1",
            headers=_headers(),
        ).json()
        assert r1["status"] == "failed"
        assert r1["step_status"] == "pending"

        client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )
        r2 = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step0}/complete?worker_id=worker-a&success=false&error_code=e2",
            headers=_headers(),
        ).json()
        assert r2["step_status"] == "pending"

        client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )
        r3 = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step0}/complete?worker_id=worker-a&success=false&error_code=e3",
            headers=_headers(),
        ).json()
        assert r3["step_status"] == "blocked"
        assert r3["retry_count"] == 3

    def test_complete_not_running(self):
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step0 = task["steps"][0]["step_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step0}/complete?worker_id=worker-a&success=true",
            headers=_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_running"


class TestXXII3SlaAndQueue:
    def test_sla_report_no_breach(self):
        _reset()
        _create_task()

        resp = client.get("/api/admin/brain/agent/sla/1?sla_seconds=300", headers=_headers_read_only())
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 1
        assert data["breach_count"] == 0

    def test_sla_report_detects_breach(self):
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step0 = task["steps"][0]["step_id"]

        # Claim step then manually backdate started_at to trigger breach
        client.post(
            "/api/admin/brain/agent/tasks/claim?tenant_id=1&worker_id=worker-a",
            headers=_headers(),
        )
        status = brain_core_service.get_agent_task_status(task_id)
        step = next(s for s in status["steps"] if s["step_id"] == step0)
        step["started_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1000)).isoformat()

        resp = client.get("/api/admin/brain/agent/sla/1?sla_seconds=300", headers=_headers_read_only())
        assert resp.status_code == 200
        data = resp.json()
        assert data["breach_count"] >= 1
        assert any(b["step_id"] == step0 for b in data["breaches"])

    def test_queue_metrics_contract(self):
        _reset()
        _create_task()
        resp = client.get("/api/admin/brain/agent/queue/1", headers=_headers_read_only())
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 1
        assert data["tasks_total"] == 1
        assert "steps_pending" in data
        assert "steps_running" in data
        assert "steps_done" in data
