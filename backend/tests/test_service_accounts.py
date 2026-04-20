"""Tests for service_accounts module — CRUD, token lifecycle, revocation, RBAC guards.

Covers: list, create, idempotent replay, token issue, secret validation,
revoke, permission gates, unauthenticated access, platform-global guards.
"""

from tests.conftest import ADMIN_HEADERS, _auth_headers, client


# ---------------------------------------------------------------------------
# 1. List — empty state
# ---------------------------------------------------------------------------


def test_list_service_accounts_empty() -> None:
    resp = client.get("/api/admin/service-accounts", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["accounts"] == []


# ---------------------------------------------------------------------------
# 2. Create — basic flow
# ---------------------------------------------------------------------------


def test_create_service_account() -> None:
    resp = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={
            "name": "ci-runner",
            "permissions": ["admin.integrations.manage"],
            "platform_global": False,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["idempotent_replay"] is False
    account = body["account"]
    assert account["name"] == "ci-runner"
    assert account["active"] is True
    assert "secret" in account
    assert account["account_id"].startswith("svc.")
    assert "admin.integrations.manage" in account["permissions"]


def test_create_service_account_appears_in_list() -> None:
    client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "list-check", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    resp = client.get("/api/admin/service-accounts", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()["accounts"]]
    assert "list-check" in names


# ---------------------------------------------------------------------------
# 3. Idempotent replay
# ---------------------------------------------------------------------------


def test_create_idempotent_replay() -> None:
    payload = {
        "name": "idempotent-svc",
        "permissions": ["admin.integrations.manage"],
        "platform_global": False,
    }
    first = client.post("/api/admin/service-accounts", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 200
    assert first.json()["idempotent_replay"] is False
    first_id = first.json()["account"]["account_id"]

    second = client.post("/api/admin/service-accounts", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 200
    assert second.json()["idempotent_replay"] is True
    assert second.json()["account"]["account_id"] == first_id


# ---------------------------------------------------------------------------
# 4. Token issue — correct secret
# ---------------------------------------------------------------------------


def test_issue_token_with_valid_secret() -> None:
    created = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "token-test", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    assert created.status_code == 200
    account = created.json()["account"]
    account_id = account["account_id"]
    secret = account["secret"]

    token_resp = client.post(
        f"/api/admin/service-accounts/{account_id}/token",
        headers=ADMIN_HEADERS,
        json={"secret": secret},
    )
    assert token_resp.status_code == 200
    assert "token" in token_resp.json()
    assert len(token_resp.json()["token"]) > 20


# ---------------------------------------------------------------------------
# 5. Token issue — wrong secret
# ---------------------------------------------------------------------------


def test_issue_token_with_wrong_secret_fails() -> None:
    created = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "bad-secret-svc", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    account_id = created.json()["account"]["account_id"]

    resp = client.post(
        f"/api/admin/service-accounts/{account_id}/token",
        headers=ADMIN_HEADERS,
        json={"secret": "wrong-secret-value"},
    )
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6. Token issue — nonexistent account
# ---------------------------------------------------------------------------


def test_issue_token_for_nonexistent_account() -> None:
    resp = client.post(
        "/api/admin/service-accounts/svc.does-not-exist/token",
        headers=ADMIN_HEADERS,
        json={"secret": "long-enough-secret-value"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 7. Revoke account
# ---------------------------------------------------------------------------


def test_revoke_service_account() -> None:
    created = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "revoke-me", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    account_id = created.json()["account"]["account_id"]

    revoke_resp = client.post(
        f"/api/admin/service-accounts/{account_id}/revoke",
        headers=ADMIN_HEADERS,
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["revoked"] is True


def test_revoked_account_rejects_token_issue() -> None:
    created = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "revoke-then-token", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    account = created.json()["account"]
    account_id = account["account_id"]
    secret = account["secret"]

    client.post(f"/api/admin/service-accounts/{account_id}/revoke", headers=ADMIN_HEADERS)

    # After revoke the account is inactive → token issue should fail
    # (the service raises ValueError for disabled accounts)
    resp = client.post(
        f"/api/admin/service-accounts/{account_id}/token",
        headers=ADMIN_HEADERS,
        json={"secret": secret},
    )
    assert resp.status_code == 400
    assert "disabled" in resp.json()["detail"].lower()


def test_revoke_nonexistent_account() -> None:
    resp = client.post(
        "/api/admin/service-accounts/svc.nonexistent/revoke",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 8. Double revoke
# ---------------------------------------------------------------------------


def test_double_revoke_returns_404() -> None:
    created = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "double-revoke", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    account_id = created.json()["account"]["account_id"]

    first = client.post(f"/api/admin/service-accounts/{account_id}/revoke", headers=ADMIN_HEADERS)
    assert first.status_code == 200

    second = client.post(f"/api/admin/service-accounts/{account_id}/revoke", headers=ADMIN_HEADERS)
    assert second.status_code == 404


# ---------------------------------------------------------------------------
# 9. Permission guards
# ---------------------------------------------------------------------------


def test_list_accounts_requires_permission() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/service-accounts", headers=viewer)
    assert resp.status_code == 403


def test_create_account_requires_permission() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/service-accounts",
        headers=viewer,
        json={"name": "denied", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 10. Unauthenticated
# ---------------------------------------------------------------------------


def test_list_accounts_unauthenticated() -> None:
    resp = client.get("/api/admin/service-accounts")
    assert resp.status_code in (401, 403)


def test_create_account_unauthenticated() -> None:
    resp = client.post(
        "/api/admin/service-accounts",
        json={"name": "anon", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 11. Platform-global guard
# ---------------------------------------------------------------------------


def test_platform_global_requires_platform_admin(monkeypatch) -> None:
    """Non-platform-admin cannot create platform-global service account."""
    # Regular admin token (not platform admin)
    regular_admin = _auth_headers("regular.admin@example.com", ["admin"])
    monkeypatch.setattr(
        "app.modules.rbac.service.is_platform_admin",
        lambda actor: actor == "platform.root@example.com",
    )
    resp = client.post(
        "/api/admin/service-accounts",
        headers=regular_admin,
        json={"name": "global-denied", "permissions": ["admin.integrations.manage"], "platform_global": True},
    )
    assert resp.status_code == 403
    assert "platform" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 12. Audit trail
# ---------------------------------------------------------------------------


def test_create_account_is_audited() -> None:
    client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "audit-svc", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    events = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert events.status_code == 200
    actions = [e.get("action") for e in events.json().get("events", [])]
    assert "service_accounts.create" in actions


# ---------------------------------------------------------------------------
# 13. Validation: empty name / empty permissions
# ---------------------------------------------------------------------------


def test_create_with_empty_name_fails() -> None:
    resp = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "  ", "permissions": ["admin.integrations.manage"], "platform_global": False},
    )
    assert resp.status_code == 400
    assert "name" in resp.json()["detail"].lower()


def test_create_with_empty_permissions_fails() -> None:
    resp = client.post(
        "/api/admin/service-accounts",
        headers=ADMIN_HEADERS,
        json={"name": "no-perms", "permissions": [], "platform_global": False},
    )
    assert resp.status_code in (400, 422)
