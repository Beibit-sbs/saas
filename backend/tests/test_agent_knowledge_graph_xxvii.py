"""Phase XXVII — Agent Knowledge Graph & Cross-Agent Memory tests.

XXVII1: Agent knowledge store — store / retrieve with expiry guard
XXVII2: Cross-agent knowledge sharing — conflict detection transition guard
XXVII3: Knowledge expiry & health — time-based business invariant
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


# ---------------------------------------------------------------------------
# XXVII1 — Agent Knowledge Store
# ---------------------------------------------------------------------------

class TestXXVII1AgentKnowledgeStore:
    def test_store_and_retrieve_knowledge_success(self) -> None:
        """Storing a knowledge entry and retrieving it returns correct values."""
        _reset()
        agent_id = "agent-alpha"

        store_resp = client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_id, "key": "risk_threshold", "value": 0.75, "confidence": 0.9},
            headers=_headers(),
        )
        assert store_resp.status_code == 200
        data = store_resp.json()
        assert data["key"] == "risk_threshold"
        assert data["value"] == 0.75
        assert data["confidence"] == 0.9
        assert data["expired"] is False

        get_resp = client.get(
            f"/api/admin/brain/agent/knowledge/{agent_id}/risk_threshold",
            headers=_headers_read(),
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["value"] == 0.75

    def test_retrieve_missing_knowledge_returns_422(self) -> None:
        """Retrieving a non-existent knowledge key returns 422."""
        _reset()
        resp = client.get(
            "/api/admin/brain/agent/knowledge/ghost-agent/no-such-key",
            headers=_headers_read(),
        )
        assert resp.status_code == 422
        assert "knowledge_not_found" in resp.json()["detail"]

    def test_store_invalid_confidence_returns_422(self) -> None:
        """Confidence outside [0, 1] is blocked by the cross-entity invariant."""
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": "agent-beta", "key": "threshold", "value": 0.5, "confidence": 1.5},
            headers=_headers(),
        )
        assert resp.status_code == 422
        assert "confidence" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# XXVII2 — Cross-Agent Knowledge Sharing (conflict guard)
# ---------------------------------------------------------------------------

class TestXXVII2CrossAgentKnowledgeSharing:
    def test_share_knowledge_propagates_to_target(self) -> None:
        """Sharing knowledge from agent A to agent B propagates the value."""
        _reset()
        agent_a = "agent-sender"
        agent_b = "agent-receiver"

        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_a, "key": "intervention_threshold", "value": 0.6, "confidence": 0.85},
            headers=_headers(),
        )

        share_resp = client.post(
            "/api/admin/brain/agent/knowledge/share",
            json={"from_agent_id": agent_a, "to_agent_id": agent_b, "key": "intervention_threshold"},
            headers=_headers(),
        )
        assert share_resp.status_code == 200
        data = share_resp.json()
        assert data["conflict_detected"] is False
        assert data["value"] == 0.6

        # Verify knowledge now accessible from agent B
        get_resp = client.get(
            f"/api/admin/brain/agent/knowledge/{agent_b}/intervention_threshold",
            headers=_headers_read(),
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["value"] == 0.6

    def test_share_knowledge_conflict_blocks_overwrite(self) -> None:
        """Transition guard: conflicting values block propagation, conflict recorded."""
        _reset()
        agent_a = "agent-src"
        agent_b = "agent-dst"

        # Store different values for same key in both agents
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_a, "key": "risk_cap", "value": 0.8, "confidence": 0.9},
            headers=_headers(),
        )
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_b, "key": "risk_cap", "value": 0.5, "confidence": 0.7},
            headers=_headers(),
        )

        share_resp = client.post(
            "/api/admin/brain/agent/knowledge/share",
            json={"from_agent_id": agent_a, "to_agent_id": agent_b, "key": "risk_cap"},
            headers=_headers(),
        )
        assert share_resp.status_code == 200
        data = share_resp.json()
        assert data["conflict_detected"] is True
        assert data["conflict_detail"]["from_value"] == 0.8
        assert data["conflict_detail"]["to_existing_value"] == 0.5

        # Target value must NOT be overwritten
        get_resp = client.get(
            f"/api/admin/brain/agent/knowledge/{agent_b}/risk_cap",
            headers=_headers_read(),
        )
        assert get_resp.json()["value"] == 0.5  # unchanged

    def test_get_shared_knowledge_lists_conflicts(self) -> None:
        """get_shared_knowledge aggregates total and conflict count."""
        _reset()
        agent_a, agent_b = "src-x", "dst-x"

        # Share clean
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_a, "key": "alpha", "value": 1, "confidence": 0.9},
            headers=_headers(),
        )
        client.post(
            "/api/admin/brain/agent/knowledge/share",
            json={"from_agent_id": agent_a, "to_agent_id": agent_b, "key": "alpha"},
            headers=_headers(),
        )

        # Share with conflict
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_b, "key": "beta", "value": 99, "confidence": 0.8},
            headers=_headers(),
        )
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_a, "key": "beta", "value": 42, "confidence": 0.8},
            headers=_headers(),
        )
        client.post(
            "/api/admin/brain/agent/knowledge/share",
            json={"from_agent_id": agent_a, "to_agent_id": agent_b, "key": "beta"},
            headers=_headers(),
        )

        resp = client.get(
            f"/api/admin/brain/agent/knowledge/{agent_b}/shared",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["conflicts"] == 1


# ---------------------------------------------------------------------------
# XXVII3 — Knowledge Expiry & Health (time-based business invariant)
# ---------------------------------------------------------------------------

class TestXXVII3KnowledgeExpiryHealth:
    def test_expire_returns_zero_for_fresh_entries(self) -> None:
        """Fresh entries are not expired even with a reasonable TTL."""
        _reset()
        agent_id = "agent-fresh"
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_id, "key": "limit", "value": 100, "confidence": 0.9},
            headers=_headers(),
        )

        # max_age_hours=24 — a fresh entry (just stored) should not expire
        resp = client.post(
            f"/api/admin/brain/agent/knowledge/{agent_id}/expire",
            json={"max_age_hours": 24},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["expired_count"] == 0

    def test_expire_with_zero_ttl_returns_422(self) -> None:
        """max_age_hours=0 is an invalid business invariant — must return 422."""
        _reset()
        resp = client.post(
            "/api/admin/brain/agent/knowledge/some-agent/expire",
            json={"max_age_hours": 0},
            headers=_headers(),
        )
        assert resp.status_code == 422

    def test_knowledge_health_reflects_low_confidence(self) -> None:
        """Entries with confidence < 0.5 degrade health status."""
        _reset()
        agent_id = "agent-lowconf"
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_id, "key": "fragile_rule", "value": "maybe", "confidence": 0.3},
            headers=_headers(),
        )
        client.post(
            "/api/admin/brain/agent/knowledge",
            json={"agent_id": agent_id, "key": "solid_rule", "value": "yes", "confidence": 0.95},
            headers=_headers(),
        )

        resp = client.get(
            f"/api/admin/brain/agent/knowledge/{agent_id}/health",
            headers=_headers_read(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] == 2
        assert data["low_confidence_entries"] == 1
        assert data["health"] == "degraded"
