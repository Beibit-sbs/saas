from tests.conftest import _auth_headers, _configure_db_only_role_resolution, client
from app.modules.auth.token_service import (
    create_access_token,
    revoke_token,
    verify_access_token,
    verify_refresh_token,
)
from app.modules.auth.local_users_service import local_user_store
from app.modules.identity.identity_errors import IdentityInvalidCredentials
from app.modules.ldap import service as ldap_service
from app.modules.security import rate_limit as rate_limit_service


def _ensure_local_user(login: str, password: str, roles: list[str], display_name: str) -> dict[str, object]:
    existing = local_user_store.find_user_by_login(login)
    if existing is not None:
        return existing
    return local_user_store.create_user(
        login=login,
        password=password,
        display_name=display_name,
        roles=roles,
        default_language="ru",
        tenant_id=1,
    )


def _login_local(login: str, password: str, **extra_payload):
    return client.post(
        "/api/auth/login",
        json={"login": login, "password": password, **extra_payload},
        headers={"X-Tenant-ID": "1"},
    )


def test_auth_modes_endpoint() -> None:
    response = client.get("/api/auth/modes")
    assert response.status_code == 200
    body = response.json()
    assert "modes" in body
    assert "local" in body["modes"]


def test_demo_routes_are_removed_from_runtime() -> None:
    client.cookies.clear()
    response_users = client.get("/api/auth/demo-users")
    response_demo_login = client.post("/api/auth/demo-login", json={"user_id": "student.001"})
    response_mock_login = client.post("/api/auth/mock-login", json={"login": "admin", "password": "admin123"})
    assert response_users.status_code == 404
    assert response_demo_login.status_code == 404
    assert response_mock_login.status_code == 404


def test_login_endpoint_local_user_flow() -> None:
    client.cookies.clear()
    user = _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    response = _login_local("admin", "admin123")
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user["user_id"]
    assert isinstance(body.get("access_token"), str)
    assert isinstance(body.get("refresh_token"), str)
    token = response.cookies.get("app_access_token")
    refresh = response.cookies.get("app_refresh_token")
    assert isinstance(token, str)
    assert isinstance(refresh, str)
    claims = verify_access_token(token)
    refresh_claims = verify_refresh_token(refresh)
    assert claims.user_id == user["user_id"]
    assert "admin" in claims.roles
    assert claims.tenant_id == 1
    assert refresh_claims.user_id == user["user_id"]


def test_local_admin_login_syncs_db_roles_and_allows_admin_endpoints(monkeypatch) -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    assignments: dict[str, list[str]] = {}
    _configure_db_only_role_resolution(monkeypatch, assignments)

    def fake_sync(user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
        assert tenant_id == 1
        assignments[user_id] = sorted({role for role in roles if role})
        return {"user_id": user_id, "roles": assignments[user_id]}

    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    login_response = _login_local("admin", "admin123")
    assert login_response.status_code == 200
    assert assignments
    dashboard_response = client.get(
        "/api/admin/dashboard",
    )
    assert dashboard_response.status_code == 200


def test_local_teacher_and_student_have_expected_limited_or_no_admin_access(monkeypatch) -> None:
    client.cookies.clear()
    _ensure_local_user("teacher", "teacher123", ["teacher"], "Teacher Local")
    _ensure_local_user("student", "student123", ["student"], "Student Local")
    assignments: dict[str, list[str]] = {}
    _configure_db_only_role_resolution(monkeypatch, assignments)

    def fake_sync(user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
        assert tenant_id == 1
        assignments[user_id] = sorted({role for role in roles if role})
        return {"user_id": user_id, "roles": assignments[user_id]}

    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    teacher_login = _login_local("teacher", "teacher123")
    assert teacher_login.status_code == 200
    assert any("teacher" in roles for roles in assignments.values())

    teacher_dashboard = client.get(
        "/api/admin/dashboard",
    )
    assert teacher_dashboard.status_code == 403

    teacher_rbac = client.get(
        "/api/admin/rbac/roles",
    )
    assert teacher_rbac.status_code == 403

    client.cookies.clear()
    student_login = _login_local("student", "student123")
    assert student_login.status_code == 200
    assert any("student" in roles for roles in assignments.values())

    student_dashboard = client.get(
        "/api/admin/dashboard",
    )
    assert student_dashboard.status_code == 403


def test_me_profile_endpoint() -> None:
    user = _ensure_local_user("profile.admin", "profile123", ["admin"], "Profile Admin")
    headers = {
        "Authorization": f"Bearer {create_access_token(str(user['user_id']), ['admin'], 'test', tenant_id=1)}",
    }
    response = client.get("/api/auth/me/profile", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user["user_id"]
    assert "roles" in body
    assert "permissions" in body
    assert "students.read" in body["permissions"]


def test_primary_login_returns_provider_unavailable_without_identity_provider() -> None:
    client.cookies.clear()
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        headers={"X-Tenant-ID": "1"},
    )

    assert response.status_code == 503, response.text
    detail = response.json().get("detail", {})
    assert detail.get("code") == "IDENTITY_PROVIDER_UNAVAILABLE"


def test_primary_login_local_user_survives_identity_db_unavailable(monkeypatch) -> None:
    client.cookies.clear()
    local_user_store.create_user(
        login="pilot-local",
        password="pilot-secret",
        display_name="Pilot Local",
        roles=["dean"],
        default_language="ru",
        tenant_id=1,
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/auth/login",
        json={"login": "pilot-local", "password": "pilot-secret"},
        headers={"X-Tenant-ID": "1"},
    )

    assert response.status_code == 200, response.text
    claims = verify_access_token(response.json()["access_token"])
    assert claims.user_id.startswith("local.")
    assert "dean" in claims.roles
    assert "metrics.read" in claims.permissions


def test_login_sets_signed_auth_cookie() -> None:
    client.cookies.clear()
    user = _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    response = _login_local("admin", "admin123")
    assert response.status_code == 200
    assert isinstance(response.json().get("access_token"), str)
    assert isinstance(response.json().get("refresh_token"), str)
    token = response.cookies.get("app_access_token")
    refresh = response.cookies.get("app_refresh_token")
    assert isinstance(token, str)
    assert isinstance(refresh, str)
    claims = verify_access_token(token)
    assert claims.user_id == user["user_id"]
    assert "admin" in claims.roles
    assert claims.tenant_id == 1


def test_revoked_access_token_is_rejected() -> None:
    token = create_access_token("admin.001", ["admin"], "test", tenant_id=1)
    claims = verify_access_token(token)
    revoke_token(claims.jti, expires_at=claims.expires_at)

    response = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"]


def test_revoked_access_token_is_rejected_when_redis_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("app.modules.auth.token_service._get_redis_client", lambda: None)
    token = create_access_token("admin.redis.offline", ["admin"], "test", tenant_id=1)
    claims = verify_access_token(token)
    revoke_token(claims.jti, expires_at=claims.expires_at)

    response = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"]


def test_access_token_is_rejected_when_session_store_is_unavailable(monkeypatch) -> None:
    client.cookies.clear()
    _ensure_local_user("session.fail.closed", "session123", ["admin"], "Session Fail Closed")
    login = _login_local("session.fail.closed", "session123")
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    monkeypatch.setattr(
        "app.modules.auth.session_service.is_session_active",
        lambda session_id: (_ for _ in ()).throw(RuntimeError("session db offline")),
    )

    response = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert "session store unavailable" in response.json()["detail"]


def test_login_endpoint_locks_after_repeated_failures(monkeypatch) -> None:
    client.cookies.clear()
    rate_limit_service.clear_rate_limit_state()
    monkeypatch.setattr(
        "app.modules.auth.router.authenticate_tenant_login",
        lambda **kwargs: (_ for _ in ()).throw(IdentityInvalidCredentials()),
    )
    monkeypatch.setattr(rate_limit_service, "get_auth_lockout_threshold", lambda: 2)
    monkeypatch.setattr(rate_limit_service, "get_auth_lockout_base_seconds", lambda: 4)
    monkeypatch.setattr(rate_limit_service, "get_auth_lockout_max_seconds", lambda: 60)
    monkeypatch.setattr(rate_limit_service, "get_auth_lockout_reset_window_seconds", lambda: 3600)

    first = client.post(
        "/api/auth/login",
        json={"login": "blocked.user", "password": "wrong-pass"},
        headers={"X-Tenant-ID": "1"},
    )
    second = client.post(
        "/api/auth/login",
        json={"login": "blocked.user", "password": "wrong-pass"},
        headers={"X-Tenant-ID": "1"},
    )
    third = client.post(
        "/api/auth/login",
        json={"login": "blocked.user", "password": "wrong-pass"},
        headers={"X-Tenant-ID": "1"},
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert third.status_code == 429
    assert third.headers.get("Retry-After") == "4"
    detail = third.json()["detail"]
    assert detail["code"] == "IDENTITY_RATE_LIMITED"


def test_refresh_flow_rotates_tokens_and_issues_new_access() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = _login_local("admin", "admin123")
    assert login.status_code == 200
    old_access = client.cookies.get("app_access_token")
    old_refresh = client.cookies.get("app_refresh_token")
    assert isinstance(old_access, str)
    assert isinstance(old_refresh, str)

    csrf = client.get("/api/auth/csrf")
    assert csrf.status_code == 200
    csrf_token = csrf.json()["csrf_token"]

    refresh_response = client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf_token})
    assert refresh_response.status_code == 200
    new_access = client.cookies.get("app_access_token")
    new_refresh = client.cookies.get("app_refresh_token")
    assert isinstance(new_access, str)
    assert isinstance(new_refresh, str)
    assert new_access != old_access
    assert new_refresh != old_refresh


def test_revoked_refresh_token_is_rejected() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = _login_local("admin", "admin123")
    assert login.status_code == 200
    refresh_token = client.cookies.get("app_refresh_token")
    assert isinstance(refresh_token, str)

    refresh_claims = verify_refresh_token(refresh_token)
    revoke_token(refresh_claims.jti, expires_at=refresh_claims.expires_at)

    csrf = client.get("/api/auth/csrf")
    assert csrf.status_code == 200
    csrf_token = csrf.json()["csrf_token"]

    response = client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf_token})
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"]


def test_ldap_login_requires_enabled_config(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.delenv("AUTH_LDAP_ENABLED", raising=False)
    response = client.post(
        "/api/auth/ldap-login",
        json={"login": "alice", "password": "secret"},
        headers={"X-Tenant-ID": "1"},
    )
    assert response.status_code == 400


def test_ldap_login_success(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")

    def fake_authenticate(username: str, password: str, tenant_id: int | None = None):
        assert username == "alice"
        assert password == "secret"
        return {
            "user_id": "ad.alice",
            "display_name": "Alice Admin",
            "roles": ["admin"],
            "language": "ru",
        }

    monkeypatch.setattr(ldap_service, "authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.authenticate_ldap_user", fake_authenticate)

    response = client.post(
        "/api/auth/ldap-login",
        json={"login": "alice", "password": "secret"},
        headers={"X-Tenant-ID": "1"},
    )
    assert response.status_code == 200
    assert response.json()["auth_source"] == "ldap"


def test_ldap_user_can_read_me_profile(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")

    def fake_authenticate(username: str, password: str, tenant_id: int | None = None):
        return {
            "user_id": "ad.alice",
            "display_name": "Alice Admin",
            "roles": ["admin"],
            "language": "ru",
        }

    monkeypatch.setattr(ldap_service, "authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.authenticate_ldap_user", fake_authenticate)

    login = client.post(
        "/api/auth/ldap-login",
        json={"login": "alice", "password": "secret"},
        headers={"X-Tenant-ID": "1"},
    )
    assert login.status_code == 200

    profile = client.get("/api/auth/me/profile")
    assert profile.status_code == 200
    assert profile.json()["user_id"] == "ad.alice"
    assert profile.json()["auth_source"] == "ldap"


def test_ldap_login_syncs_roles_to_db(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")
    synced: dict[str, list[str]] = {}

    def fake_authenticate(username: str, password: str, tenant_id: int | None = None):
        return {
            "user_id": "ad.alice",
            "display_name": "Alice Admin",
            "roles": ["admin"],
            "language": "ru",
        }

    def fake_sync(user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
        assert tenant_id == 1
        synced[user_id] = sorted(roles)
        return {"user_id": user_id, "roles": sorted(roles)}

    monkeypatch.setattr(ldap_service, "authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    response = client.post(
        "/api/auth/ldap-login",
        json={"login": "alice", "password": "secret"},
        headers={"X-Tenant-ID": "1"},
    )
    assert response.status_code == 200
    assert response.json()["auth_source"] == "ldap"
    assert synced.get("ad.alice") == ["admin"]


def test_profile_is_resolved_from_auth_cookie() -> None:
    client.cookies.clear()
    login_user = _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = _login_local("admin", "admin123")
    assert login.status_code == 200

    cookie_name = "app_access_token"
    assert cookie_name in login.cookies

    client.cookies.set(cookie_name, login.cookies[cookie_name])
    me = client.get("/api/auth/me/profile")
    assert me.status_code == 200
    assert me.json()["user_id"] == login_user["user_id"]


def test_legacy_headers_disabled_by_default(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.delenv("AUTH_ALLOW_LEGACY_HEADERS", raising=False)

    response = client.get(
        "/api/auth/me/profile",
        headers={"x-user-id": "admin.001"},
    )
    assert response.status_code == 401


def test_csrf_endpoint_issues_token() -> None:
    client.cookies.clear()
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    token = response.json().get("csrf_token")
    assert isinstance(token, str)
    assert len(token) >= 32
    assert "app_csrf_token" in response.cookies
    assert response.cookies.get("app_csrf_token") == token


def test_cookie_auth_mutation_without_csrf_token_is_rejected() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = _login_local("admin", "admin123")
    assert login.status_code == 200

    response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "en"},
    )
    assert response.status_code == 403


def test_cookie_auth_mutation_with_valid_csrf_token_succeeds() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = _login_local("admin", "admin123")
    assert login.status_code == 200

    csrf = client.get("/api/auth/csrf")
    assert csrf.status_code == 200
    token = csrf.json()["csrf_token"]

    response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "en"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
    assert response.json()["language"] == "en"


def test_cookie_auth_mutation_with_invalid_csrf_token_is_rejected() -> None:
    client.cookies.clear()
    _ensure_local_user("admin", "admin123", ["admin"], "Admin Local")
    login = _login_local("admin", "admin123")
    assert login.status_code == 200

    response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "en"},
        headers={"X-CSRF-Token": "invalid-token"},
    )
    assert response.status_code == 403


def test_bearer_only_mutation_without_csrf_token_is_allowed() -> None:
    client.cookies.clear()
    headers = _auth_headers("student.001", ["student"])

    response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "en"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["language"] == "en"
