"""Phase XXIX1 — Replay approval/reject contract tests.

XXIX1 endpoints:
- POST /api/admin/brain/reprocess/{signal_id}/approve
- POST /api/admin/brain/reprocess/{signal_id}/reject
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


def _seed_signal(signal_id: str = "xxix-sig-1", tenant_id: int = 1) -> None:
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
            "metadata": {"source": "xxix1-test"},
        }
    )


class TestXXIX1ReplayApprovalAPI:
    def test_approve_reprocess_executes_and_marks_approved(self) -> None:
        _reset()
        _seed_signal(signal_id="xxix-approve")

        resp = client.post(
            "/api/admin/brain/reprocess/xxix-approve/approve",
            json={
                "reason": "operator_approved_recovery",
                "idempotency_key": "xxix-approve-001",
            },
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_status"] == "approved"
        assert data["original_signal_id"] == "xxix-approve"

        audit = client.get(
            "/api/admin/brain/replay-audit",
            params={"signal_id": "xxix-approve", "event_type": "replay_approved"},
            headers=_headers(),
        )
        assert audit.status_code == 200
        assert audit.json()["total"] == 1

    def test_reject_reprocess_records_rejection(self) -> None:
        _reset()
        _seed_signal(signal_id="xxix-reject")

        resp = client.post(
            "/api/admin/brain/reprocess/xxix-reject/reject",
            json={"reason": "operator_rejected_manual_review_required"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "replay_rejected"
        assert data["reason"] == "operator_rejected_manual_review_required"

        audit = client.get(
            "/api/admin/brain/replay-audit",
            params={"signal_id": "xxix-reject", "event_type": "replay_rejected"},
            headers=_headers(),
        )
        assert audit.status_code == 200
        assert audit.json()["total"] >= 1

    def test_approve_reprocess_not_found(self) -> None:
        _reset()

        resp = client.post(
            "/api/admin/brain/reprocess/xxix-missing/approve",
            json={"reason": "missing_signal"},
            headers=_headers(),
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "signal_not_found"
