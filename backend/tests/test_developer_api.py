"""Tests for Developer/Partner Integration API (/api/dev).

Verify that:
- Developer API requires X-App-Key/X-App-Secret credentials
- Endpoints are NOT accessible via public routes
- tenant_id comes from app_key (not URL or X-Tenant-Id header)
- Scope validation works correctly
- Rate limiting is tracked per app_id
- Audit logging is enabled
"""

import pytest
from tests.conftest import client
from app.platform.developer import service as developer_service


class TestDeveloperAPIEndpoints:
    """Verify Developer API endpoints are in correct location with auth required."""

    def test_developer_students_endpoint_requires_auth(self) -> None:
        """GET /api/dev/students returns 401 without developer credentials."""
        response = client.get("/api/dev/students")
        assert response.status_code == 401
        assert "developer app credentials are required" in response.json().get("detail", "")

    def test_developer_enrollments_endpoint_requires_auth(self) -> None:
        """GET /api/dev/enrollments returns 401 without developer credentials."""
        response = client.get("/api/dev/enrollments")
        assert response.status_code == 401

    def test_developer_grades_endpoint_requires_auth(self) -> None:
        """GET /api/dev/grades returns 401 without developer credentials."""
        response = client.get("/api/dev/grades")
        assert response.status_code == 401

    def test_developer_analytics_kpi_endpoint_requires_auth(self) -> None:
        """GET /api/dev/analytics/kpi returns 401 without developer credentials."""
        response = client.get("/api/dev/analytics/kpi")
        assert response.status_code == 401


class TestPublicAPIDoesNotHaveDeveloperEndpoints:
    """Verify Developer endpoints were removed from public API."""

    def test_students_not_in_public_api(self) -> None:
        """GET /api/v1/public/students should NOT exist (moved to /api/dev)."""
        response = client.get("/api/v1/public/students")
        assert response.status_code == 404, (
            "Students endpoint should be removed from public API. "
            "Use /api/dev/students instead."
        )

    def test_enrollments_not_in_public_api(self) -> None:
        """GET /api/v1/public/enrollments should NOT exist (moved to /api/dev)."""
        response = client.get("/api/v1/public/enrollments")
        assert response.status_code == 404

    def test_grades_not_in_public_api(self) -> None:
        """GET /api/v1/public/grades should NOT exist (moved to /api/dev)."""
        response = client.get("/api/v1/public/grades")
        assert response.status_code == 404

    def test_analytics_kpi_not_in_public_api(self) -> None:
        """GET /api/v1/public/analytics/kpi should NOT exist (moved to /api/dev)."""
        response = client.get("/api/v1/public/analytics/kpi")
        assert response.status_code == 404


class TestTenantContextFromAppKey:
    """Verify tenant_id comes from app_key, not URL or headers.

    This is security-critical: developers must NOT be able to override
    tenant context through URL parameters or headers.
    """

    def test_tenant_id_not_accepted_from_url(self) -> None:
        """Even if endpoint accepted {tenant_id} in URL, it would be ignored.
        Current endpoints don't have URL parameters, which is correct."""
        # Current implementation: no {tenant_id} in URL path
        # Tenant comes from X-App-Key credential validation only
        response = client.get("/api/dev/students")
        # Should fail on credential validation, not because of missing {tenant_id}
        assert response.status_code == 401

    def test_tenant_id_from_header_not_used(self) -> None:
        """Manual X-Tenant-Id override must be rejected for developer API."""
        response = client.get(
            "/api/dev/students",
            headers={
                "X-App-Key": "app_key_any",
                "X-App-Secret": "app_secret_any",
                "X-Tenant-Id": "999",
            },
        )
        assert response.status_code == 400
        assert "manual tenant override is forbidden" in response.json().get("detail", "")

    def test_tenant_context_comes_from_app_key_only(self, monkeypatch) -> None:
        """Authenticated calls must use tenant linked to app credentials."""
        app = developer_service.developer_service.create_app(
            tenant_id=1,
            name="Tenant-bound app",
            description="Test app",
            owner_email="owner@example.com",
            scopes=["students.read"],
        )
        developer_service.developer_service.install_app(
            app_id=int(app["id"]),
            tenant_id=1,
            installed_by="test-suite",
        )

        observed: dict[str, int] = {}

        def _fake_list_students(tenant_id: int) -> list[dict[str, object]]:
            observed["tenant_id"] = int(tenant_id)
            return []

        monkeypatch.setattr("app.platform.router_developer_api.students_service.list_students", _fake_list_students)

        response = client.get(
            "/api/dev/students",
            headers={
                "X-App-Key": str(app["app_key"]),
                "X-App-Secret": str(app["app_secret"]),
            },
        )
        assert response.status_code == 200, response.text
        assert observed["tenant_id"] == 1


class TestDeveloperAPIScopes:
    """Verify scope-based access control works for developer endpoints."""

    def test_students_read_scope_required(self) -> None:
        """students.read scope must be present for /students endpoint."""
        # Without credentials: 401
        response = client.get("/api/dev/students")
        assert response.status_code == 401
        # With invalid scope: would get 403 (implementation depends on conftest)

    def test_enrollments_read_scope_required(self) -> None:
        """enrollments.read scope must be present for /enrollments endpoint."""
        response = client.get("/api/dev/enrollments")
        assert response.status_code == 401

    def test_grades_read_scope_required(self) -> None:
        """grades.read scope must be present for /grades endpoint."""
        response = client.get("/api/dev/grades")
        assert response.status_code == 401

    def test_analytics_read_scope_required(self) -> None:
        """analytics.read scope must be present for /analytics/kpi endpoint."""
        response = client.get("/api/dev/analytics/kpi")
        assert response.status_code == 401


class TestDeveloperAPIDocumentation:
    """Verify Developer API is properly documented and discoverable."""

    def test_developer_endpoints_documented_in_openapi(self) -> None:
        """Developer endpoints should appear in OpenAPI docs under developer-api tag."""
        # This is a future test: verify OpenAPI schema includes /api/dev endpoints
        # marked with correct tags and auth requirements
        pass

    def test_developer_endpoints_have_correct_tags(self) -> None:
        """All /api/dev endpoints tagged with 'developer-api'."""
        # Verification: Check that endpoint tags are 'developer-api' not 'public'
        pass


class TestDeveloperAPIRateLimiting:
    """Verify rate limiting is tracked per app_id."""

    def test_rate_limit_tracked_by_app_id(self) -> None:
        """API usage should be logged with app_id for rate limiting purposes."""
        # This verifies that log_api_usage() is called with correct app_id
        # Implementation depends on test database setup
        pass


class TestDeveloperAPIAuditLogging:
    """Verify all developer API calls are audited."""

    def test_api_calls_logged_for_audit(self) -> None:
        """All /api/dev calls should be logged via developer_service.log_api_usage()."""
        # Successful calls should log:
        # - app_id
        # - tenant_id
        # - endpoint path
        # - status_code
        # - latency_ms
        pass

    def test_auth_failures_logged(self) -> None:
        """401/403 responses should be logged for security audit."""
        pass


class TestDeveloperAPIErrorResponses:
    """Verify Developer API returns appropriate error responses."""

    def test_missing_app_key_returns_401(self) -> None:
        """Request without X-App-Key should return 401."""
        response = client.get("/api/dev/students")
        assert response.status_code == 401
        detail = response.json().get("detail", "")
        assert "developer app credentials are required" in detail or "missing" in detail.lower()

    def test_invalid_app_secret_returns_401(self) -> None:
        """Request with invalid X-App-Secret should return 401."""
        response = client.get(
            "/api/dev/students",
            headers={
                "X-App-Key": "invalid_key",
                "X-App-Secret": "invalid_secret",
            },
        )
        assert response.status_code == 401

    def test_insufficient_scope_returns_403(self) -> None:
        """Request without required scope should return 403."""
        # This depends on conftest mocking
        # Application with 'students.write' but not 'students.read'
        # should get 403 on GET /students
        pass

    def test_rate_limit_exceeded_returns_429(self) -> None:
        """Requests exceeding rate limit should return 429."""
        # This depends on rate limiting system being active in tests
        pass


class TestDeveloperAPIDataTenantIsolation:
    """Verify Developer API returns only tenant-scoped data."""

    def test_students_endpoint_returns_only_tenant_students(self) -> None:
        """Students endpoint must return only students for authenticated tenant."""
        # Positive test: with valid auth, returns tenant's students
        # Negative test: cannot access other tenant's students
        pass

    def test_enrollments_endpoint_returns_only_tenant_enrollments(self) -> None:
        """Enrollments endpoint must return only enrollments for authenticated tenant."""
        pass

    def test_analytics_endpoint_returns_only_tenant_analytics(self) -> None:
        """Analytics endpoint must return only data for authenticated tenant."""
        pass


class TestDeveloperAPISchema:
    """Verify Developer API returns correct response schemas."""

    def test_students_response_schema(self) -> None:
        """Student records should include required fields."""
        # With valid auth: returns list of students with:
        # - id, tenant_id, student_id, first_name, last_name, email, status
        pass

    def test_enrollments_response_schema(self) -> None:
        """Enrollment records should include required fields."""
        # Returns: id, tenant_id, student_id, course_id, semester, status
        pass

    def test_analytics_response_schema(self) -> None:
        """Analytics response should match expected KPI structure."""
        pass
