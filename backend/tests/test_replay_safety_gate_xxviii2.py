"""Phase XXVIII2 — Action Replay Safety Gate contract tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile
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


def _reset() -> None:
    brain_core_service.__init__()


def _seed_signal(signal_id: str = "gate-sig", tenant_id: int = 99) -> None:
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
                "attendance_rate": 0.45,
                "grade_trend": "declining",
                "source_entity_type": "section_attendance",
                "source_entity_id": signal_id,
            },
            "metadata": {"source": "xxviii2-test"},
        }
    )


class TestXXVIII2SafetyGate:
    def test_autonomy_level_zero_blocks_replay(self) -> None:
        """autonomy_level=0 (full manual) must block replay — fail-closed."""
        _reset()
        _seed_signal(signal_id="gate-autonomy", tenant_id=50)
        # Set tenant 50 to autonomy_level=0
        brain_core_service._policy_resolver.set_profile(
            TenantPolicyProfile(
                tenant_id=50,
                autonomy_level=0,
                require_approval_for_critical=True,
                default_approval_role="dean_office",
                enable_ai_reasoning=False,
            )
        )

        resp = client.post(
            "/api/admin/brain/reprocess/gate-autonomy",
            json={"replay_reason": "test_autonomy_gate"},
            headers=_headers(),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "autonomy_blocked"

    def test_suspended_tenant_blocks_replay(self) -> None:
        """Explicitly suspended tenants must be blocked regardless of autonomy_level."""
        _reset()
        _seed_signal(signal_id="gate-suspended", tenant_id=51)
        brain_core_service.suspend_tenant_replay(51)

        resp = client.post(
            "/api/admin/brain/reprocess/gate-suspended",
            json={"replay_reason": "should_be_blocked"},
            headers=_headers(),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "policy_suspended"

    def test_unsuspend_allows_replay(self) -> None:
        """After unsuspend, replay must succeed (gate open)."""
        _reset()
        _seed_signal(signal_id="gate-unsuspend", tenant_id=52)
        brain_core_service.suspend_tenant_replay(52)
        brain_core_service.unsuspend_tenant_replay(52)

        resp = client.post(
            "/api/admin/brain/reprocess/gate-unsuspend",
            json={"replay_reason": "should_succeed"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] not in {"safety_gate_blocked", "tenant_mismatch"}

    def test_replay_rate_limit_blocks_after_max_executions(self) -> None:
        """After max replay executions, further replays must be rejected."""
        _reset()
        _seed_signal(signal_id="gate-ratelimit", tenant_id=53)
        # Force the limit to 2 for testability
        brain_core_service._replay_max_per_signal = 2

        for i in range(2):
            r = client.post(
                "/api/admin/brain/reprocess/gate-ratelimit",
                json={"idempotency_key": f"rl-{i}", "replay_reason": "fill_quota"},
                headers=_headers(),
            )
            assert r.status_code == 200

        # Third attempt should be blocked
        resp = client.post(
            "/api/admin/brain/reprocess/gate-ratelimit",
            json={"idempotency_key": "rl-overflow", "replay_reason": "overflow"},
            headers=_headers(),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "replay_rate_limit_exceeded"
