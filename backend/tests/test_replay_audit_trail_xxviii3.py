"""Phase XXVIII3 — Replay Audit Trail contract tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service
from tests.conftest import client


def _headers(write: bool = False) -> dict[str, str]:
    perms = ["admin.dashboard.read"]
    if write:
        perms.append("admin.dashboard.write")
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=perms,
    )
    return {"Authorization": f"Bearer {token}"}


def _reset() -> None:
    brain_core_service.__init__()


def _seed_and_replay(signal_id: str, tenant_id: int = 1, dry_run: bool = False) -> None:
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
            "metadata": {"source": "xxviii3-test"},
        }
    )
    client.post(
        f"/api/admin/brain/reprocess/{signal_id}",
        json={"dry_run": dry_run, "replay_reason": "audit_trail_test"},
        headers=_headers(write=True),
    )


class TestXXVIII3ReplayAuditTrail:
    def test_audit_trail_lists_replay_requested_event(self) -> None:
        _reset()
        _seed_and_replay(signal_id="audit-sig-1")

        resp = client.get(
            "/api/admin/brain/replay-audit",
            params={"signal_id": "audit-sig-1"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        events = [r["event"] for r in data["records"]]
        assert "replay_requested" in events

    def test_audit_trail_lists_replay_executed_for_non_dry_run(self) -> None:
        _reset()
        _seed_and_replay(signal_id="audit-sig-2", dry_run=False)

        resp = client.get(
            "/api/admin/brain/replay-audit",
            params={"signal_id": "audit-sig-2", "event_type": "replay_executed"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert all(r["event"] == "replay_executed" for r in data["records"])

    def test_audit_trail_dry_run_does_not_emit_executed(self) -> None:
        _reset()
        _seed_and_replay(signal_id="audit-sig-3", dry_run=True)

        resp = client.get(
            "/api/admin/brain/replay-audit",
            params={"signal_id": "audit-sig-3"},
            headers=_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        executed = [r for r in data["records"] if r["event"] == "replay_executed"]
        assert len(executed) == 0
        requested = [r for r in data["records"] if r["event"] == "replay_requested"]
        assert len(requested) >= 1
