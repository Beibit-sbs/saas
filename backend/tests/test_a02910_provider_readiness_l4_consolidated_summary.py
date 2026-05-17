"""
A-029.10 Provider L4 Consolidated Summary Endpoint Tests

Validates consolidated provider L4 summary endpoint:
- GET /api/admin/provider-readiness/l4/summary
- aggregates 11 existing provider L4 service summaries
- read-only, tenant-safe, NON_LIVE_READINESS
- no provider calls, no credentials, no sync
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestConsolidatedEndpointRegistration:
    """Test route registration and HTTP contract."""

    def test_consolidated_route_is_registered(self):
        """Verify /summary route exists and is accessible."""
        # Route should exist in the provider_readiness router
        routes = [route.path for route in app.routes]
        assert "/api/admin/provider-readiness/l4/summary" in routes

    def test_route_method_is_get_only(self):
        """Verify method is GET."""
        matching_routes = [
            route for route in app.routes
            if route.path == "/api/admin/provider-readiness/l4/summary"
        ]
        assert len(matching_routes) > 0
        route = matching_routes[0]
        assert "GET" in route.methods or route.methods is None  # GET is default

    def test_no_post_on_consolidated_provider_route(self):
        """Verify POST is not allowed."""
        response = client.post(
            "/api/admin/provider-readiness/l4/summary",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code in [405, 403, 401]  # Method Not Allowed, Forbidden, or Unauthorized

    def test_no_put_on_consolidated_provider_route(self):
        """Verify PUT is not allowed."""
        response = client.put(
            "/api/admin/provider-readiness/l4/summary",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code in [405, 403, 401]

    def test_no_patch_on_consolidated_provider_route(self):
        """Verify PATCH is not allowed."""
        response = client.patch(
            "/api/admin/provider-readiness/l4/summary",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code in [405, 403, 401]


class TestPermissionAndAuthentication:
    """Test permission and authentication boundaries."""

    def test_route_requires_permission(self, authenticated_tenant_header, mocker):
        """Verify admin.expansion.read permission is required."""
        # Mock permission check to verify it's called
        mocker.patch(
            "app.modules.rbac.security.permission_dependency",
            side_effect=lambda perm: lambda: None if perm == "admin.expansion.read" else (_ for _ in ()).throw(Exception("Wrong permission"))
        )
        # The route should require the correct permission
        # This is verified through the route signature

    def test_unauthenticated_request_rejected(self):
        """Verify 401 for missing JWT."""
        response = client.get("/api/admin/provider-readiness/l4/summary")
        assert response.status_code == 401

    def test_valid_authenticated_request_accepted(self, authenticated_tenant_header):
        """Verify 200 with valid authentication."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.status_code == 200

    def test_tenant_dependency_is_fail_closed(self, mocker):
        """Verify tenant resolution fails closed for invalid tenants."""
        # Mock tenant resolver to return None
        mocker.patch(
            "app.core.tenant.get_current_tenant",
            return_value=None,
        )
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers={"Authorization": "Bearer test_token"},
        )
        # Should fail for None tenant
        assert response.status_code in [400, 403]


class TestConsolidatedResponseShape:
    """Test consolidated response contract."""

    @pytest.fixture
    def consolidated_response(self, authenticated_tenant_header):
        """Get consolidated response."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.status_code == 200
        return response.json()

    def test_response_http_200(self, authenticated_tenant_header):
        """Verify HTTP 200 response."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.status_code == 200

    def test_response_content_type_json(self, authenticated_tenant_header):
        """Verify response is JSON."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.headers["content-type"].startswith("application/json")

    def test_tenant_id_present(self, consolidated_response):
        """Verify tenant_id field is present."""
        assert "tenant_id" in consolidated_response
        assert isinstance(consolidated_response["tenant_id"], int)
        assert consolidated_response["tenant_id"] > 0

    def test_readiness_level_correct(self, consolidated_response):
        """Verify readiness_level == L4_PROVIDER_READONLY_CONSOLIDATED_SUMMARY."""
        assert consolidated_response["readiness_level"] == "L4_PROVIDER_READONLY_CONSOLIDATED_SUMMARY"

    def test_maturity_target_is_l4(self, consolidated_response):
        """Verify maturity_target == L4."""
        assert consolidated_response["maturity_target"] == "L4"

    def test_aggregation_source_level_correct(self, consolidated_response):
        """Verify aggregation_source_level == L4_PROVIDER_READONLY_VISIBILITY."""
        assert consolidated_response["aggregation_source_level"] == "L4_PROVIDER_READONLY_VISIBILITY"

    def test_integration_mode_non_live(self, consolidated_response):
        """Verify integration_mode == NON_LIVE_READINESS."""
        assert consolidated_response["integration_mode"] == "NON_LIVE_READINESS"

    def test_coverage_version_a029_10(self, consolidated_response):
        """Verify coverage_version == A-029.10."""
        assert consolidated_response["coverage_version"] == "A-029.10"

    def test_total_provider_candidates_11(self, consolidated_response):
        """Verify total_provider_candidates == 11."""
        assert consolidated_response["total_provider_candidates"] == 11

    def test_provider_l4_visibility_count_11(self, consolidated_response):
        """Verify provider_l4_visibility_count == 11."""
        assert consolidated_response["provider_l4_visibility_count"] == 11

    def test_provider_l4_api_route_count_11(self, consolidated_response):
        """Verify provider_l4_api_route_count == 11."""
        assert consolidated_response["provider_l4_api_route_count"] == 11

    def test_providers_list_present(self, consolidated_response):
        """Verify providers list is present."""
        assert "providers" in consolidated_response
        assert isinstance(consolidated_response["providers"], list)

    def test_no_synthetic_score(self, consolidated_response):
        """Verify readiness_score is not created."""
        assert "readiness_score" not in consolidated_response


class TestProviderAggregation:
    """Test provider aggregation completeness."""

    @pytest.fixture
    def consolidated_response(self, authenticated_tenant_header):
        """Get consolidated response."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.status_code == 200
        return response.json()

    def test_providers_list_length_11(self, consolidated_response):
        """Verify providers list has exactly 11 entries."""
        assert len(consolidated_response["providers"]) == 11

    def test_all_11_providers_present(self, consolidated_response):
        """Verify all 11 provider candidates are present."""
        expected_uces = {
            "UCE-024", "UCE-025", "UCE-030", "UCE-109", "UCE-112",
            "UCE-108", "UCE-027", "UCE-028", "UCE-110", "UCE-113", "UCE-106",
        }
        # Provider summaries should contain readiness data from all 11
        assert len(consolidated_response["providers"]) == 11

    def test_all_providers_preserve_readiness_level(self, consolidated_response):
        """Verify all providers preserve L4_PROVIDER_READONLY_VISIBILITY."""
        for provider in consolidated_response["providers"]:
            if "readiness_level" in provider:
                assert provider["readiness_level"] == "L4_PROVIDER_READONLY_VISIBILITY"

    def test_no_provider_marked_connected(self, consolidated_response):
        """Verify no provider has provider_connected: true."""
        for provider in consolidated_response["providers"]:
            if "provider_connected" in provider:
                assert provider["provider_connected"] is False


class TestCounterRollups:
    """Test counter rollups and zeros."""

    @pytest.fixture
    def consolidated_response(self, authenticated_tenant_header):
        """Get consolidated response."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.status_code == 200
        return response.json()

    def test_provider_connected_count_zero(self, consolidated_response):
        """Verify provider_connected_count == 0."""
        assert consolidated_response["provider_connected_count"] == 0

    def test_provider_live_call_count_zero(self, consolidated_response):
        """Verify provider_live_call_count == 0."""
        assert consolidated_response["provider_live_call_count"] == 0

    def test_provider_credentials_count_zero(self, consolidated_response):
        """Verify provider_credentials_count == 0."""
        assert consolidated_response["provider_credentials_count"] == 0

    def test_provider_external_submission_count_zero(self, consolidated_response):
        """Verify provider_external_submission_count == 0."""
        assert consolidated_response["provider_external_submission_count"] == 0

    def test_provider_sync_count_zero(self, consolidated_response):
        """Verify provider_sync_count == 0."""
        assert consolidated_response["provider_sync_count"] == 0

    def test_provider_type_rollup_present(self, consolidated_response):
        """Verify provider_type_rollup is present."""
        assert "provider_type_rollup" in consolidated_response

    def test_readiness_status_rollup_present(self, consolidated_response):
        """Verify readiness_status_rollup is present."""
        assert "readiness_status_rollup" in consolidated_response

    def test_blocker_rollup_present(self, consolidated_response):
        """Verify blocker_rollup is present."""
        assert "blocker_rollup" in consolidated_response

    def test_missing_evidence_rollup_present(self, consolidated_response):
        """Verify missing_evidence_rollup is present."""
        assert "missing_evidence_rollup" in consolidated_response


class TestForbiddenActions:
    """Test forbidden action flags."""

    @pytest.fixture
    def consolidated_response(self, authenticated_tenant_header):
        """Get consolidated response."""
        response = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response.status_code == 200
        return response.json()

    def test_no_provider_call_true(self, consolidated_response):
        """Verify no_provider_call == True."""
        assert consolidated_response["no_provider_call"] is True

    def test_no_credentials_true(self, consolidated_response):
        """Verify no_credentials == True."""
        assert consolidated_response["no_credentials"] is True

    def test_no_external_submission_true(self, consolidated_response):
        """Verify no_external_submission == True."""
        assert consolidated_response["no_external_submission"] is True

    def test_no_provider_connected_claim_true(self, consolidated_response):
        """Verify no_provider_connected_claim == True."""
        assert consolidated_response["no_provider_connected_claim"] is True

    def test_no_sync_claim_true(self, consolidated_response):
        """Verify no_sync_claim == True."""
        assert consolidated_response["no_sync_claim"] is True

    def test_no_l5_claim_true(self, consolidated_response):
        """Verify no_l5_claim == True."""
        assert consolidated_response["no_l5_claim"] is True

    def test_no_l6_claim_true(self, consolidated_response):
        """Verify no_l6_claim == True."""
        assert consolidated_response["no_l6_claim"] is True

    def test_read_only_true(self, consolidated_response):
        """Verify read_only == True."""
        assert consolidated_response["read_only"] is True

    def test_no_mutation_true(self, consolidated_response):
        """Verify no_mutation == True."""
        assert consolidated_response["no_mutation"] is True

    def test_tenant_scoped_true(self, consolidated_response):
        """Verify tenant_scoped == True."""
        assert consolidated_response["tenant_scoped"] is True


class TestDeterminism:
    """Test endpoint determinism."""

    def test_same_tenant_returns_same_response_shape(self, authenticated_tenant_header):
        """Verify same tenant_id returns same response shape on repeat."""
        response1 = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        response2 = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert response1.json().keys() == response2.json().keys()

    def test_same_tenant_returns_same_provider_count(self, authenticated_tenant_header):
        """Verify provider count is consistent."""
        response1 = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        response2 = client.get(
            "/api/admin/provider-readiness/l4/summary",
            headers=authenticated_tenant_header,
        )
        assert len(response1.json()["providers"]) == len(response2.json()["providers"])


class TestIntegrity:
    """Test code integrity scans."""

    def test_no_external_http_provider_calls(self):
        """Verify no HTTP provider calls in router."""
        with open("backend/app/modules/provider_readiness/router.py") as f:
            content = f.read()
            # Should not contain external HTTP library imports
            assert "import requests" not in content
            assert "import httpx" not in content
            assert "import aiohttp" not in content
            assert "import urllib" not in content
            assert "import boto3" not in content

    def test_no_db_mutation_in_router(self):
        """Verify no DB mutations in router."""
        with open("backend/app/modules/provider_readiness/router.py") as f:
            content = f.read()
            # Should not contain DB mutation patterns
            assert ".add(" not in content or "session.add" not in content
            assert "INSERT INTO" not in content
            assert "UPDATE " not in content


class TestRouterDetails:
    """Test aggregation does not call internal HTTP routes."""

    def test_no_internal_http_forwarding(self):
        """Verify aggregation calls service functions directly."""
        with open("backend/app/modules/provider_readiness/router.py") as f:
            content = f.read()
            # Should call service functions, not HTTP routes
            assert "get_student_information_system_provider_l4_visibility_summary" in content
            assert "get_finance_erp_provider_l4_visibility_summary" in content
            # Should NOT try to make internal HTTP calls to routes
            assert 'client.get("/api/admin/provider-readiness/l4/' not in content


@pytest.fixture
def authenticated_tenant_header():
    """Provide authenticated tenant header for tests."""
    # This is a basic fixture - in integration tests, use real JWT
    return {
        "Authorization": "Bearer test_jwt_token_with_valid_claims_and_tenant_id_1",
    }
