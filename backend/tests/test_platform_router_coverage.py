"""
Tests for modules/platform/router.py — platform admin endpoints.

Currently at 48% coverage. Exercises plans CRUD, quotas, tenant provisioning,
billing state / transition / plan-change endpoints, and the _require_platform_admin guard.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import _auth_headers, client
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.rbac import service as rbac_service

BASE = "/platform"


def _make_platform_admin_headers():
    """Headers for a superadmin on tenant 1 (platform admin)."""
    perms = sorted(rbac_service.resolve_permissions_for_tenant(["superadmin"], tenant_id=1))
    token = create_access_token(
        user_id="platform@admin.test", roles=["superadmin"],
        auth_source="test", tenant_id=1, permissions=perms,
    )
    return {"Authorization": f"Bearer {token}"}


def _make_viewer_headers():
    return _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)


ADMIN = _make_platform_admin_headers()
VIEWER = _make_viewer_headers()


# ---------------------------------------------------------------------------
# _require_platform_admin guard
# ---------------------------------------------------------------------------


class TestPlatformAdminGuard:
    def test_non_admin_gets_403(self):
        resp = client.get(f"{BASE}/plans", headers=VIEWER)
        assert resp.status_code == 403

    def test_superadmin_allowed(self):
        with patch("app.modules.platform.router.list_plans", return_value=[]):
            resp = client.get(f"{BASE}/plans", headers=ADMIN)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /plans
# ---------------------------------------------------------------------------


class TestGetPlans:
    @patch("app.modules.platform.router.list_plans", return_value=[{"id": 1, "code": "free", "name": "Free", "description": "", "active": True}])
    def test_success(self, mock_lp):
        resp = client.get(f"{BASE}/plans", headers=ADMIN)
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data


# ---------------------------------------------------------------------------
# POST /plans
# ---------------------------------------------------------------------------


class TestCreatePlan:
    @patch("app.modules.platform.router.log_admin_action")
    @patch("app.modules.platform.router.create_plan", return_value={"id": 2, "code": "pro", "name": "Pro", "description": "", "active": True})
    def test_success(self, mock_cp, mock_audit):
        resp = client.post(f"{BASE}/plans", headers=ADMIN, json={"code": "pro", "name": "Pro"})
        assert resp.status_code == 200
        assert resp.json()["plan"]["code"] == "pro"

    @patch("app.modules.platform.router.create_plan", side_effect=ValueError("code already exists"))
    def test_duplicate_returns_400(self, mock_cp):
        resp = client.post(f"{BASE}/plans", headers=ADMIN, json={"code": "pro", "name": "Pro"})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PUT /plans/{plan_id}
# ---------------------------------------------------------------------------


class TestUpdatePlan:
    @patch("app.modules.platform.router.log_admin_action")
    @patch("app.modules.platform.router.update_plan", return_value={"id": 1, "code": "free", "name": "Updated Free", "description": "", "active": True})
    def test_success(self, mock_up, mock_audit):
        resp = client.put(f"{BASE}/plans/1", headers=ADMIN, json={"name": "Updated Free"})
        assert resp.status_code == 200
        assert resp.json()["plan"]["name"] == "Updated Free"

    @patch("app.modules.platform.router.update_plan", side_effect=ValueError("plan not found"))
    def test_not_found_returns_404(self, mock_up):
        resp = client.put(f"{BASE}/plans/999", headers=ADMIN, json={"name": "X"})
        assert resp.status_code == 404

    @patch("app.modules.platform.router.update_plan", side_effect=ValueError("invalid"))
    def test_bad_data_returns_400(self, mock_up):
        resp = client.put(f"{BASE}/plans/1", headers=ADMIN, json={"name": "X"})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /quotas
# ---------------------------------------------------------------------------


class TestGetQuotas:
    @patch("app.modules.platform.router.list_quotas", return_value=[])
    def test_success(self, mock_lq):
        resp = client.get(f"{BASE}/quotas", headers=ADMIN)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /quotas/consistency
# ---------------------------------------------------------------------------


class TestQuotaConsistency:
    @patch("app.modules.platform.router.get_plan_quota_consistency_report", return_value={"total_plan_count": 1, "configured_plan_quota_count": 2, "issue_count": 0, "issues": []})
    def test_success(self, mock_rpt):
        resp = client.get(f"{BASE}/quotas/consistency", headers=ADMIN)
        assert resp.status_code == 200
        assert resp.json()["issue_count"] == 0


# ---------------------------------------------------------------------------
# PUT /quotas/{plan_id}
# ---------------------------------------------------------------------------


class TestUpdateQuotas:
    @patch("app.modules.platform.router.log_admin_action")
    @patch("app.modules.platform.router.update_plan_quotas", return_value=[])
    def test_success(self, mock_upq, mock_audit):
        resp = client.put(
            f"{BASE}/quotas/1", headers=ADMIN,
            json={"quotas": {"students": 100}},
        )
        assert resp.status_code == 200

    @patch("app.modules.platform.router.update_plan_quotas", side_effect=ValueError("plan not found"))
    def test_not_found(self, mock_upq):
        resp = client.put(
            f"{BASE}/quotas/999", headers=ADMIN,
            json={"quotas": {"students": 100}},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /tenants (provision)
# ---------------------------------------------------------------------------


class TestCreateTenant:
    @patch("app.modules.platform.router.log_admin_action")
    @patch("app.modules.platform.router.get_tenant_billing_state", return_value={"subscription": {}, "billing_state": "active"})
    @patch("app.modules.platform.router.TenantProvisioningService")
    def test_success(self, mock_tps, mock_billing, mock_audit):
        mock_tps.create_tenant_with_defaults.return_value = {
            "tenant": {"id": 5, "name": "New U"},
            "plan": {"code": "free"},
        }
        resp = client.post(
            f"{BASE}/tenants", headers=ADMIN,
            json={"tenant_name": "New U", "admin_email": "admin@newu.edu"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant"]["id"] == 5
        assert "invite_token" in data

    def test_missing_tenant_name(self):
        resp = client.post(
            f"{BASE}/tenants", headers=ADMIN,
            json={"admin_email": "admin@u.edu"},
        )
        assert resp.status_code == 400

    def test_missing_admin_email(self):
        resp = client.post(
            f"{BASE}/tenants", headers=ADMIN,
            json={"tenant_name": "Test U"},
        )
        assert resp.status_code == 400

    @patch("app.modules.platform.router.TenantProvisioningService")
    def test_duplicate_returns_409(self, mock_tps):
        mock_tps.create_tenant_with_defaults.side_effect = ValueError("tenant already exists")
        resp = client.post(
            f"{BASE}/tenants", headers=ADMIN,
            json={"tenant_name": "Dup U", "admin_email": "admin@dup.edu"},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /tenants/{tenant_id}/billing
# ---------------------------------------------------------------------------


class TestGetBillingState:
    @patch("app.modules.platform.router.get_tenant_billing_state", return_value={"billing_state": "active", "subscription": {}})
    def test_success(self, mock_bs):
        resp = client.get(f"{BASE}/tenants/1/billing", headers=ADMIN)
        assert resp.status_code == 200
        assert resp.json()["billing_state"] == "active"

    @patch("app.modules.platform.router.get_tenant_billing_state", side_effect=ValueError("tenant not found"))
    def test_not_found(self, mock_bs):
        resp = client.get(f"{BASE}/tenants/999/billing", headers=ADMIN)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /tenants/{tid}/billing/subscription/transition
# ---------------------------------------------------------------------------


class TestTransitionSubscription:
    @patch("app.modules.platform.router.log_admin_action")
    @patch("app.modules.platform.router.get_tenant_billing_state", return_value={"billing_state": "active"})
    @patch("app.modules.platform.router.transition_subscription_status", return_value={"id": 1, "status": "suspended"})
    def test_success(self, mock_tr, mock_bs, mock_audit):
        resp = client.post(
            f"{BASE}/tenants/1/billing/subscription/transition",
            headers=ADMIN, json={"status": "suspended"},
        )
        assert resp.status_code == 200

    def test_missing_status(self):
        resp = client.post(
            f"{BASE}/tenants/1/billing/subscription/transition",
            headers=ADMIN, json={},
        )
        assert resp.status_code == 400

    @patch("app.modules.platform.router.transition_subscription_status", side_effect=ValueError("tenant not found"))
    def test_not_found(self, mock_tr):
        resp = client.post(
            f"{BASE}/tenants/999/billing/subscription/transition",
            headers=ADMIN, json={"status": "suspended"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /tenants/{tid}/billing/subscription/plan-change
# ---------------------------------------------------------------------------


class TestChangePlan:
    @patch("app.modules.platform.router.log_admin_action")
    @patch("app.modules.platform.router.change_subscription_plan", return_value={"old_plan": "free", "new_plan": "pro", "effective": "immediate"})
    def test_success(self, mock_cp, mock_audit):
        resp = client.post(
            f"{BASE}/tenants/1/billing/subscription/plan-change",
            headers=ADMIN, json={"plan_code": "pro"},
        )
        assert resp.status_code == 200

    def test_missing_plan_code(self):
        resp = client.post(
            f"{BASE}/tenants/1/billing/subscription/plan-change",
            headers=ADMIN, json={},
        )
        assert resp.status_code == 400

    @patch("app.modules.platform.router.change_subscription_plan", side_effect=ValueError("plan not found"))
    def test_plan_not_found(self, mock_cp):
        resp = client.post(
            f"{BASE}/tenants/1/billing/subscription/plan-change",
            headers=ADMIN, json={"plan_code": "nonexistent"},
        )
        assert resp.status_code == 404
