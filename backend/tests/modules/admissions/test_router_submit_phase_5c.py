"""
Phase 5C Router Tests: POST /api/admin/admissions/applications/{application_id}/submit

Validation:
- Thin router pattern (no business logic)
- Correct schema parsing (ApplicationSubmitRequestSchema)
- Proper error handling via _map_service_error()
- RBAC permission check (admissions.write)
- Tenant context from trusted header
- Pass-through to ApplicationService.submit_application()
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.modules.admissions.router import submit_application_endpoint, _map_service_error, _parse_payload, ErrorDetailResponse
from app.modules.admissions.schemas import ApplicationSubmitRequestSchema, ApplicationReadSchema, ApplicationStage


class TestPhase5CRouterValidation:
    """Validate Phase 5C router implementation."""

    def test_submit_application_endpoint_signature(self):
        """Test endpoint accepts correct parameters."""
        # Verify function signature
        import inspect
        sig = inspect.signature(submit_application_endpoint)
        
        # Required parameters
        assert "application_id" in sig.parameters
        assert "payload" in sig.parameters
        assert "actor" in sig.parameters
        assert "_" in sig.parameters  # Permission dependency (ignored in signature)
        assert "tenant" in sig.parameters
        assert "db" in sig.parameters

    def test_parse_payload_valid_submit_request(self):
        """Test _parse_payload correctly parses ApplicationSubmitRequestSchema."""
        payload = {"expected_version": 1}
        request_model = _parse_payload(ApplicationSubmitRequestSchema, payload)
        
        assert isinstance(request_model, ApplicationSubmitRequestSchema)
        assert request_model.expected_version == 1

    def test_parse_payload_missing_expected_version_raises_400(self):
        """Test _parse_payload raises 400 when expected_version missing."""
        payload = {}  # Missing required field
        
        with pytest.raises(HTTPException) as exc_info:
            _parse_payload(ApplicationSubmitRequestSchema, payload)
        
        assert exc_info.value.status_code == 400

    def test_parse_payload_invalid_expected_version_type_raises_400(self):
        """Test _parse_payload raises 400 for invalid expected_version type."""
        payload = {"expected_version": "not_an_int"}  # Invalid type
        
        with pytest.raises(HTTPException) as exc_info:
            _parse_payload(ApplicationSubmitRequestSchema, payload)
        
        assert exc_info.value.status_code == 400

    def test_parse_payload_negative_expected_version_raises_400(self):
        """Test _parse_payload raises 400 for negative expected_version."""
        payload = {"expected_version": 0}  # Must be >= 1
        
        with pytest.raises(HTTPException) as exc_info:
            _parse_payload(ApplicationSubmitRequestSchema, payload)
        
        assert exc_info.value.status_code == 400

    def test_map_service_error_permission_error_returns_403(self):
        """Test _map_service_error maps PermissionError to HTTP 403."""
        exc = PermissionError("User lacks admissions.write permission")
        http_exc = _map_service_error(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 403

    def test_map_service_error_version_mismatch_returns_409(self):
        """Test _map_service_error maps version mismatch to HTTP 409."""
        exc = ValueError("Version mismatch for application 123: expected 1, got 2")
        http_exc = _map_service_error(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 409
        assert "version mismatch" in http_exc.detail.lower()

    def test_map_service_error_integrity_error_returns_409(self):
        """Test _map_service_error maps IntegrityError to HTTP 409."""
        exc = IntegrityError("Duplicate entry", None, None)
        http_exc = _map_service_error(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 409

    def test_map_service_error_not_found_returns_404(self):
        """Test _map_service_error maps 'not found' ValueError to HTTP 404."""
        exc = ValueError("Application 999 not found in tenant 1")
        http_exc = _map_service_error(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 404

    def test_map_service_error_generic_returns_400(self):
        """Test _map_service_error maps unrecognized errors to HTTP 400."""
        exc = ValueError("Some unknown error")
        http_exc = _map_service_error(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400

    @pytest.mark.asyncio
    async def test_submit_application_endpoint_success_path(self):
        """Test endpoint successfully submits application via ApplicationService."""
        # Mock dependencies
        mock_db = AsyncMock()
        mock_actor = "user@example.com"
        mock_tenant = {"id": 1}
        mock_payload = {"expected_version": 1}
        
        # Mock ApplicationService
        mock_service = AsyncMock()
        mock_response = MagicMock(spec=ApplicationReadSchema)
        mock_response.id = 123
        mock_response.stage = ApplicationStage.RECEIVED.value
        mock_response.version = 2
        mock_service.submit_application.return_value = mock_response
        
        # Patch ApplicationService
        with patch("app.modules.admissions.router.ApplicationService", return_value=mock_service):
            result = await submit_application_endpoint(
                application_id=123,
                payload=mock_payload,
                actor=mock_actor,
                _=None,  # Permission dependency (already checked by framework)
                tenant=mock_tenant,
                db=mock_db,
            )
        
        # Verify result
        assert result == mock_response
        
        # Verify ApplicationService.submit_application() called correctly
        mock_service.submit_application.assert_called_once_with(
            tenant_id=1,
            application_id=123,
            actor="user@example.com",
            expected_version=1,
        )

    @pytest.mark.asyncio
    async def test_submit_application_endpoint_permission_error_raises_403(self):
        """Test endpoint propagates PermissionError from service."""
        mock_db = AsyncMock()
        mock_actor = "user@example.com"
        mock_tenant = {"id": 1}
        mock_payload = {"expected_version": 1}
        
        mock_service = AsyncMock()
        mock_service.submit_application.side_effect = PermissionError("Tenant mismatch")
        
        with patch("app.modules.admissions.router.ApplicationService", return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await submit_application_endpoint(
                    application_id=123,
                    payload=mock_payload,
                    actor=mock_actor,
                    _=None,
                    tenant=mock_tenant,
                    db=mock_db,
                )
        
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_submit_application_endpoint_version_mismatch_raises_409(self):
        """Test endpoint propagates version mismatch ValueError from service."""
        mock_db = AsyncMock()
        mock_actor = "user@example.com"
        mock_tenant = {"id": 1}
        mock_payload = {"expected_version": 1}
        
        mock_service = AsyncMock()
        mock_service.submit_application.side_effect = ValueError(
            "Version mismatch for application 123: expected 1, got 2"
        )
        
        with patch("app.modules.admissions.router.ApplicationService", return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await submit_application_endpoint(
                    application_id=123,
                    payload=mock_payload,
                    actor=mock_actor,
                    _=None,
                    tenant=mock_tenant,
                    db=mock_db,
                )
        
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_submit_application_endpoint_not_found_raises_404(self):
        """Test endpoint propagates 'not found' ValueError from service."""
        mock_db = AsyncMock()
        mock_actor = "user@example.com"
        mock_tenant = {"id": 1}
        mock_payload = {"expected_version": 1}
        
        mock_service = AsyncMock()
        mock_service.submit_application.side_effect = ValueError(
            "Application 999 not found in tenant 1"
        )
        
        with patch("app.modules.admissions.router.ApplicationService", return_value=mock_service):
            with pytest.raises(HTTPException) as exc_info:
                await submit_application_endpoint(
                    application_id=123,
                    payload=mock_payload,
                    actor=mock_actor,
                    _=None,
                    tenant=mock_tenant,
                    db=mock_db,
                )
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_application_endpoint_passes_tenant_id_from_context(self):
        """Test endpoint extracts tenant_id from trusted context (not from request)."""
        mock_db = AsyncMock()
        mock_actor = "user@example.com"
        mock_tenant = {"id": 42}  # Tenant from trusted context
        mock_payload = {"expected_version": 1}
        
        mock_service = AsyncMock()
        mock_response = MagicMock(spec=ApplicationReadSchema)
        mock_service.submit_application.return_value = mock_response
        
        with patch("app.modules.admissions.router.ApplicationService", return_value=mock_service):
            await submit_application_endpoint(
                application_id=123,
                payload=mock_payload,
                actor=mock_actor,
                _=None,
                tenant=mock_tenant,
                db=mock_db,
            )
        
        # Verify tenant_id from context (42) was passed, not from payload
        mock_service.submit_application.assert_called_once()
        call_args = mock_service.submit_application.call_args
        assert call_args[1]["tenant_id"] == 42

    @pytest.mark.asyncio
    async def test_submit_application_endpoint_passes_actor_from_context(self):
        """Test endpoint passes actor from authenticated context."""
        mock_db = AsyncMock()
        mock_actor = "authenticated_user@example.com"  # From security context
        mock_tenant = {"id": 1}
        mock_payload = {"expected_version": 1}
        
        mock_service = AsyncMock()
        mock_response = MagicMock(spec=ApplicationReadSchema)
        mock_service.submit_application.return_value = mock_response
        
        with patch("app.modules.admissions.router.ApplicationService", return_value=mock_service):
            await submit_application_endpoint(
                application_id=123,
                payload=mock_payload,
                actor=mock_actor,
                _=None,
                tenant=mock_tenant,
                db=mock_db,
            )
        
        # Verify actor from context was passed
        mock_service.submit_application.assert_called_once()
        call_args = mock_service.submit_application.call_args
        assert call_args[1]["actor"] == "authenticated_user@example.com"

    def test_error_detail_response_schema(self):
        """Test ErrorDetailResponse schema for documenting error responses."""
        # Verify ErrorDetailResponse is properly defined for OpenAPI docs
        assert hasattr(ErrorDetailResponse, "schema")
        schema = ErrorDetailResponse.model_json_schema()
        assert "properties" in schema
        assert "detail" in schema["properties"]


class TestPhase5CIntegration:
    """Integration-level tests for router endpoint."""

    def test_submit_endpoint_route_pattern(self):
        """Test route pattern matches expected path."""
        # Verify endpoint is registered at correct path
        from app.modules.admissions.router import router
        
        # Find the submit endpoint
        submit_routes = [
            route for route in router.routes
            if hasattr(route, "path") and "/submit" in route.path
        ]
        
        assert len(submit_routes) > 0, "Submit endpoint not found in router"

    def test_submit_endpoint_method_is_post(self):
        """Test submit endpoint is registered as POST."""
        from app.modules.admissions.router import router
        
        # Find the submit endpoint
        submit_routes = [
            route for route in router.routes
            if hasattr(route, "path") and "/submit" in route.path
        ]
        
        assert any("POST" in str(route.methods) for route in submit_routes)

    def test_submit_endpoint_response_model_is_application_read_schema(self):
        """Test endpoint documents ApplicationReadSchema as response."""
        from app.modules.admissions.router import router
        
        # Find the submit endpoint
        submit_routes = [
            route for route in router.routes
            if hasattr(route, "path") and "/submit" in route.path
        ]
        
        for route in submit_routes:
            if hasattr(route, "response_model"):
                assert route.response_model == ApplicationReadSchema
