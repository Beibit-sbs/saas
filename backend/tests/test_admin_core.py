from tests.conftest import ADMIN_HEADERS, client
from app.modules.audit import service as audit_service
from app.modules.auth.token_service import create_access_token


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_admin_audit_requires_header() -> None:
    response = client.post("/api/admin/audit-test")
    assert response.status_code == 401


def test_admin_audit_logs_action() -> None:
    audit_service.clear_audit_events()

    response = client.post("/api/admin/audit-test", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "logged"

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    assert len(events) >= 1
    assert events[0]["action"] == "audit_test"
    assert events[0]["entity"] == "audit"
    assert events[0]["result"] == "success"
    assert events[0]["ip"]
    assert events[0]["metadata"]["method"] == "POST"


def test_audit_export_csv() -> None:
    audit_service.clear_audit_events()
    client.post("/api/admin/audit-test", headers=ADMIN_HEADERS)

    response = client.get("/api/admin/audit/export?format=csv", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert "timestamp,actor,action,entity,path,ip,result,correlation_id,metadata" in response.text


def test_admin_audit_uses_database_storage_when_available(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_insert(event: dict[str, object]) -> None:
        captured["event"] = event

    def fake_list(
        actor: str | None = None,
        action: str | None = None,
        entity: str | None = None,
        result: str | None = None,
        correlation_id: str | None = None,
        since: str | None = None,
        limit: int = 100,
        tenant_id: int | None = None,
        include_all_tenants: bool = False,
    ) -> list[dict[str, object]]:
        assert actor is None
        assert action is None
        assert entity is None
        assert result is None
        assert correlation_id is None
        assert since is None
        assert limit == 5
        assert tenant_id == 1
        assert include_all_tenants is False
        return [captured["event"]] if "event" in captured else []

    monkeypatch.setattr(audit_service, "_use_database", lambda: True)
    monkeypatch.setattr(audit_service, "_insert_db", fake_insert)
    monkeypatch.setattr(audit_service, "_list_db", fake_list)
    monkeypatch.setattr(audit_service, "_clear_db", captured.clear)

    audit_service.clear_audit_events()
    audit_service.log_admin_action(
        actor="db-admin@example.com",
        action="db_audit_test",
        path="/api/admin/audit-test",
        client_ip="127.0.0.1",
        entity="audit",
        result="success",
        metadata={"source": "db-test"},
    )

    events = audit_service.list_admin_actions(limit=5)
    assert len(events) == 1
    assert events[0]["actor"] == "db-admin@example.com"
    assert events[0]["metadata"]["source"] == "db-test"
    assert events[0]["tenant_id"] == 1


def test_admin_audit_falls_back_to_memory_when_database_unavailable(monkeypatch) -> None:
    audit_service.clear_audit_events()

    def failing_insert(event: dict[str, object]) -> None:
        raise RuntimeError("db offline")

    def failing_list(
        actor: str | None = None,
        action: str | None = None,
        entity: str | None = None,
        result: str | None = None,
        correlation_id: str | None = None,
        since: str | None = None,
        limit: int = 100,
        tenant_id: int | None = None,
        include_all_tenants: bool = False,
    ) -> list[dict[str, object]]:
        raise RuntimeError("db offline")

    monkeypatch.setattr(audit_service, "_use_database", lambda: True)
    monkeypatch.setattr(audit_service, "_insert_db", failing_insert)
    monkeypatch.setattr(audit_service, "_list_db", failing_list)
    monkeypatch.setattr(audit_service, "_clear_db", lambda: None)

    audit_service.log_admin_action(
        actor="fallback@example.com",
        action="fallback_audit_test",
        path="/api/admin/audit-test",
        client_ip="127.0.0.1",
        entity="audit",
        result="success",
    )

    events = audit_service.list_admin_actions(limit=10)
    assert len(events) >= 1
    assert events[0]["action"] == "fallback_audit_test"


def test_admin_dashboard_requires_permission() -> None:
    response = client.get(
        "/api/admin/dashboard",
        headers={
            "Authorization": f"Bearer {create_access_token('student.001', ['student'], 'test')}",
            "x-user-roles": "admin",
        },
    )
    assert response.status_code == 403


def test_admin_dashboard_rejects_spoofed_actor_header() -> None:
    response = client.get(
        "/api/admin/dashboard",
        headers={
            "Authorization": f"Bearer {create_access_token('owner@example.com', ['admin'], 'test')}",
            "x-admin-user": "attacker@example.com",
        },
    )
    assert response.status_code == 401


def test_admin_dashboard_rejects_invalid_bearer_token() -> None:
    response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401


def test_admin_dashboard_returns_operational_snapshot() -> None:
    response = client.get("/api/admin/dashboard", headers=ADMIN_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["system"]["backend_health"] == "ok"
    assert body["system"]["api_health"] == "ok"
    assert body["system"]["metrics_available"] is True
    assert isinstance(body["users"]["local_users_count"], int)
    assert isinstance(body["rbac"]["roles_count"], int)
    assert isinstance(body["rbac"]["assignments_count"], int)
    assert isinstance(body["languages"]["total_count"], int)
    assert isinstance(body["integrations"]["ai_providers"]["configured_count"], int)
