"""Phase XXIX2 — Replay cancel contract tests.

XXIX2 endpoint:
- POST /api/admin/brain/reprocess/{signal_id}/cancel
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


def _seed_signal(signal_id: str = "xxix2-sig-1", tenant_id: int = 1) -> None:
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
                "attendance_rate": 0.40,
                "grade_trend": "declining",
                "source_entity_type": "section_attendance",
                "source_entity_id": signal_id,
            },
            "metadata": {"source": "xxix2-test"},
        }
    )


class TestXXIX2ReplayCancelAPI:
    def test_cancel_reprocess_records_cancelled_status(self) -> None:
        _reset()
        _seed_signal(signal_id="xxix2-cancel")

        resp = client.post(
            "/api/admin/brain/reprocess/xxix2-cancel/cancel",
            json={"reason": "operator_cancelled_before_execution"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "replay_cancelled"
        assert data["reason"] == "operator_cancelled_before_execution"

        audit = client.get(
            "/api/admin/brain/replay-audit",
            params={"signal_id": "xxix2-cancel", "event_type": "replay_cancelled"},
            headers=_headers(),
        )
        assert audit.status_code == 200
        assert audit.json()["total"] == 1

    def test_cancel_reprocess_tenant_mismatch_blocked(self) -> None:
        _reset()
        _seed_signal(signal_id="xxix2-tenant", tenant_id=1)

        resp = client.post(
            "/api/admin/brain/reprocess/xxix2-tenant/cancel",
            json={"expected_tenant_id": 2, "reason": "cross_tenant_attempt"},
            headers=_headers(),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "tenant_mismatch"

    def test_cancel_reprocess_not_found(self) -> None:
        _reset()

        resp = client.post(
            "/api/admin/brain/reprocess/xxix2-missing/cancel",
            json={"reason": "missing_signal"},
            headers=_headers(),
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "signal_not_found"
