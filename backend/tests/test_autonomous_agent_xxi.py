"""Phase XXI — Autonomous Agent Workflows & Self-Governance tests.

XXI1: Agent Task Orchestrator — create_task, invalid workflow type
XXI2: Agent Workflow Execution — execute_step, blocked dependency, task_not_found
XXI3: Agent Self-Correction — blocked step triggers alternative path
XXI4: Tenant Agent Policy — get/update, invalid workflow type rejection
"""
from __future__ import annotations

import pytest

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


# ---------------------------------------------------------------------------
# XXI1 — Agent Task Orchestrator
# ---------------------------------------------------------------------------

class TestXXI1AgentTaskOrchestrator:
    def test_create_task_valid_workflow(self):
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=intervention_followup",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] is not None
        assert data["workflow_type"] == "intervention_followup"
        assert data["status"] == "pending"
        assert len(data["steps"]) == 3
        assert data["steps"][0]["name"] == "assess"
        assert data["steps"][0]["status"] == "pending"

    def test_create_task_invalid_workflow_type(self):
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=nonexistent_type",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "invalid_workflow_type"
        assert data["task_id"] is None

    def test_create_task_step_graph_dependencies(self):
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=policy_remediation",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        steps = data["steps"]
        # First step has no deps; subsequent steps depend on previous
        assert steps[0]["depends_on"] == []
        assert len(steps[1]["depends_on"]) == 1
        assert len(steps[2]["depends_on"]) == 1


# ---------------------------------------------------------------------------
# XXI2 — Agent Workflow Execution
# ---------------------------------------------------------------------------

class TestXXI2AgentWorkflowExecution:
    def test_execute_step_sequential_success(self):
        _reset()
        # Create task
        create_resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=compliance_audit",
            headers=_headers(),
        )
        assert create_resp.status_code == 200
        task = create_resp.json()
        task_id = task["task_id"]
        step0_id = task["steps"][0]["step_id"]

        # Execute first step (no deps → should succeed)
        exec_resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step0_id}/execute",
            headers=_headers(),
        )
        assert exec_resp.status_code == 200
        result = exec_resp.json()
        assert result["status"] == "done"
        assert result["step_name"] == "assess"

    def test_execute_step_blocked_by_dependency(self):
        _reset()
        # Create task
        create_resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=risk_escalation",
            headers=_headers(),
        )
        task = create_resp.json()
        task_id = task["task_id"]
        step1_id = task["steps"][1]["step_id"]  # depends on step 0

        # Try to execute step 1 without executing step 0 first
        exec_resp = client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step1_id}/execute",
            headers=_headers(),
        )
        assert exec_resp.status_code == 200
        result = exec_resp.json()
        assert result["status"] == "blocked"
        assert "blocked_by" in result

    def test_execute_step_task_not_found(self):
        _reset()
        exec_resp = client.post(
            "/api/admin/brain/agent/tasks/nonexistent-task-id/steps/fake-step/execute",
            headers=_headers(),
        )
        assert exec_resp.status_code == 200
        result = exec_resp.json()
        assert result["status"] == "task_not_found"


# ---------------------------------------------------------------------------
# XXI3 — Agent Self-Correction
# ---------------------------------------------------------------------------

class TestXXI3AgentSelfCorrection:
    def test_get_status_no_blocks(self):
        _reset()
        # Create and execute all steps
        create_resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=onboarding_sequence",
            headers=_headers(),
        )
        task = create_resp.json()
        task_id = task["task_id"]

        # Execute all 3 steps in order
        for step in task["steps"]:
            client.post(
                f"/api/admin/brain/agent/tasks/{task_id}/steps/{step['step_id']}/execute",
                headers=_headers(),
            )

        status_resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/status",
            headers=_headers_read_only(),
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["status"] == "done"
        assert data["correction_applied"] is False

    def test_self_correction_applied_on_blocked_step(self):
        _reset()
        create_resp = client.post(
            "/api/admin/brain/agent/tasks?tenant_id=1&workflow_type=intervention_followup",
            headers=_headers(),
        )
        task = create_resp.json()
        task_id = task["task_id"]
        step1_id = task["steps"][1]["step_id"]

        # Force step 1 into blocked state by trying to execute without prereq
        client.post(
            f"/api/admin/brain/agent/tasks/{task_id}/steps/{step1_id}/execute",
            headers=_headers(),
        )

        # Now get status — self-correction should be applied
        status_resp = client.get(
            f"/api/admin/brain/agent/tasks/{task_id}/status",
            headers=_headers_read_only(),
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["correction_applied"] is True
        assert data["status"] == "self_correcting"
        # The blocked step should now be corrected_pending
        corrected = [s for s in data["steps"] if s["status"] == "corrected_pending"]
        assert len(corrected) >= 1

    def test_get_status_task_not_found(self):
        _reset()
        status_resp = client.get(
            "/api/admin/brain/agent/tasks/nonexistent-id/status",
            headers=_headers_read_only(),
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["status"] == "task_not_found"


# ---------------------------------------------------------------------------
# XXI4 — Tenant Agent Policy
# ---------------------------------------------------------------------------

class TestXXI4TenantAgentPolicy:
    def test_get_default_policy(self):
        _reset()
        resp = client.get(
            "/api/admin/brain/agent/policy/1",
            headers=_headers_read_only(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 1
        assert isinstance(data["allowed_workflow_types"], list)
        assert len(data["allowed_workflow_types"]) > 0
        assert "step_budget" in data
        assert data["policy_version"] == "v1"

    def test_update_policy_valid(self):
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/policy/1"
            "?approval_gate_required=true&step_budget=5"
            "&workflow_types=intervention_followup&workflow_types=risk_escalation",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["approval_gate_required"] is True
        assert data["step_budget"] == 5
        assert "intervention_followup" in data["allowed_workflow_types"]

    def test_update_policy_invalid_workflow_type(self):
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/policy/1"
            "?approval_gate_required=false&step_budget=10"
            "&workflow_types=totally_made_up_type",
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "invalid_workflow_type"
        assert "totally_made_up_type" in data["unknown_types"]
