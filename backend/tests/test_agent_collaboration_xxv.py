"""Phase XXV — Agent Multi-Agent Collaboration & Handoff tests.

XXV1: Agent handoff protocol (initiate / get status / accept)
XXV2: Collaborative task splitting
XXV3: Agent result merge & conflict detection
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
# XXV1 — Agent Handoff Protocol
# ---------------------------------------------------------------------------

class TestXXV1AgentHandoff:
    def test_initiate_handoff_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/handoff/{task_id}",
            json={"to_agent_id": "agent-B", "context_snapshot": {"key": "value"}},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "handoff_id" in data
        assert data["status"] == "pending"
        assert data["to_agent_id"] == "agent-B"

    def test_get_handoff_status_and_accept(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        # Initiate
        init_resp = client.post(
            f"/api/admin/brain/agent/handoff/{task_id}",
            json={"to_agent_id": "agent-C"},
            headers=_headers(),
        )
        assert init_resp.status_code == 200
        handoff_id = init_resp.json()["handoff_id"]

        # Get status — should be pending
        status_resp = client.get(
            f"/api/admin/brain/agent/handoff/{handoff_id}",
            headers=_headers_read(),
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "pending"

        # Accept handoff
        accept_resp = client.post(
            f"/api/admin/brain/agent/handoff/{handoff_id}/accept",
            headers=_headers(),
        )
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "accepted"

    def test_handoff_unknown_task_returns_422(self) -> None:
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/handoff/nonexistent-task-id",
            json={"to_agent_id": "agent-X"},
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXV2 — Collaborative Task Splitting
# ---------------------------------------------------------------------------

class TestXXV2TaskSplitting:
    def test_split_task_creates_subtasks(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/split",
            json={
                "split_strategy": "parallel",
                "subtask_configs": [
                    {"agent_id": "agent-1", "workflow_type": "data_collection"},
                    {"agent_id": "agent-2", "workflow_type": "analysis"},
                ],
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["split_strategy"] == "parallel"
        assert data["subtask_count"] == 2
        assert len(data["subtasks"]) == 2
        sub_ids = [s["subtask_id"] for s in data["subtasks"]]
        assert len(set(sub_ids)) == 2  # unique IDs

    def test_split_task_empty_configs_returns_422(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/split",
            json={"split_strategy": "parallel", "subtask_configs": []},
            headers=_headers(),
        )
        assert resp.status_code == 422

    def test_split_unknown_task_returns_422(self) -> None:
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/tasks/no-such-task/split",
            json={
                "split_strategy": "parallel",
                "subtask_configs": [{"agent_id": "a1"}],
            },
            headers=_headers(),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# XXV3 — Agent Result Merge
# ---------------------------------------------------------------------------

class TestXXV3AgentResultMerge:
    def test_merge_subtasks_success(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        # Split first
        split_resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/split",
            json={
                "split_strategy": "parallel",
                "subtask_configs": [
                    {"agent_id": "a1", "workflow_type": "risk_assessment"},
                    {"agent_id": "a2", "workflow_type": "data_enrichment"},
                ],
            },
            headers=_headers(),
        )
        assert split_resp.status_code == 200
        subtask_ids = [s["subtask_id"] for s in split_resp.json()["subtasks"]]

        # Merge
        merge_resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/merge",
            json={"subtask_ids": subtask_ids},
            headers=_headers(),
        )
        assert merge_resp.status_code == 200
        data = merge_resp.json()
        assert data["task_id"] == task_id
        assert len(data["subtask_results"]) == 2
        assert "conflicts_detected" in data
        assert "resolution" in data

    def test_get_merge_status_after_merge(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        split_resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/split",
            json={
                "split_strategy": "fan_out",
                "subtask_configs": [{"agent_id": "a1"}],
            },
            headers=_headers(),
        )
        sub_ids = [s["subtask_id"] for s in split_resp.json()["subtasks"]]

        client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/merge",
            json={"subtask_ids": sub_ids},
            headers=_headers(),
        )

        status_resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/merge-status",
            headers=_headers_read(),
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["task_id"] == task_id
        assert "merged_at" in data

    def test_get_merge_status_no_merge_returns_404(self) -> None:
        _reset()
        task = _create_task()
        task_id = task["task_id"]

        resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/merge-status",
            headers=_headers_read(),
        )
        assert resp.status_code == 404
