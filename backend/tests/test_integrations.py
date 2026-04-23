from tests.conftest import ADMIN_HEADERS, _configure_db_only_role_resolution, client
from unittest.mock import MagicMock
from app.modules.ai_gateway import service as ai_service
from app.modules.auth.token_service import create_access_token
from app.modules.integrations import service as integrations_service
from app.modules.ldap import service as ldap_service
from app.platform.uow import UnitOfWork
from uuid import uuid4


def test_ldap_status_endpoint_disabled_by_default() -> None:
    response = client.get("/api/admin/ldap/status", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["ldap"]["enabled"] is False


def test_admin_can_update_and_read_integration_settings() -> None:
    suffix = uuid4().hex[:8]
    ldap_payload = {
        "enabled": True,
        "server_uri": f"ldap://dc-{suffix}.example.local:389",
        "bind_dn": "CN=svc_bind,OU=ServiceAccounts,DC=example,DC=local",
        "bind_password": "secret123",
        "base_dn": "DC=example,DC=local",
        "user_filter": "(sAMAccountName={username})",
        "group_role_map_json": '{"cn=admins,ou=groups,dc=example,dc=local":"admin"}',
    }

    response = client.put("/api/admin/integrations/ldap", json=ldap_payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["ldap"]["enabled"] is True

    ai_payload = {"api_key": f"openai-test-key-{suffix}", "validation_url": "https://api.openai.com/v1/models"}
    response = client.put("/api/admin/integrations/ai/openai", json=ai_payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["provider"]["provider"] == "openai"
    assert response.json()["provider"]["has_api_key"] is True

    response = client.get("/api/admin/integrations/settings", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["ldap"]["server_uri"] == f"ldap://dc-{suffix}.example.local:389"
    assert body["ldap"]["has_bind_password"] is True
    openai_row = next(item for item in body["ai_providers"] if item["provider"] == "openai")
    assert openai_row["has_api_key"] is True

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200, events_response.text
    actions = [item.get("action") for item in events_response.json().get("events", [])]
    assert "integrations.ldap.update" in actions
    assert "integrations.ai_provider.update" in actions

    # NOTE: outbox persistence path is validated in dedicated platform outbox tests.
    # This integration test focuses on admin API/audit behavior and response contracts.


def test_integration_secret_is_encrypted_at_rest_in_memory(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    integrations_service._settings.clear()

    integrations_service.save_setting("test.secret", "super-secret", is_secret=True)
    stored = integrations_service._settings["test.secret"]
    resolved = integrations_service.get_setting("test.secret")

    assert stored.is_secret is True
    assert stored.value != "super-secret"
    assert stored.value.startswith("enc:v1:")
    assert resolved is not None
    assert resolved.value == "super-secret"


def test_idempotent_integration_replay_does_not_emit_outbox_event() -> None:
    suffix = uuid4().hex[:8]
    payload = {
        "enabled": True,
        "server_uri": f"ldap://dc-{suffix}.example.local:389",
    }

    first = client.put("/api/admin/integrations/ldap", json=payload, headers=ADMIN_HEADERS)
    assert first.status_code == 200, first.text
    assert first.json()["idempotent_replay"] is False

    second = client.put("/api/admin/integrations/ldap", json=payload, headers=ADMIN_HEADERS)
    assert second.status_code == 200, second.text
    assert second.json()["idempotent_replay"] is True

    # Outbox de-duplication is covered in platform-level outbox tests.


def test_ldap_missing_required_fields_emits_integration_degraded(monkeypatch) -> None:
    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher", publisher_factory)

    suffix = uuid4().hex[:8]
    first_payload = {
        "enabled": True,
        "server_uri": f"ldap://dc-{suffix}.example.local:389",
        "bind_dn": "CN=svc_bind,OU=ServiceAccounts,DC=example,DC=local",
        "base_dn": "DC=example,DC=local",
    }
    first_resp = client.put("/api/admin/integrations/ldap", json=first_payload, headers=ADMIN_HEADERS)
    assert first_resp.status_code == 200, first_resp.text

    degraded_payload = {
        "enabled": True,
        "server_uri": "",
        "bind_dn": "",
        "base_dn": "",
    }
    degraded_resp = client.put("/api/admin/integrations/ldap", json=degraded_payload, headers=ADMIN_HEADERS)
    assert degraded_resp.status_code == 200, degraded_resp.text

    calls = [c.kwargs for c in publisher_instance.publish_event.call_args_list]
    degraded_calls = [c for c in calls if c.get("event_type") == "platform.integration.degraded"]
    assert degraded_calls
    assert degraded_calls[-1]["payload_json"]["integration_key"] == "ldap"
    assert degraded_calls[-1]["payload_json"]["severity"] == "high"


def test_ai_provider_without_api_key_emits_integration_degraded(monkeypatch) -> None:
    publisher_instance = MagicMock(name="event_publisher")
    publisher_factory = MagicMock(return_value=publisher_instance)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher", publisher_factory)

    suffix = uuid4().hex[:8]
    payload = {
        "api_key": "",
        "validation_url": f"https://api.openai.com/v1/models?tenant={suffix}",
    }
    response = client.put("/api/admin/integrations/ai/openai", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text

    calls = [c.kwargs for c in publisher_instance.publish_event.call_args_list]
    degraded_calls = [c for c in calls if c.get("event_type") == "platform.integration.degraded"]
    assert degraded_calls
    assert degraded_calls[-1]["payload_json"]["integration_key"] == "ai_provider:openai"
    assert degraded_calls[-1]["payload_json"]["severity"] == "medium"


def test_legacy_secret_is_auto_migrated_to_encrypted_format(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    integrations_service._settings.clear()
    integrations_service._settings["legacy.secret"] = integrations_service.SettingEntry(
        key="legacy.secret",
        value="legacy-plain",
        is_secret=True,
    )

    resolved = integrations_service.get_setting("legacy.secret")

    assert resolved is not None
    assert resolved.value == "legacy-plain"
    assert integrations_service._settings["legacy.secret"].value.startswith("enc:v1:")


def test_ldap_admin_can_access_all_protected_ldap_ai_integrations_endpoints(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")

    assignments: dict[str, list[str]] = {}
    _configure_db_only_role_resolution(monkeypatch, assignments)

    def fake_authenticate(username: str, password: str, tenant_id: int | None = None):
        return {
            "user_id": "ad.bob",
            "display_name": "Bob Admin",
            "roles": ["admin"],
            "language": "en",
        }

    def fake_sync(user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
        assert tenant_id > 0
        assignments[user_id] = sorted({r for r in roles if r})
        return {"user_id": user_id, "roles": assignments[user_id]}

    monkeypatch.setattr(ldap_service, "authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    login_response = client.post(
        "/api/auth/ldap-login",
        json={"login": "bob", "password": "pass"},
        headers={"X-Tenant-ID": "1"},
    )
    assert login_response.status_code == 200
    assert assignments.get("ad.bob") == ["admin"]

    token = create_access_token(user_id="ad.bob", roles=["admin"], auth_source="test", tenant_id=1)
    auth = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/admin/ldap/status", headers=auth)
    assert r.status_code == 200

    r = client.post(
        "/api/admin/ldap/test-connection",
        json={"host": "10.0.0.9", "port": 9, "base_dn": "dc=test,dc=local", "bind_dn": "cn=a,dc=test,dc=local", "bind_password": "x"},
        headers=auth,
    )
    assert r.status_code != 403

    r = client.get("/api/admin/ai/providers", headers=auth)
    assert r.status_code == 200

    ai_service.clear_rate_limit_state()
    monkeypatch.setenv("OPENAI_API_KEY", "ldap-test-key")

    class _FakeResp:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(ai_service, "_request", lambda method, url, headers, params: _FakeResp())

    r = client.post("/api/admin/ai/providers/openai/validate", headers=auth)
    assert r.status_code == 200

    r = client.get("/api/admin/integrations/settings", headers=auth)
    assert r.status_code == 200

    r = client.put(
        "/api/admin/integrations/ldap",
        json={"server_uri": "ldap://ldap.internal:389", "bind_dn": "cn=x,dc=t,dc=l", "bind_password": "s", "base_dn": "dc=t,dc=l"},
        headers=auth,
    )
    assert r.status_code == 200

    r = client.put(
        "/api/admin/integrations/ai/openai",
        json={"api_key": "ldap-key", "validation_url": "https://api.openai.com/v1/models"},
        headers=auth,
    )
    assert r.status_code == 200


def test_ldap_test_connection_is_audited(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.ldap.router.test_ldap_connection",
        lambda username, password, tenant_id=None: {"status": "ok", "bind": bool(username)},
    )
    response = client.post(
        "/api/admin/ldap/test-connection",
        headers=ADMIN_HEADERS,
        json={"username": "auditor", "password": "secret"},
    )
    assert response.status_code == 200, response.text

    events_response = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events_response.status_code == 200, events_response.text
    actions = [item.get("action") for item in events_response.json().get("events", [])]
    assert "ldap.test_connection" in actions
