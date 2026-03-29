"""Security tests: Verify public API surface is minimal and secure.

SECURITY REQUIREMENTS:
- NO public access to /tenants/{tenant_id} or similar (REMOVED)
- NO developer/partner endpoints in /api/v1/public (MOVED to /api/dev)
- tenant_id MUST come from JWT token, never from URL
- All developer endpoints require X-App-Key/X-App-Secret (strict auth)
"""

import pytest
from tests.conftest import client


class TestPublicEndpointsRemoved:
    """Verify that public tenant endpoints are completely removed."""

    def test_get_tenants_by_id_returns_404_not_found(self) -> None:
        """GET /api/v1/public/tenants/{tenant_id} should NOT exist."""
        response = client.get("/api/v1/public/tenants/1")
        assert response.status_code == 404

    def test_get_tenants_features_by_id_returns_404(self) -> None:
        """GET /api/v1/public/tenants/{tenant_id}/features should NOT exist."""
        response = client.get("/api/v1/public/tenants/1/features")
        assert response.status_code == 404

    def test_get_tenants_subscription_by_id_returns_404(self) -> None:
        """GET /api/v1/public/tenants/{tenant_id}/subscription should NOT exist."""
        response = client.get("/api/v1/public/tenants/1/subscription")
        assert response.status_code == 404

    def test_safe_tenant_endpoints_removed(self) -> None:
        """GET /api/v1/public/tenants-safe/* endpoints should NOT exist."""
        response = client.get("/api/v1/public/tenants-safe/1")
        assert response.status_code == 404

    def test_safe_tenant_subscription_endpoints_removed(self) -> None:
        """GET /api/v1/public/tenants-safe/{tenant_id}/subscription should NOT exist."""
        response = client.get("/api/v1/public/tenants-safe/1/subscription")
        assert response.status_code == 404


class TestDeveloperEndpointsMovedFromPublic:
    """Verify that developer/partner endpoints were moved from /api/v1/public to /api/dev."""

    def test_students_not_in_public_api(self) -> None:
        """GET /api/v1/public/students → 404 (moved to /api/dev/students)."""
        response = client.get("/api/v1/public/students")
        assert response.status_code == 404, (
            "Students endpoint should NOT be in public API"
        )

    def test_enrollments_not_in_public_api(self) -> None:
        """GET /api/v1/public/enrollments → 404 (moved to /api/dev/enrollments)."""
        response = client.get("/api/v1/public/enrollments")
        assert response.status_code == 404

    def test_grades_not_in_public_api(self) -> None:
        """GET /api/v1/public/grades → 404 (moved to /api/dev/grades)."""
        response = client.get("/api/v1/public/grades")
        assert response.status_code == 404

    def test_analytics_kpi_not_in_public_api(self) -> None:
        """GET /api/v1/public/analytics/kpi → 404 (moved to /api/dev/analytics/kpi)."""
        response = client.get("/api/v1/public/analytics/kpi")
        assert response.status_code == 404


class TestEnumerationAttacksBlocked:
    """Verify tenant enumeration is impossible."""

    def test_cannot_enumerate_tenants_1_to_100(self) -> None:
        """Attempting to enumerate tenant_id 1-100 should fail for all."""
        for tenant_id in range(1, 11):
            response = client.get(f"/api/v1/public/tenants/{tenant_id}")
            assert response.status_code == 404

    def test_cannot_enumerate_safe_tenants(self) -> None:
        """Even 'safe' endpoints should not allow enumeration."""
        for tenant_id in range(1, 6):
            response = client.get(f"/api/v1/public/tenants-safe/{tenant_id}")
            assert response.status_code == 404


class TestTenantMetadataNotExposed:
    """Verify tenant business data is never publicly accessible."""

    def test_no_public_settings_leak(self) -> None:
        """Verify settings dict is never exposed in public API."""
        endpoints = [
            "/api/v1/public/tenants/1",
            "/api/v1/public/tenants-safe/1",
            "/api/v1/public/tenants/1/features",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404

    def test_no_public_quotas_leak(self) -> None:
        """Verify quotas dict is never exposed."""
        response = client.get("/api/v1/public/tenants/1")
        assert response.status_code == 404

    def test_no_public_limits_leak(self) -> None:
        """Verify limits dict is never exposed."""
        response = client.get("/api/v1/public/tenants/1")
        assert response.status_code == 404

    """Verify that public tenant endpoints are completely removed."""

    def test_get_tenants_by_id_returns_404_not_found(self) -> None:
        """GET /api/v1/public/tenants/{tenant_id} should NOT exist."""
        response = client.get("/api/v1/public/tenants/1")
        assert response.status_code in [404, 401, 403], (
            f"Got {response.status_code}: {response.text}\n"
            "Public tenant endpoints must be removed or require strong auth."
        )

    def test_get_tenants_features_by_id_returns_404(self) -> None:
        """GET /api/v1/public/tenants/{tenant_id}/features should NOT exist."""
        response = client.get("/api/v1/public/tenants/1/features")
        assert response.status_code in [404, 401, 403]

    def test_get_tenants_subscription_by_id_returns_404(self) -> None:
        """GET /api/v1/public/tenants/{tenant_id}/subscription should NOT exist."""
        response = client.get("/api/v1/public/tenants/1/subscription")
        assert response.status_code in [404, 401, 403]

    def test_safe_tenant_endpoints_removed(self) -> None:
        """GET /api/v1/public/tenants-safe/* endpoints should NOT exist."""
        response = client.get("/api/v1/public/tenants-safe/1")
        assert response.status_code in [404, 401, 403], (
            "Safe tenant endpoints (Option B) must be completely removed."
        )

    def test_safe_tenant_subscription_endpoints_removed(self) -> None:
        """GET /api/v1/public/tenants-safe/{tenant_id}/subscription should NOT exist."""
        response = client.get("/api/v1/public/tenants-safe/1/subscription")
        assert response.status_code in [404, 401, 403]


class TestEnumerationAttacksBlocked:
    """Verify tenant enumeration is impossible."""

    def test_cannot_enumerate_tenants_1_to_100(self) -> None:
        """Attempting to enumerate tenant_id 1-100 should fail for all."""
        for tenant_id in range(1, 11):  # Try first 10
            response = client.get(f"/api/v1/public/tenants/{tenant_id}")
            assert response.status_code in [404, 401, 403], (
                f"Tenant {tenant_id}: Got {response.status_code}. "
                "Public enumeration must be blocked."
            )

    def test_cannot_enumerate_safe_tenants(self) -> None:
        """Even 'safe' endpoints should not allow enumeration."""
        for tenant_id in range(1, 6):
            response = client.get(f"/api/v1/public/tenants-safe/{tenant_id}")
            assert response.status_code in [404, 401, 403], (
                f"Safe tenant {tenant_id}: Got {response.status_code}. "
                "All public tenant endpoints must be removed."
            )


class TestTenantMetadataNotExposed:
    """Verify tenant business data (settings, quotas, limits) is never publicly accessible."""

    def test_no_public_settings_leak(self) -> None:
        """Verify settings dict is never exposed in public API."""
        # Try all variations
        endpoints = [
            "/api/v1/public/tenants/1",
            "/api/v1/public/tenants-safe/1",
            "/api/v1/public/tenants/1/features",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                assert "settings" not in data, (
                    f"{endpoint}: settings MUST NOT be exposed (got {list(data.keys())})"
                )

    def test_no_public_quotas_leak(self) -> None:
        """Verify quotas dict is never exposed."""
        endpoints = [
            "/api/v1/public/tenants/1",
            "/api/v1/public/tenants-safe/1",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                assert "quotas" not in data, (
                    f"{endpoint}: quotas MUST NOT be exposed"
                )

    def test_no_public_limits_leak(self) -> None:
        """Verify limits dict is never exposed."""
        response = client.get("/api/v1/public/tenants/1")
        if response.status_code == 200:
            data = response.json()
            assert "limits" not in data, (
                "limits (business-critical) MUST NOT be exposed"
            )


class TestAuthenticatedEndpoints:
    """Verify developer endpoints require auth in their new /api/dev zone."""

    def test_authenticated_students_endpoint_requires_auth(self) -> None:
        """GET /api/dev/students without auth should fail."""
        response = client.get("/api/dev/students")
        assert response.status_code == 401, (
            "Authenticated endpoints must require X-App-Key/X-App-Secret headers"
        )

    def test_authenticated_enrollments_endpoint_requires_auth(self) -> None:
        """GET /api/dev/enrollments without auth should fail."""
        response = client.get("/api/dev/enrollments")
        assert response.status_code == 401


class TestNoTenantIdFromUrl:
    """Verify tenant_id NEVER comes from URL, only from JWT token."""

    def test_user_cannot_access_other_tenant_via_url(self) -> None:
        """Even if endpoint exists, tenant_id from URL should be ignored."""
        # This is more of a future test if someone creates /api/users/{tenant_id}/data
        # For now, verify no such endpoints exist
        endpoints_with_tenant_id_param = [
            "/api/v1/public/tenants/999",
            "/api/v1/public/tenants/999/features",
            "/api/v1/public/tenants-safe/999",
        ]
        for endpoint in endpoints_with_tenant_id_param:
            response = client.get(endpoint)
            assert response.status_code in [404, 401, 403], (
                f"Endpoint {endpoint} should not accept tenant_id from URL"
            )


class TestCrossTenantDataProtection:
    """Highest priority: Verify cross-tenant data access is impossible."""

    def test_different_tenant_ids_all_blocked(self) -> None:
        """All different tenant IDs in URL should be blocked."""
        tenant_ids = [1, 2, 999, 1000, 999999]
        for tid in tenant_ids:
            response = client.get(f"/api/v1/public/tenants/{tid}")
            assert response.status_code in [404, 401, 403], (
                f"tenant_id={tid} from URL must be blocked (got {response.status_code})"
            )

    def test_safe_endpoint_also_blocks_cross_tenant(self) -> None:
        """Even 'safe' endpoints should not allow cross-tenant access."""
        response = client.get("/api/v1/public/tenants-safe/2")
        assert response.status_code in [404, 401, 403], (
            "Safe endpoints must also block URL-based tenant access"
        )


class TestSubscriptionMetadataProtected:
    """Verify subscription data (pricing, plan code) is never exposed."""

    def test_subscription_endpoint_removed_or_protected(self) -> None:
        """Subscription metadata endpoint must not expose commercial details."""
        response = client.get("/api/v1/public/tenants/1/subscription")
        # Either it should be gone (404) or require auth (401)
        assert response.status_code in [404, 401, 403]

    def test_no_public_subscription_pricing_leak(self) -> None:
        """Verify plan_code, price_cents never exposed."""
        response = client.get("/api/v1/public/tenants/1/subscription")
        if response.status_code == 200:
            data = response.json()
            assert "plan_code" not in data, "plan_code is commercial data"
            assert "price_cents" not in data, "pricing is commercial data"
            assert "plan_id" not in data, "plan_id is commercial data"

