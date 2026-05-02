"""Phase XXVIII — Decision Replay & Recovery contract tests.

XXVIII1: POST /api/admin/brain/reprocess/{signal_id}
- dry_run mode
- execute + idempotency replay
- tenant safety guard
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


def _reset() -> None:
    brain_core_service.__init__()


def _seed_signal(signal_id: str = "xxviii-sig-1", tenant_id: int = 1) -> None:
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
            "metadata": {"source": "xxviii-test"},
        }
    )


class TestXXVIIIReprocessAPI:
    def test_reprocess_dry_run(self) -> None:
        _reset()
        _seed_signal(signal_id="xxviii-dryrun")

        resp = client.post(
            "/api/admin/brain/reprocess/xxviii-dryrun",
            json={"dry_run": True, "replay_reason": "operator_preview"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dry_run"
        assert data["would_process"] is True
        assert data["signal_id"] == "xxviii-dryrun"

    def test_reprocess_execute_idempotency_replay(self) -> None:
        _reset()
        _seed_signal(signal_id="xxviii-idem")

        first = client.post(
            "/api/admin/brain/reprocess/xxviii-idem",
            json={
                "dry_run": False,
                "idempotency_key": "idem-001",
                "replay_reason": "manual_recovery",
            },
            headers=_headers(),
        )
        second = client.post(
            "/api/admin/brain/reprocess/xxviii-idem",
            json={
                "dry_run": False,
                "idempotency_key": "idem-001",
                "replay_reason": "manual_recovery",
            },
            headers=_headers(),
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["idempotent_replay"] is False
        assert second.json()["idempotent_replay"] is True

    def test_reprocess_tenant_mismatch_blocked(self) -> None:
        _reset()
        _seed_signal(signal_id="xxviii-tenant", tenant_id=1)

        resp = client.post(
            "/api/admin/brain/reprocess/xxviii-tenant",
            json={"expected_tenant_id": 2, "replay_reason": "cross_tenant_attempt"},
            headers=_headers(),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "tenant_mismatch"
