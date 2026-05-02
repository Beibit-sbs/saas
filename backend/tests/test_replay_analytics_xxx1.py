"""Phase XXX — Replay Analytics & Operator Insights: backend tests."""
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
            "metadata": {"source": "xxx1-test"},
        }
    )


class TestReplayAnalyticsXXX1:
    """XXX1 — GET /api/admin/brain/reprocess/analytics/{tenant_id}"""

    def test_analytics_counts_approve_reject_cancel(self) -> None:
        _reset()
        _seed_signal("xxx-a1", tenant_id=42)
        _seed_signal("xxx-a2", tenant_id=42)
        _seed_signal("xxx-a3", tenant_id=42)

        brain_core_service.approve_signal_reprocess("xxx-a1", actor="op", reason="ok")
        brain_core_service.reject_signal_reprocess("xxx-a2", actor="op", reason="no")
        brain_core_service.cancel_signal_reprocess("xxx-a3", actor="op", reason="abort", expected_tenant_id=42)

        resp = client.get("/api/admin/brain/reprocess/analytics/42", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["approved_count"] == 1
        assert data["rejected_count"] == 1
        assert data["cancelled_count"] == 1
        assert data["total_resolved"] == 3
        assert data["tenant_id"] == 42

    def test_analytics_empty_tenant_returns_zeros(self) -> None:
        _reset()
        resp = client.get("/api/admin/brain/reprocess/analytics/9999", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["approved_count"] == 0
        assert data["rejected_count"] == 0
        assert data["cancelled_count"] == 0
        assert data["total_resolved"] == 0
        assert data["avg_resolution_seconds"] is None
        assert data["top_actors"] == []

    def test_analytics_top_actors_listed(self) -> None:
        _reset()
        for i in range(3):
            sid = f"xxx-top-{i}"
            _seed_signal(sid, tenant_id=7)
            brain_core_service.approve_signal_reprocess(sid, actor="alice", reason="ok")

        resp = client.get("/api/admin/brain/reprocess/analytics/7", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["top_actors"]) >= 1
        top = data["top_actors"][0]
        assert top["actor"] == "alice"
        assert top["actions"] == 3


class TestReplayTrendAlertsXXX2:
    """XXX2 — GET /api/admin/brain/reprocess/alerts/{tenant_id}"""

    def test_no_alert_when_reject_rate_below_threshold(self) -> None:
        _reset()
        for i in range(2):
            sid = f"xxx-ok-{i}"
            _seed_signal(sid, tenant_id=10)
            brain_core_service.approve_signal_reprocess(sid, actor="op", reason="ok")

        resp = client.get("/api/admin/brain/reprocess/alerts/10", headers=_headers())
        assert resp.status_code == 200
        assert resp.json() == []

    def test_alert_raised_when_reject_rate_exceeds_threshold(self) -> None:
        _reset()
        sid_a = "xxx-alert-approve"
        _seed_signal(sid_a, tenant_id=11)
        brain_core_service.approve_signal_reprocess(sid_a, actor="op", reason="ok")

        for i in range(3):
            sid = f"xxx-alert-rej-{i}"
            _seed_signal(sid, tenant_id=11)
            brain_core_service.reject_signal_reprocess(sid, actor="op", reason="no")

        resp = client.get("/api/admin/brain/reprocess/alerts/11", headers=_headers())
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "high_reject_rate"
        assert alerts[0]["tenant_id"] == 11
        assert alerts[0]["reject_rate"] > 0.5

    def test_empty_tenant_no_alerts(self) -> None:
        _reset()
        resp = client.get("/api/admin/brain/reprocess/alerts/9999", headers=_headers())
        assert resp.status_code == 200
        assert resp.json() == []


class TestReplayOperatorSummaryXXX3:
    """XXX3 — GET /api/admin/brain/reprocess/operator-summary/{actor}"""

    def test_operator_summary_counts_actions(self) -> None:
        _reset()
        _seed_signal("xxx-bob-1", tenant_id=20)
        _seed_signal("xxx-bob-2", tenant_id=20)
        brain_core_service.approve_signal_reprocess("xxx-bob-1", actor="bob", reason="ok")
        brain_core_service.reject_signal_reprocess("xxx-bob-2", actor="bob", reason="no")

        resp = client.get("/api/admin/brain/reprocess/operator-summary/bob", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["actor"] == "bob"
        assert data["approved_count"] == 1
        assert data["rejected_count"] == 1
        assert data["cancelled_count"] == 0
        assert data["total_actions"] == 2

    def test_operator_summary_empty_actor(self) -> None:
        _reset()
        resp = client.get("/api/admin/brain/reprocess/operator-summary/nobody", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_actions"] == 0
        assert data["actor"] == "nobody"

    def test_operator_summary_tenants_affected_listed(self) -> None:
        _reset()
        for tid in [30, 31]:
            sid = f"xxx-carol-{tid}"
            _seed_signal(sid, tenant_id=tid)
            brain_core_service.approve_signal_reprocess(sid, actor="carol", reason="ok")

        resp = client.get("/api/admin/brain/reprocess/operator-summary/carol", headers=_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tenants_affected"]) == 2
        assert set(data["tenants_affected"]) == {30, 31}
