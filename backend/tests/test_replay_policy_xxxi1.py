"""Phase XXXI — Replay Policy Configuration & Tenant-Scoped Governance Settings: backend tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service
from app.modules.tenants import service as tenant_service
from tests.conftest import client


def _headers(tenant_id: int = 1) -> dict[str, str]:
    """Create admin headers scoped to the given tenant_id.

    A-011 added _assert_tenant_match to set_replay_policy; callers must use a
    token whose tenant_id matches the policy tenant_id they are updating.
    """
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["admin.dashboard.read", "admin.dashboard.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _reset() -> None:
    brain_core_service.__init__()


def _create_tenant(prefix: str) -> int:
    tenant = tenant_service.create_tenant({
        "slug": f"{prefix}",
        "name": f"{prefix} tenant",
    })
    return int(tenant["id"])


def _seed_signal(signal_id: str, tenant_id: int = 1) -> None:
    brain_core_service.process_signal(
        {
            "signal_id": signal_id,
            "tenant_id": tenant_id,
            "correlation_id": f"corr-{signal_id}",
            "event_type": "academic.attendance_risk.detected",
            "subject": {"student_id": "S-1", "course_id": "C-1"},
            "payload": {
                "student_id": "S-1",
                "course_id": "C-1",
                "attendance_rate": 0.42,
                "grade_trend": "declining",
                "source_entity_type": "section_attendance",
                "source_entity_id": signal_id,
            },
            "metadata": {"source": "xxxi1-test"},
        }
    )


# ── XXXI1 — Policy Config API ──────────────────────────────────────────────

class TestReplayPolicyConfigXXXI1:
    """XXXI1 — GET/PUT /api/admin/brain/reprocess/policy/{tenant_id}"""

    def test_get_policy_returns_defaults_when_not_set(self) -> None:
        _reset()
        resp = client.get("/api/admin/brain/reprocess/policy/99", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == 99
        assert data["max_window_days"] == 90
        assert data["require_dual_approval"] is False
        assert data["max_replays_per_signal"] == 5

    def test_put_policy_persists_and_returns_config(self) -> None:
        _reset()
        tenant_id = _create_tenant("replay-policy-put")
        payload = {
            "actor": "admin@example.com",
            "max_window_days": 30,
            "allowed_actors": ["op1@example.com", "op2@example.com"],
            "auto_reject_threshold": 0.7,
            "require_dual_approval": True,
            "max_replays_per_signal": 3,
        }
        resp = client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_id}",
            json=payload,
            headers=_headers(tenant_id=tenant_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == tenant_id
        assert data["max_window_days"] == 30
        assert data["allowed_actors"] == ["op1@example.com", "op2@example.com"]
        assert data["auto_reject_threshold"] == 0.7
        assert data["require_dual_approval"] is True
        assert data["max_replays_per_signal"] == 3

    def test_get_policy_reflects_put(self) -> None:
        _reset()
        tenant_id = _create_tenant("replay-policy-get")
        payload = {
            "actor": "admin@example.com",
            "max_window_days": 60,
            "allowed_actors": None,
            "auto_reject_threshold": None,
            "require_dual_approval": False,
            "max_replays_per_signal": 10,
        }
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_id}",
            json=payload,
            headers=_headers(tenant_id=tenant_id),
        )
        resp = client.get(f"/api/admin/brain/reprocess/policy/{tenant_id}", headers=_headers(tenant_id=tenant_id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == tenant_id
        assert data["max_window_days"] == 60
        assert data["max_replays_per_signal"] == 10


# ── XXXI2 — Policy Enforcement Check ──────────────────────────────────────

class TestReplayPolicyEnforcementXXXI2:
    """XXXI2 — GET /api/admin/brain/reprocess/policy/{tenant_id}/check"""

    def test_check_allowed_when_no_restrictions(self) -> None:
        _reset()
        resp = client.get(
            "/api/admin/brain/reprocess/policy/10/check",
            params={"actor": "anyone@example.com", "signal_id": "sig-check-1"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["allowed"] is True

    def test_check_denied_when_actor_not_in_whitelist(self) -> None:
        _reset()
        tenant_id = _create_tenant("replay-policy-whitelist")
        payload = {
            "actor": "admin@example.com",
            "max_window_days": 90,
            "allowed_actors": ["allowed@example.com"],
            "auto_reject_threshold": None,
            "require_dual_approval": False,
            "max_replays_per_signal": 5,
        }
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_id}",
            json=payload,
            headers=_headers(tenant_id=tenant_id),
        )
        resp = client.get(
            f"/api/admin/brain/reprocess/policy/{tenant_id}/check",
            params={"actor": "notallowed@example.com", "signal_id": "sig-check-2"},
            headers=_headers(tenant_id=tenant_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["allowed"] is False
        assert "allowed_actors" in data["reason"]

    def test_check_denied_when_max_replays_exceeded(self) -> None:
        _reset()
        tenant_id = _create_tenant("replay-policy-max-replays")
        # Set policy with max_replays_per_signal=1
        payload = {
            "actor": "admin@example.com",
            "max_window_days": 90,
            "allowed_actors": None,
            "auto_reject_threshold": None,
            "require_dual_approval": False,
            "max_replays_per_signal": 1,
        }
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_id}",
            json=payload,
            headers=_headers(tenant_id=tenant_id),
        )

        # Seed signal and approve once (counts as 1 replay)
        _seed_signal("sig-limit-1", tenant_id=tenant_id)
        brain_core_service.approve_signal_reprocess("sig-limit-1", actor="op@example.com", reason="first")

        # Now check — should be denied
        resp = client.get(
            f"/api/admin/brain/reprocess/policy/{tenant_id}/check",
            params={"actor": "op@example.com", "signal_id": "sig-limit-1"},
            headers=_headers(tenant_id=tenant_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["allowed"] is False
        assert "max_replays_per_signal" in data["reason"]


# ── XXXI3 — Policy History & Audit ────────────────────────────────────────

class TestReplayPolicyHistoryXXXI3:
    """XXXI3 — GET /api/admin/brain/reprocess/policy/{tenant_id}/history"""

    def test_history_empty_before_any_set(self) -> None:
        _reset()
        resp = client.get("/api/admin/brain/reprocess/policy/20/history", headers=_headers())
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_records_each_policy_update(self) -> None:
        _reset()
        tenant_id = _create_tenant("replay-policy-history")
        base_payload = {
            "actor": "admin@example.com",
            "max_window_days": 90,
            "allowed_actors": None,
            "auto_reject_threshold": None,
            "require_dual_approval": False,
            "max_replays_per_signal": 5,
        }
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_id}",
            json=base_payload,
            headers=_headers(tenant_id=tenant_id),
        )
        updated = dict(base_payload)
        updated["max_window_days"] = 14
        updated["actor"] = "superadmin@example.com"
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_id}",
            json=updated,
            headers=_headers(tenant_id=tenant_id),
        )

        resp = client.get(
            f"/api/admin/brain/reprocess/policy/{tenant_id}/history",
            headers=_headers(tenant_id=tenant_id),
        )
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) == 2
        assert history[0]["actor"] == "admin@example.com"
        assert history[1]["actor"] == "superadmin@example.com"
        assert history[1]["policy"]["max_window_days"] == 14

    def test_history_is_tenant_scoped(self) -> None:
        _reset()
        tenant_a = _create_tenant("replay-policy-scope-a")
        tenant_b = _create_tenant("replay-policy-scope-b")
        payload = {
            "actor": "admin@example.com",
            "max_window_days": 90,
            "allowed_actors": None,
            "auto_reject_threshold": None,
            "require_dual_approval": False,
            "max_replays_per_signal": 5,
        }
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_a}",
            json=payload,
            headers=_headers(tenant_id=tenant_a),
        )
        client.put(
            f"/api/admin/brain/reprocess/policy/{tenant_b}",
            json=payload,
            headers=_headers(tenant_id=tenant_b),
        )

        resp30 = client.get(
            f"/api/admin/brain/reprocess/policy/{tenant_a}/history",
            headers=_headers(tenant_id=tenant_a),
        )
        resp31 = client.get(
            f"/api/admin/brain/reprocess/policy/{tenant_b}/history",
            headers=_headers(tenant_id=tenant_b),
        )

        assert len(resp30.json()) == 1
        assert len(resp31.json()) == 1
        assert all(e["tenant_id"] == tenant_a for e in resp30.json())
        assert all(e["tenant_id"] == tenant_b for e in resp31.json())
