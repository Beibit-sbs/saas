from tests.conftest import ADMIN_HEADERS, _configure_db_only_role_resolution, client
from app.modules.ai_gateway import service as ai_service
from app.modules.integrations import service as integrations_service
from app.modules.ldap import service as ldap_service


def test_ldap_status_endpoint_disabled_by_default() -> None:
    response = client.get("/api/admin/ldap/status", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["ldap"]["enabled"] is False


def test_admin_can_update_and_read_integration_settings() -> None:
    ldap_payload = {
        "enabled": True,
        "server_uri": "ldap://dc.example.local:389",
        "bind_dn": "CN=svc_bind,OU=ServiceAccounts,DC=example,DC=local",
        "bind_password": "secret123",
        "base_dn": "DC=example,DC=local",
        "user_filter": "(sAMAccountName={username})",
        "group_role_map_json": '{"cn=admins,ou=groups,dc=example,dc=local":"admin"}',
    }

    response = client.put("/api/admin/integrations/ldap", json=ldap_payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["ldap"]["enabled"] is True

    ai_payload = {"api_key": "openai-test-key", "validation_url": "https://api.openai.com/v1/models"}
    response = client.put("/api/admin/integrations/ai/openai", json=ai_payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["provider"]["provider"] == "openai"
    assert response.json()["provider"]["has_api_key"] is True

    response = client.get("/api/admin/integrations/settings", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["ldap"]["server_uri"] == "ldap://dc.example.local:389"
    assert body["ldap"]["has_bind_password"] is True
    openai_row = next(item for item in body["ai_providers"] if item["provider"] == "openai")
    assert openai_row["has_api_key"] is True


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

    def fake_authenticate(username: str, password: str):
        return {
            "user_id": "ad.bob",
            "display_name": "Bob Admin",
            "roles": ["admin"],
            "language": "en",
        }

    def fake_sync(user_id: str, roles: list[str]) -> dict[str, object]:
        assignments[user_id] = sorted({r for r in roles if r})
        return {"user_id": user_id, "roles": assignments[user_id]}

    monkeypatch.setattr(ldap_service, "authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    login_response = client.post("/api/auth/ldap-login", json={"login": "bob", "password": "pass"})
    assert login_response.status_code == 200
    assert assignments.get("ad.bob") == ["admin"]

    token = login_response.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/admin/ldap/status", headers=auth)
    assert r.status_code == 200

    r = client.post(
        "/api/admin/ldap/test-connection",
        json={"host": "127.0.0.1", "port": 9, "base_dn": "dc=test,dc=local", "bind_dn": "cn=a,dc=test,dc=local", "bind_password": "x"},
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
        json={"server_uri": "ldap://127.0.0.1:389", "bind_dn": "cn=x,dc=t,dc=l", "bind_password": "s", "base_dn": "dc=t,dc=l"},
        headers=auth,
    )
    assert r.status_code == 200

    r = client.put(
        "/api/admin/integrations/ai/openai",
        json={"api_key": "ldap-key", "validation_url": "https://api.openai.com/v1/models"},
        headers=auth,
    )
    assert r.status_code == 200
