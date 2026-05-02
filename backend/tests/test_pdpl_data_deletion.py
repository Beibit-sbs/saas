"""Tests for the PDPL Right-to-Erasure endpoint.

These tests run without a live database (in-memory local-user-store fallback).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import ADMIN_HEADERS, _auth_headers, client, _reset_local_user_store
from app.modules.auth.local_users_service import local_user_store
from app.modules.audit.service import clear_audit_events, list_admin_actions

TEST_TENANT_ID = 1


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset in-memory stores before every test."""
    _reset_local_user_store()
    clear_audit_events()
    yield
    _reset_local_user_store()
    clear_audit_events()


def _create_test_user(user_id: str = "u-erase-001") -> dict:
    """Insert a local user directly into the in-memory store."""
    user = {
        "user_id": user_id,
        "login": f"testuser_{user_id}",
        "display_name": "Alice PDPL Test",
        "roles": ["student"],
        "default_language": "ar",
        "tenant_id": TEST_TENANT_ID,
        "auth_source": "local",
        "sync_with_ad": False,
    }
    local_user_store._users_by_id[user_id] = user
    local_user_store._users_by_login[user["login"]] = user_id
    local_user_store._loaded = True
    return user


# ------------------------------------------------------------------
# Happy path
# ------------------------------------------------------------------


def test_pdpl_erase_returns_receipt():
    """DELETE /api/admin/pdpl/users/{id}/data returns a valid receipt."""
    user_id = "u-pdpl-001"
    _create_test_user(user_id)

    with patch(
        "app.modules.auth.local_users_service.LocalUserStore._use_db",
        return_value=False,
    ), patch(
        "app.modules.billing.service.assert_billing_write_allowed",
        return_value=None,
    ):
        resp = client.delete(
            f"/api/admin/pdpl/users/{user_id}/data",
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == user_id
    assert body["action"] == "personal_data_erased"
    assert body["regulation"] == "PDPL-SA"
    assert body["article"] == "14"
    assert body["status"] == "completed"
    assert "receipt_id" in body
    assert "issued_at" in body
    assert body["tenant_id"] == TEST_TENANT_ID


def test_pdpl_erase_anonymises_display_name():
    """After erasure the user's display_name should be anonymised."""
    user_id = "u-pdpl-002"
    _create_test_user(user_id)

    with patch(
        "app.modules.auth.local_users_service.LocalUserStore._use_db",
        return_value=False,
    ), patch(
        "app.modules.billing.service.assert_billing_write_allowed",
        return_value=None,
    ):
        resp = client.delete(
            f"/api/admin/pdpl/users/{user_id}/data",
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 200, resp.text
    # Verify in-store anonymisation
    stored = local_user_store._users_by_id.get(user_id)
    assert stored is not None
    assert "ANONYMIZED" in stored["display_name"]


def test_pdpl_erase_emits_audit_event():
    """Erasure should emit a pdpl.erasure audit event."""
    user_id = "u-pdpl-003"
    _create_test_user(user_id)

    with patch(
        "app.modules.auth.local_users_service.LocalUserStore._use_db",
        return_value=False,
    ), patch(
        "app.modules.billing.service.assert_billing_write_allowed",
        return_value=None,
    ):
        client.delete(
            f"/api/admin/pdpl/users/{user_id}/data",
            headers=ADMIN_HEADERS,
        )

    events = list_admin_actions(action="pdpl.erasure", tenant_id=TEST_TENANT_ID)
    assert len(events) == 1
    evt = events[0]
    assert evt["action"] == "pdpl.erasure"
    assert evt["entity"] == "user"
    assert evt["result"] == "success"
    meta = evt.get("metadata", {})
    assert meta.get("user_id") == user_id
    assert meta.get("regulation") == "PDPL-SA"
    assert "receipt_id" in meta


def test_pdpl_erase_404_for_unknown_user():
    """Erasing a non-existent user should return 404."""
    with patch(
        "app.modules.auth.local_users_service.LocalUserStore._use_db",
        return_value=False,
    ):
        resp = client.delete(
            "/api/admin/pdpl/users/does-not-exist/data",
            headers=ADMIN_HEADERS,
        )

    assert resp.status_code == 404


def test_pdpl_erase_requires_auth():
    """Without auth headers the endpoint must return 401."""
    user_id = "u-pdpl-005"
    _create_test_user(user_id)

    resp = client.delete(f"/api/admin/pdpl/users/{user_id}/data")
    assert resp.status_code in (401, 403)


def test_pdpl_erase_requires_admin_role():
    """A student token must be denied (403)."""
    user_id = "u-pdpl-006"
    _create_test_user(user_id)

    student_headers = _auth_headers("student@example.com", ["student"])
    resp = client.delete(
        f"/api/admin/pdpl/users/{user_id}/data",
        headers=student_headers,
    )
    assert resp.status_code == 403
