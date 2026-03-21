from tests.conftest import ADMIN_HEADERS, _configure_db_only_role_resolution, client
from app.modules.auth.local_users_service import local_user_store


def test_admin_create_and_list_local_user() -> None:
    create_payload = {
        "login": "local.registrar",
        "password": "local12345",
        "display_name": "Local Registrar",
        "roles": ["registrar"],
        "default_language": "ru",
    }

    create_response = client.post(
        "/api/admin/local-users",
        json=create_payload,
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    body = create_response.json()
    assert body["user"]["auth_source"] == "local"
    assert body["user"]["sync_with_ad"] is False

    list_response = client.get("/api/admin/local-users", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    users = list_response.json()["users"]
    assert any(item["login"] == "local.registrar" for item in users)


def test_local_user_can_login_via_mock_login() -> None:
    client.cookies.clear()
    client.post(
        "/api/admin/local-users",
        json={
            "login": "local.teacher",
            "password": "teach12345",
            "display_name": "Local Teacher",
            "roles": ["auditor"],
            "default_language": "en",
        },
        headers=ADMIN_HEADERS,
    )

    response = client.post(
        "/api/auth/mock-login",
        json={"login": "local.teacher", "password": "teach12345"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["auth_source"] == "local"
    assert body["user_id"].startswith("local.")


def test_local_user_login_syncs_server_roles_and_is_idempotent(monkeypatch) -> None:
    client.cookies.clear()
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.sync.case",
            "password": "sync12345",
            "display_name": "Local Sync Case",
            "roles": ["auditor"],
            "default_language": "en",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    assignments: dict[str, list[str]] = {}
    _configure_db_only_role_resolution(monkeypatch, assignments)
    sync_calls = {"count": 0}

    def fake_sync(current_user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
        sync_calls["count"] += 1
        assert tenant_id > 0
        assignments[current_user_id] = sorted({role for role in roles if role})
        return {"user_id": current_user_id, "roles": assignments[current_user_id]}

    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", fake_sync)

    first_login = client.post(
        "/api/auth/mock-login",
        json={"login": "local.sync.case", "password": "sync12345"},
    )
    client.cookies.clear()
    second_login = client.post(
        "/api/auth/mock-login",
        json={"login": "local.sync.case", "password": "sync12345"},
    )

    assert first_login.status_code == 200
    assert second_login.status_code == 200
    assert assignments.get(user_id) == ["auditor"]
    assert sync_calls["count"] == 2
    dashboard_response = client.get(
        "/api/admin/dashboard",
    )
    assert dashboard_response.status_code == 200


def test_local_user_password_is_hashed_in_store() -> None:
    client.cookies.clear()
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.secure",
            "password": "secure12345",
            "display_name": "Local Secure",
            "roles": ["auditor"],
            "default_language": "en",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    raw = local_user_store.get_user(user_id)
    assert raw is not None
    assert "password" not in raw
    assert str(raw.get("password_hash", "")).startswith("pbkdf2_sha256$")

    login_response = client.post(
        "/api/auth/mock-login",
        json={"login": "local.secure", "password": "secure12345"},
    )
    assert login_response.status_code == 200


def test_local_users_list_supports_search_and_filters() -> None:
    alpha_login = "local.filter.alpha"
    beta_login = "local.filter.beta"

    client.post(
        "/api/admin/local-users",
        json={
            "login": alpha_login,
            "password": "filter12345",
            "display_name": "Filter Alpha",
            "roles": ["auditor"],
            "default_language": "en",
        },
        headers=ADMIN_HEADERS,
    )
    client.post(
        "/api/admin/local-users",
        json={
            "login": beta_login,
            "password": "filter12345",
            "display_name": "Filter Beta",
            "roles": ["registrar"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )

    search_response = client.get(
        "/api/admin/local-users?search=Filter%20Alpha",
        headers=ADMIN_HEADERS,
    )
    assert search_response.status_code == 200
    assert any(item["login"] == alpha_login for item in search_response.json()["users"])
    assert all(item["login"] != beta_login for item in search_response.json()["users"])

    role_response = client.get(
        "/api/admin/local-users?role=registrar",
        headers=ADMIN_HEADERS,
    )
    assert role_response.status_code == 200
    assert any(item["login"] == beta_login for item in role_response.json()["users"])

    language_response = client.get(
        "/api/admin/local-users?language=en",
        headers=ADMIN_HEADERS,
    )
    assert language_response.status_code == 200
    assert any(item["login"] == alpha_login for item in language_response.json()["users"])


def test_admin_can_update_local_user() -> None:
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.update.case",
            "password": "update12345",
            "display_name": "Before Update",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    update_response = client.patch(
        f"/api/admin/local-users/{user_id}",
        json={
            "display_name": "After Update",
            "language": "en",
            "roles": ["registrar", "auditor"],
        },
        headers=ADMIN_HEADERS,
    )
    assert update_response.status_code == 200
    body = update_response.json()["user"]
    assert body["display_name"] == "After Update"
    assert body["default_language"] == "en"
    assert body["roles"] == ["registrar", "auditor"]


def test_local_user_create_and_update_sync_rbac_assignments(monkeypatch) -> None:
    sync_events: list[tuple[str, list[str]]] = []

    def fake_sync(user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
        assert tenant_id > 0
        normalized = sorted({role for role in roles if role})
        sync_events.append((user_id, normalized))
        return {"user_id": user_id, "roles": normalized}

    monkeypatch.setattr("app.modules.admin.local_users_router.sync_user_roles_from_trusted_source", fake_sync)

    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.sync.update",
            "password": "syncupdate123",
            "display_name": "Sync Update",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]
    assert sync_events[-1] == (user_id, ["auditor"])

    update_response = client.patch(
        f"/api/admin/local-users/{user_id}",
        json={"roles": ["registrar", "auditor"]},
        headers=ADMIN_HEADERS,
    )
    assert update_response.status_code == 200
    assert sync_events[-1] == (user_id, ["auditor", "registrar"])


def test_admin_can_change_local_user_password() -> None:
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.password.case",
            "password": "oldpass123",
            "display_name": "Password Case",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]
    before = local_user_store.get_user(user_id)
    assert before is not None
    old_hash = str(before.get("password_hash", ""))
    assert old_hash.startswith("pbkdf2_sha256$")

    update_response = client.post(
        f"/api/admin/local-users/{user_id}/password",
        json={"password": "newpass123"},
        headers=ADMIN_HEADERS,
    )
    assert update_response.status_code == 200
    assert update_response.json() == {"status": "updated"}

    after = local_user_store.get_user(user_id)
    assert after is not None
    new_hash = str(after.get("password_hash", ""))
    assert new_hash.startswith("pbkdf2_sha256$")
    assert new_hash != old_hash


def test_local_user_password_update_rejects_invalid_passwords() -> None:
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.password.invalid",
            "password": "valid12345",
            "display_name": "Password Invalid",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    empty_response = client.post(
        f"/api/admin/local-users/{user_id}/password",
        json={"password": ""},
        headers=ADMIN_HEADERS,
    )
    assert empty_response.status_code == 422

    short_response = client.post(
        f"/api/admin/local-users/{user_id}/password",
        json={"password": "123"},
        headers=ADMIN_HEADERS,
    )
    assert short_response.status_code == 422


def test_admin_can_delete_local_user() -> None:
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.delete.case",
            "password": "delete12345",
            "display_name": "Delete Case",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    delete_response = client.delete(f"/api/admin/local-users/{user_id}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    list_response = client.get(
        "/api/admin/local-users?search=local.delete.case",
        headers=ADMIN_HEADERS,
    )
    assert list_response.status_code == 200
    assert all(item["user_id"] != user_id for item in list_response.json()["users"])


def test_local_user_delete_cleans_up_rbac_assignments(monkeypatch) -> None:
    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": "local.cleanup.case",
            "password": "cleanup12345",
            "display_name": "Cleanup Case",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    assignments = {user_id: ["auditor"]}

    def fake_clear(current_user_id: str) -> dict[str, object]:
        had_roles = bool(assignments.pop(current_user_id, []))
        return {"user_id": current_user_id, "removed": had_roles, "roles": []}

    monkeypatch.setattr("app.modules.admin.local_users_router.clear_user_roles_for_user", fake_clear)

    delete_response = client.delete(f"/api/admin/local-users/{user_id}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200
    assert user_id not in assignments
