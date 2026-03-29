from tests.conftest import ADMIN_HEADERS, client
from app.modules.auth.token_service import create_access_token
from app.modules.rbac import service as rbac_service
from uuid import uuid4


def test_rbac_roles_endpoint() -> None:
    response = client.get("/api/admin/rbac/roles", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert "roles" in response.json()


def test_rbac_upsert_role() -> None:
    payload = {
        "name": "registrar",
        "permissions": ["admin.dashboard.read", "records.write"],
    }
    response = client.post("/api/admin/rbac/roles", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert "role" in response.json()


def test_rbac_role_persistence_uses_database(monkeypatch) -> None:
    monkeypatch.setattr(rbac_service, "_use_database", lambda: True)
    monkeypatch.setattr(
        rbac_service,
        "_list_roles_db",
        lambda: {
            "admin": ["admin.dashboard.read"],
            "registrar": ["records.write"],
        },
    )

    roles = rbac_service.list_roles()
    assert "registrar" in roles
    assert roles["registrar"] == ["records.write"]


def test_rbac_role_permission_mapping_uses_database(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(rbac_service, "_use_database", lambda: True)

    def fake_upsert(name: str, permissions: set[str]) -> dict[str, list[str]]:
        captured["name"] = name
        captured["permissions"] = set(permissions)
        return {name: sorted(permissions)}

    monkeypatch.setattr(rbac_service, "_add_or_update_role_db", fake_upsert)
    monkeypatch.setattr(
        rbac_service,
        "_resolve_permissions_db",
        lambda roles: {"records.write", "admin.dashboard.read"} if "registrar" in roles else set(),
    )

    result = rbac_service.add_or_update_role("registrar", ["records.write", "admin.dashboard.read"])
    assert result["registrar"] == ["admin.dashboard.read", "records.write"]
    assert captured["name"] == "registrar"
    assert captured["permissions"] == {"records.write", "admin.dashboard.read"}

    granted = rbac_service.resolve_permissions(["registrar"])
    assert "records.write" in granted


def test_rbac_user_role_assignment_uses_database(monkeypatch) -> None:
    monkeypatch.setattr(rbac_service, "_use_database", lambda: True)
    monkeypatch.setattr(
        rbac_service,
        "_assign_role_db",
        lambda user_id, role: {"user_id": user_id, "roles": [role]},
    )
    monkeypatch.setattr(rbac_service, "_get_user_roles_db", lambda user_id: ["auditor"] if user_id else [])

    assigned = rbac_service.assign_role("student.001", "auditor")
    assert assigned["user_id"] == "student.001"
    assert assigned["roles"] == ["auditor"]

    roles = rbac_service.get_user_roles("student.001", tenant_id=1)
    assert roles == ["auditor"]


def test_authorization_resolution_from_db_roles(monkeypatch) -> None:
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "false")
    monkeypatch.setattr(
        rbac_service,
        "_get_user_roles_db",
        lambda user_id: ["auditor"] if user_id == "owner@example.com" else [],
    )

    def fake_resolve(roles: list[str]) -> set[str]:
        if "auditor" in roles:
            return {"admin.dashboard.read", "admin.audit.read"}
        if "admin" in roles:
            return {
                "admin.dashboard.read",
                "admin.roles.manage",
                "admin.audit.read",
            }
        return set()

    monkeypatch.setattr(rbac_service, "_resolve_permissions_db", fake_resolve)

    response = client.get(
        "/api/admin/rbac/roles",
        headers={"Authorization": f"Bearer {create_access_token('owner@example.com', ['admin'], 'test', tenant_id=1)}"},
    )
    assert response.status_code == 403


def test_authorization_dev_fallback_allows_token_roles_when_db_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    monkeypatch.setattr(
        rbac_service,
        "_get_user_roles_db",
        lambda user_id: (_ for _ in ()).throw(RuntimeError("db offline")),
    )
    monkeypatch.setattr(
        rbac_service,
        "_resolve_permissions_db",
        lambda roles: (_ for _ in ()).throw(RuntimeError("db offline")),
    )

    response = client.get(
        "/api/admin/rbac/roles",
        headers={"Authorization": f"Bearer {create_access_token('owner@example.com', ['admin'], 'test', tenant_id=1)}"},
    )
    assert response.status_code == 200


def test_authorization_denies_when_db_unavailable_in_operational_mode(monkeypatch) -> None:
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "false")
    monkeypatch.setattr(
        rbac_service,
        "_get_user_roles_db",
        lambda user_id: (_ for _ in ()).throw(RuntimeError("db offline")),
    )

    response = client.get(
        "/api/admin/rbac/roles",
        headers={"Authorization": f"Bearer {create_access_token('owner@example.com', ['admin'], 'test', tenant_id=1)}"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "rbac database unavailable"


def test_rbac_assignments_list_and_revoke() -> None:
    assign_response = client.post(
        "/api/admin/rbac/assign",
        json={"user_id": "student.assign.case", "role": "auditor"},
        headers=ADMIN_HEADERS,
    )
    assert assign_response.status_code == 200

    list_response = client.get(
        "/api/admin/rbac/assignments?user_id=student.assign.case",
        headers=ADMIN_HEADERS,
    )
    assert list_response.status_code == 200
    assignments = list_response.json()["assignments"]
    assert assignments == [{"user_id": "student.assign.case", "roles": ["auditor"]}]

    revoke_response = client.delete(
        "/api/admin/rbac/assignments/student.assign.case/auditor",
        headers=ADMIN_HEADERS,
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["removed"] is True
    assert revoke_response.json()["roles"] == []

    revoke_again_response = client.delete(
        "/api/admin/rbac/assignments/student.assign.case/auditor",
        headers=ADMIN_HEADERS,
    )
    assert revoke_again_response.status_code == 200
    assert revoke_again_response.json()["removed"] is False
    assert revoke_again_response.json()["roles"] == []


def test_rbac_forbids_self_role_assignment() -> None:
    response = client.post(
        "/api/admin/rbac/assign",
        json={"user_id": "owner@example.com", "role": "auditor"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "self-role modification forbidden"


def test_rbac_forbids_self_role_revoke() -> None:
    response = client.delete(
        "/api/admin/rbac/assignments/owner@example.com/admin",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "self-role modification forbidden"


def test_rbac_forbids_platform_role_assignment_by_non_platform_admin() -> None:
    response = client.post(
        "/api/admin/rbac/assign",
        json={"user_id": "other.admin@example.com", "role": "superadmin"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "platform-only role management requires platform admin"


def test_new_admin_endpoints_require_permissions() -> None:
    low_priv_headers = {
        "Authorization": f"Bearer {create_access_token('student.002', ['student'], 'test', tenant_id=1)}",
    }
    suffix = uuid4().hex[:8]
    login = f"local.permission.case.{suffix}"

    create_response = client.post(
        "/api/admin/local-users",
        json={
            "login": login,
            "password": "permit12345",
            "display_name": "Permission Case",
            "roles": ["auditor"],
            "default_language": "ru",
        },
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["user_id"]

    endpoints = [
        ("patch", f"/api/admin/local-users/{user_id}", {"display_name": "Blocked"}),
        ("delete", f"/api/admin/local-users/{user_id}", None),
        ("post", f"/api/admin/local-users/{user_id}/password", {"password": "blocked123"}),
        ("get", "/api/admin/rbac/assignments", None),
        ("delete", f"/api/admin/rbac/assignments/{user_id}/auditor", None),
    ]

    for method, path, payload in endpoints:
        if payload is None:
            response = getattr(client, method)(path, headers=low_priv_headers)
        else:
            response = getattr(client, method)(path, json=payload, headers=low_priv_headers)
        assert response.status_code == 403
