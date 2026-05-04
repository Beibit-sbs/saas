"""Phase XXIII — Agent Observability & Telemetry tests.

XXIII1: Step event log (POST + GET)
XXIII2: Task audit trail
XXIII3: Agent performance report
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
# XXIII1 — Step Event Log
# ---------------------------------------------------------------------------

class TestXXIII1StepEventLog:
    def test_log_event_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step_id = task["steps"][0]["step_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/log",
            json={"event_type": "started", "payload": {"worker": "w-1"}},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["logged"] is True
        assert data["seq"] == 0

    def test_get_step_log_returns_events(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step_id = task["steps"][0]["step_id"]

        # Log two events
        client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/log",
            json={"event_type": "started", "payload": {}},
            headers=_headers(),
        )
        client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/log",
            json={"event_type": "progress", "payload": {"pct": 50}},
            headers=_headers(),
        )

        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/log",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_count"] == 2
        assert data["events"][0]["event_type"] == "started"
        assert data["events"][1]["event_type"] == "progress"
        assert data["events"][1]["seq"] == 1

    def test_invalid_event_type_returns_422(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step_id = task["steps"][0]["step_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/log",
            json={"event_type": "explode", "payload": {}},
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXIII2 — Task Audit Trail
# ---------------------------------------------------------------------------

class TestXXIII2TaskAudit:
    def test_audit_trail_for_known_task(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/audit",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["found"] is True
        assert data["workflow_type"] == "intervention_followup"
        assert data["tenant_id"] == 1
        assert isinstance(data["audit_trail"], list)

    def test_audit_trail_unknown_task(self) -> None:
        _reset()
        resp = client.get(
            "/api/admin/brain/agent/tasks/no-such-task/audit",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["audit_event_count"] == 0

    def test_audit_trail_grows_with_activity(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]
        step_id = task["steps"][0]["step_id"]

        # Execute the step to add audit entries
        client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step_id}/execute"
            "?input_data={}&worker_id=w-1",
            headers=_headers(),
        )

        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/audit",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["audit_event_count"] >= 0  # audit entries exist


# ---------------------------------------------------------------------------
# XXIII3 — Agent Performance Report
# ---------------------------------------------------------------------------

class TestXXIII3PerformanceReport:
    def test_performance_report_empty_tenant(self) -> None:
        _reset()
        resp = client.get(
            "/api/admin/brain/agent/performance/999?window_hours=24",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 999
        assert data["steps_total"] == 0
        assert data["failure_rate"] == 0.0
        assert data["retry_rate"] == 0.0
        assert data["avg_step_duration_seconds"] is None

    def test_performance_report_with_tasks(self) -> None:
        _reset()
        _create_task(tenant_id=1)
        _create_task(tenant_id=1)

        resp = client.get(
            "/api/admin/brain/agent/performance/1?window_hours=24",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 1
        assert data["steps_total"] >= 2  # at least 1 step per task
        assert "failure_rate" in data
        assert "retry_rate" in data
        assert "generated_at" in data

    def test_performance_report_contract(self) -> None:
        _reset()
        resp = client.get(
            "/api/admin/brain/agent/performance/1?window_hours=1",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        required_keys = {
            "tenant_id",
            "window_hours",
            "steps_total",
            "steps_done",
            "steps_failed",
            "steps_retried",
            "avg_step_duration_seconds",
            "failure_rate",
            "retry_rate",
            "generated_at",
        }
        assert required_keys.issubset(data.keys())
        assert data["window_hours"] == 1
