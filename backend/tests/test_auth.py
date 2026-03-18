from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client
from app.modules.auth.token_service import create_access_token, verify_access_token
from app.modules.ldap import service as ldap_service


def test_auth_modes_endpoint() -> None:
    response = client.get("/api/auth/modes")
    assert response.status_code == 200
    body = response.json()
    assert "modes" in body
    assert "local" in body["modes"]


def test_demo_users_endpoint() -> None:
    response = client.get("/api/auth/demo-users")
    assert response.status_code == 200
    body = response.json()
    assert "users" in body
    assert len(body["users"]) >= 1


def test_demo_login_endpoint() -> None:
    client.cookies.clear()
    response = client.post("/api/auth/demo-login", json={"user_id": "student.001"})
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "student.001"
    assert "language" in body


def test_mock_login_endpoint() -> None:
    client.cookies.clear()
    response = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "admin.001"
    claims = verify_access_token(body["access_token"])
    assert claims.user_id == "admin.001"
    assert "admin" in claims.roles


def test_demo_admin_login_syncs_db_roles_and_allows_admin_endpoints(monkeypatch) -> None:
    client.cookies.clear()
    assignments: dict[str, list[str]] = {}
    _configure_db_only_role_resolution(monkeypatch, assignments)

    def fake_sync(user_id: str, roles: list[str]) -> dict[str, object]:
        assignments[user_id] = sorted({role for role in roles if role})
        return {"user_id": user_id, "roles": assignments[user_id]}

    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)
    monkeypatch.setattr("app.modules.auth.router.local_user_store.authenticate", lambda login, password: None)

    login_response = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
    assert login_response.status_code == 200
    assert assignments.get("admin.001") == ["admin"]

    token = login_response.json()["access_token"]
    dashboard_response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dashboard_response.status_code == 200


def test_demo_teacher_and_student_have_expected_limited_or_no_admin_access(monkeypatch) -> None:
    client.cookies.clear()
    assignments: dict[str, list[str]] = {}
    _configure_db_only_role_resolution(monkeypatch, assignments)

    def fake_sync(user_id: str, roles: list[str]) -> dict[str, object]:
        assignments[user_id] = sorted({role for role in roles if role})
        return {"user_id": user_id, "roles": assignments[user_id]}

    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)
    monkeypatch.setattr("app.modules.auth.router.local_user_store.authenticate", lambda login, password: None)

    teacher_login = client.post(
        "/api/auth/mock-login",
        json={"login": "teacher", "password": "teacher123"},
    )
    assert teacher_login.status_code == 200
    assert assignments.get("teacher.001") == ["auditor"]

    teacher_token = teacher_login.json()["access_token"]
    teacher_dashboard = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_dashboard.status_code == 200

    teacher_rbac = client.get(
        "/api/admin/rbac/roles",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_rbac.status_code == 403

    client.cookies.clear()
    student_login = client.post(
        "/api/auth/mock-login",
        json={"login": "student", "password": "student123"},
    )
    assert student_login.status_code == 200
    assert assignments.get("student.001", []) == []

    student_token = student_login.json()["access_token"]
    student_dashboard = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_dashboard.status_code == 403


def test_me_profile_endpoint() -> None:
    headers = {
        "Authorization": f"Bearer {create_access_token('admin.001', ['admin'], 'test')}",
    }
    response = client.get("/api/auth/me/profile", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "admin.001"
    assert "roles" in body


def test_login_returns_signed_access_token() -> None:
    client.cookies.clear()
    response = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    claims = verify_access_token(token)
    assert claims.user_id == "admin.001"
    assert "admin" in claims.roles


def test_ldap_login_requires_enabled_config(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.delenv("AUTH_LDAP_ENABLED", raising=False)
    response = client.post("/api/auth/ldap-login", json={"login": "alice", "password": "secret"})
    assert response.status_code == 400


def test_ldap_login_success(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")

    def fake_authenticate(username: str, password: str):
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

    response = client.post("/api/auth/ldap-login", json={"login": "alice", "password": "secret"})
    assert response.status_code == 200
    assert response.json()["auth_source"] == "ldap"


def test_ldap_login_syncs_roles_to_db(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setenv("AUTH_LDAP_ENABLED", "true")
    synced: dict[str, list[str]] = {}

    def fake_authenticate(username: str, password: str):
        return {
            "user_id": "ad.alice",
            "display_name": "Alice Admin",
            "roles": ["admin"],
            "language": "ru",
        }

    def fake_sync(user_id: str, roles: list[str]) -> dict[str, object]:
        synced[user_id] = sorted(roles)
        return {"user_id": user_id, "roles": sorted(roles)}

    monkeypatch.setattr(ldap_service, "authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.authenticate_ldap_user", fake_authenticate)
    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    response = client.post("/api/auth/ldap-login", json={"login": "alice", "password": "secret"})
    assert response.status_code == 200
    assert response.json()["auth_source"] == "ldap"
    assert synced.get("ad.alice") == ["admin"]


def test_profile_is_resolved_from_auth_cookie() -> None:
    client.cookies.clear()
    login = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
    assert login.status_code == 200

    cookie_name = "app_access_token"
    assert cookie_name in login.cookies

    client.cookies.set(cookie_name, login.cookies[cookie_name])
    me = client.get("/api/auth/me/profile")
    assert me.status_code == 200
    assert me.json()["user_id"] == "admin.001"


def test_legacy_headers_disabled_by_default(monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.delenv("AUTH_DEV_DEMO_COMPATIBILITY", raising=False)
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
    login = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
    assert login.status_code == 200

    response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "en"},
    )
    assert response.status_code == 403


def test_cookie_auth_mutation_with_valid_csrf_token_succeeds() -> None:
    client.cookies.clear()
    login = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
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
    login = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
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
