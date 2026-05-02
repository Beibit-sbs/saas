"""Phase XXVI — Agent Adaptive Learning & Self-Optimization tests.

XXVI1: Agent learning from outcomes (record signal / get summary)
XXVI2: Agent self-optimization (optimize workflow / get history)
XXVI3: Agent performance benchmarking (benchmark / get benchmark)
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
# XXVI1 — Agent Learning from Outcomes
# ---------------------------------------------------------------------------

class TestXXVI1AgentLearning:
    def test_record_learning_signal_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/learning",
            json={
                "agent_id": "agent-alpha",
                "signal_type": "quality_score",
                "value": 0.85,
                "context": {"step": "review"},
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["agent_id"] == "agent-alpha"
        assert data["signal_type"] == "quality_score"
        assert data["value"] == 0.85
        assert data["total_signals_for_agent"] == 1

    def test_get_agent_learning_summary_aggregates_signals(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        for value in [0.6, 0.8, 1.0]:
            resp = client.post(
                f"/api/admin/brain/agent/tasks/{task_id}/learning",
                json={"agent_id": "agent-beta", "signal_type": "latency_ms", "value": value},
                headers=_headers(),
            )
            assert resp.status_code == 200

        resp = client.get("/api/admin/brain/agent/learning/agent-beta", headers=_headers_read())
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "agent-beta"
        assert data["total_signals"] == 3
        assert "latency_ms" in data["signal_types"]
        assert data["signal_types"]["latency_ms"]["count"] == 3
        assert abs(data["average_value"] - 0.8) < 0.001

    def test_record_signal_missing_task_returns_422(self) -> None:
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/tasks/no-such-task/learning",
            json={"agent_id": "x", "signal_type": "quality", "value": 1.0},
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXVI2 — Agent Self-Optimization
# ---------------------------------------------------------------------------

class TestXXVI2AgentSelfOptimization:
    def test_optimize_workflow_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/optimize",
            json={"optimization_target": "latency", "strategy": "conservative"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["optimization_target"] == "latency"
        assert data["status"] == "applied"
        assert data["strategy"] == "conservative"

    def test_optimize_history_accumulates(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        for target in ["latency", "cost"]:
            client.post(
                f"/api/admin/brain/agent/tasks/{task_id}/optimize",
                json={"optimization_target": target},
                headers=_headers(),
            )

        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/optimize-history",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["total_optimizations"] == 2
        assert len(data["history"]) == 2

    def test_optimize_invalid_target_returns_422(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/optimize",
            json={"optimization_target": "invalid_target"},
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXVI3 — Agent Performance Benchmarking
# ---------------------------------------------------------------------------

class TestXXVI3AgentBenchmarking:
    def test_benchmark_records_improvement(self) -> None:
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/benchmark",
            json={
                "agent_id": "agent-gamma",
                "metric": "latency",
                "observed_value": 120.0,
                "baseline_value": 200.0,
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "agent-gamma"
        assert data["metric"] == "latency"
        assert data["status"] == "improved"
        assert data["delta"] < 0

    def test_get_agent_benchmark_returns_all_metrics(self) -> None:
        _reset()
        for metric, observed, baseline in [
            ("latency", 90.0, 100.0),
            ("quality", 0.92, 0.80),
        ]:
            client.post(
                "/api/admin/brain/agent/benchmark",
                json={
                    "agent_id": "agent-delta",
                    "metric": metric,
                    "observed_value": observed,
                    "baseline_value": baseline,
                },
                headers=_headers(),
            )

        resp = client.get("/api/admin/brain/agent/benchmark/agent-delta", headers=_headers_read())
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "agent-delta"
        assert data["total_metrics"] == 2
        assert "latency" in data["metrics"]
        assert "quality" in data["metrics"]
        assert data["metrics"]["quality"]["status"] == "improved"

    def test_benchmark_regression_detected(self) -> None:
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/benchmark",
            json={
                "agent_id": "agent-epsilon",
                "metric": "throughput",
                "observed_value": 50.0,
                "baseline_value": 100.0,
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "regressed"
        assert data["pct_change"] == -50.0
