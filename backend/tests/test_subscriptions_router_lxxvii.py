"""Phase LXXVII — Subscription router security contract tests.

This suite intentionally validates fail-closed behavior after RBAC hardening.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import _auth_headers

client = TestClient(app, raise_server_exceptions=True)
BASE = "/api/billing/subscriptions"


@pytest.fixture
def admin_headers() -> dict[str, str]:
    # Authenticated principal without explicit billing subscription permission.
    return _auth_headers("owner@example.com", ["admin"], tenant_id=1)


def _assert_denied(response) -> None:
    assert response.status_code in {401, 403}, response.text


def test_list_denied_without_billing_scope(admin_headers) -> None:
    _assert_denied(client.get(BASE, headers=admin_headers))


def test_create_denied_without_billing_scope(admin_headers) -> None:
    _assert_denied(client.post(BASE, json={"tenant_id": 1, "plan_id": 10}, headers=admin_headers))


def test_stats_denied_without_billing_scope(admin_headers) -> None:
    _assert_denied(client.get(f"{BASE}/stats", headers=admin_headers))


def test_get_by_id_denied_without_billing_scope(admin_headers) -> None:
    _assert_denied(client.get(f"{BASE}/sub_1", headers=admin_headers))


def test_cancel_denied_without_billing_scope(admin_headers) -> None:
    _assert_denied(client.post(f"{BASE}/sub_1/cancel", json={}, headers=admin_headers))


def test_upgrade_denied_without_billing_scope(admin_headers) -> None:
    _assert_denied(client.post(f"{BASE}/sub_1/upgrade", json={"new_plan_id": 11}, headers=admin_headers))
