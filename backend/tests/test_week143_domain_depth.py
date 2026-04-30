"""W143 — academic_integrity: Router DomainValidationError hardening depth tests.

Focus:
- Router write/read endpoint error mapping to 422/404
- Service guards: active-case cap and transition documentation requirements
"""
from __future__ import annotations

import asyncio
import inspect
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.academic_integrity.router as _router
import app.modules.academic_integrity.service as _svc
from app.modules.academic_integrity.schemas import (
    IntegrityCaseCreateSchema,
    IntegrityCaseStatus,
    IntegrityCaseStatusUpdateSchema,
)


def _tenant(tenant_id: str = "1"):
    return SimpleNamespace(id=tenant_id)


def _create_payload() -> IntegrityCaseCreateSchema:
    return IntegrityCaseCreateSchema(
        student_id="stu-1",
        course_id="course-1",
        case_type="plagiarism",
        description="Detailed evidence for case.",
        priority="normal",
    )


class _DummyService:
    def __init__(self):
        self.create_integrity_case = AsyncMock()
        self.update_integrity_case_status = AsyncMock()
        self.get_integrity_case = AsyncMock()


class TestW143Constants:
    def test_status_max_active_exists(self):
        assert hasattr(_svc, "_INTEGRITY_CASE_STATUS_MAX_ACTIVE")

    def test_status_max_active_has_flagged(self):
        assert "flagged" in _svc._INTEGRITY_CASE_STATUS_MAX_ACTIVE

    def test_status_max_active_has_under_review(self):
        assert "under_review" in _svc._INTEGRITY_CASE_STATUS_MAX_ACTIVE

    def test_status_max_active_has_escalated(self):
        assert "escalated" in _svc._INTEGRITY_CASE_STATUS_MAX_ACTIVE

    def test_active_statuses_exists(self):
        assert hasattr(_svc, "_ACTIVE_INTEGRITY_CASE_STATUSES")

    def test_active_statuses_is_frozenset(self):
        assert isinstance(_svc._ACTIVE_INTEGRITY_CASE_STATUSES, frozenset)

    def test_active_statuses_contains_flagged(self):
        assert "flagged" in _svc._ACTIVE_INTEGRITY_CASE_STATUSES

    def test_active_statuses_excludes_resolved(self):
        assert "resolved" not in _svc._ACTIVE_INTEGRITY_CASE_STATUSES

    def test_allowed_transitions_exists(self):
        assert hasattr(_svc, "_ALLOWED_TRANSITIONS")

    def test_closure_requires_notes_exists(self):
        assert hasattr(_svc, "_CLOSURE_REQUIRES_NOTES")

    def test_escalation_requires_action_exists(self):
        assert hasattr(_svc, "_ESCALATION_REQUIRES_ACTION")


class TestW143ServiceCreateCapGuard:
    def test_create_integrity_case_blocks_when_cap_reached(self):
        tenant_service = AsyncMock()
        tenant_service.list_entities.return_value = ([{"status": "flagged"}] * 400, 400)
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        import asyncio
        with pytest.raises(ValueError):
            asyncio.run(svc.create_integrity_case("1", "actor", _create_payload()))

    def test_create_integrity_case_allows_below_cap(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.list_entities.return_value = ([{"status": "flagged"}] * 2, 2)
        tenant_service.create_entity.return_value = {"id": "x"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        created = asyncio.run(svc.create_integrity_case("1", "actor", _create_payload()))
        assert created["status"] == "flagged"

    def test_create_integrity_case_calls_create_entity(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.list_entities.return_value = ([], 0)
        tenant_service.create_entity.return_value = {"id": "x"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        asyncio.run(svc.create_integrity_case("1", "actor", _create_payload()))
        tenant_service.create_entity.assert_called_once()

    def test_create_integrity_case_sets_tenant_id(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.list_entities.return_value = ([], 0)
        tenant_service.create_entity.return_value = {"id": "x"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        created = asyncio.run(svc.create_integrity_case("77", "actor", _create_payload()))
        assert created["tenant_id"] == "77"

    def test_create_integrity_case_sets_created_by(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.list_entities.return_value = ([], 0)
        tenant_service.create_entity.return_value = {"id": "x"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        created = asyncio.run(svc.create_integrity_case("1", "admin@x", _create_payload()))
        assert created["created_by"] == "admin@x"


class TestW143ServiceTransitionGuards:
    def test_update_case_requires_notes_for_resolved(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = {"id": "1", "status": "under_review"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        with pytest.raises(ValueError):
            asyncio.run(svc.update_integrity_case_status(
                tenant_id="1",
                case_id="1",
                actor="a",
                payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.RESOLVED),
            ))

    def test_update_case_requires_notes_for_dismissed(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = {"id": "1", "status": "under_review"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        with pytest.raises(ValueError):
            asyncio.run(svc.update_integrity_case_status(
                tenant_id="1",
                case_id="1",
                actor="a",
                payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.DISMISSED),
            ))

    def test_update_case_requires_recommended_action_for_escalated(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = {"id": "1", "status": "under_review"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        with pytest.raises(ValueError):
            asyncio.run(svc.update_integrity_case_status(
                tenant_id="1",
                case_id="1",
                actor="a",
                payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.ESCALATED),
            ))

    def test_update_case_not_found_raises_value_error(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = None
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        with pytest.raises(ValueError):
            asyncio.run(svc.update_integrity_case_status(
                tenant_id="1",
                case_id="404",
                actor="a",
                payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.UNDER_REVIEW),
            ))

    def test_update_case_invalid_transition_raises_value_error(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = {"id": "1", "status": "resolved"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        with pytest.raises(ValueError):
            asyncio.run(svc.update_integrity_case_status(
                tenant_id="1",
                case_id="1",
                actor="a",
                payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.UNDER_REVIEW),
            ))


class TestW143RouterStructure:
    def test_router_imports_service_as_svc(self):
        src = inspect.getsource(_router)
        assert "import app.modules.academic_integrity.service as _svc" in src

    def test_router_imports_domain_validation_error(self):
        src = inspect.getsource(_router)
        assert "DomainValidationError" in src

    def test_create_endpoint_catches_domain_validation_error(self):
        src = inspect.getsource(_router.create_integrity_case)
        assert "except DomainValidationError" in src

    def test_create_endpoint_maps_value_error_to_422(self):
        src = inspect.getsource(_router.create_integrity_case)
        assert "status_code=422" in src

    def test_update_endpoint_has_not_found_mapping(self):
        src = inspect.getsource(_router.update_integrity_case_status)
        assert "not found" in src.lower()
        assert "status_code = 404" in src

    def test_get_endpoint_maps_value_error_to_404(self):
        src = inspect.getsource(_router.get_integrity_case)
        assert "status_code=404" in src


class TestW143RouterEndpointMappings:
    def test_create_endpoint_value_error_to_422(self):
        svc = _DummyService()
        svc.create_integrity_case.side_effect = ValueError("bad input")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _router.create_integrity_case(
                    payload=_create_payload(),
                    tenant=_tenant(),
                    actor="admin",
                    service=svc,
                )
            )
        assert exc_info.value.status_code == 422

    def test_create_endpoint_domain_validation_error_to_422(self):
        svc = _DummyService()
        svc.create_integrity_case.side_effect = DomainValidationError("blocked")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _router.create_integrity_case(
                    payload=_create_payload(),
                    tenant=_tenant(),
                    actor="admin",
                    service=svc,
                )
            )
        assert exc_info.value.status_code == 422

    def test_update_endpoint_not_found_to_404(self):
        svc = _DummyService()
        svc.update_integrity_case_status.side_effect = ValueError("Case 1 not found")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _router.update_integrity_case_status(
                    case_id="1",
                    payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.UNDER_REVIEW),
                    tenant=_tenant(),
                    actor="admin",
                    service=svc,
                )
            )
        assert exc_info.value.status_code == 404

    def test_update_endpoint_other_value_error_to_422(self):
        svc = _DummyService()
        svc.update_integrity_case_status.side_effect = ValueError("invalid transition")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _router.update_integrity_case_status(
                    case_id="1",
                    payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.UNDER_REVIEW),
                    tenant=_tenant(),
                    actor="admin",
                    service=svc,
                )
            )
        assert exc_info.value.status_code == 422

    def test_update_endpoint_domain_validation_error_to_422(self):
        svc = _DummyService()
        svc.update_integrity_case_status.side_effect = DomainValidationError("blocked")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _router.update_integrity_case_status(
                    case_id="1",
                    payload=IntegrityCaseStatusUpdateSchema(status=IntegrityCaseStatus.UNDER_REVIEW),
                    tenant=_tenant(),
                    actor="admin",
                    service=svc,
                )
            )
        assert exc_info.value.status_code == 422

    def test_get_endpoint_value_error_to_404(self):
        svc = _DummyService()
        svc.get_integrity_case.side_effect = ValueError("Case not found")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                _router.get_integrity_case(
                    case_id="1",
                    tenant=_tenant(),
                    service=svc,
                )
            )
        assert exc_info.value.status_code == 404

    def test_create_endpoint_success_schema_shape(self):
        svc = _DummyService()
        now = datetime.utcnow()
        svc.create_integrity_case.return_value = {
            "id": "1",
            "student_id": "stu-1",
            "course_id": "course-1",
            "assignment_id": None,
            "case_type": "plagiarism",
            "description": "Detailed evidence for case.",
            "evidence_url": None,
            "priority": "normal",
            "status": "flagged",
            "resolution_notes": None,
            "recommended_action": None,
            "created_at": now,
            "updated_at": now,
            "created_by": "admin",
            "tenant_id": "1",
        }

        resp = asyncio.run(
            _router.create_integrity_case(
                payload=_create_payload(),
                tenant=_tenant(),
                actor="admin",
                service=svc,
            )
        )
        assert resp.case.id == "1"


class TestW143Dependency:
    def test_get_service_returns_service_instance(self):
        service = _router.get_service(_svc.get_default_entity_service())
        assert isinstance(service, _svc.AcademicIntegrityService)


class TestW143GuardCoverageExtras:
    def test_get_integrity_case_not_found_raises(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = None
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        with pytest.raises(ValueError):
            asyncio.run(svc.get_integrity_case("1", "404"))

    def test_get_integrity_case_success(self):
        import asyncio
        tenant_service = AsyncMock()
        tenant_service.get_entity.return_value = {"id": "1", "status": "flagged"}
        svc = _svc.AcademicIntegrityService(tenant_entity_service=tenant_service)

        out = asyncio.run(svc.get_integrity_case("1", "1"))
        assert out["id"] == "1"

    def test_router_has_cases_list_route(self):
        paths = {r.path for r in _router.router.routes}
        assert "/api/admin/academic-integrity/cases" in paths

    def test_router_has_case_status_route(self):
        paths = {r.path for r in _router.router.routes}
        assert "/api/admin/academic-integrity/cases/{case_id}/status" in paths

    def test_router_has_brain_context_route(self):
        paths = {r.path for r in _router.router.routes}
        assert "/api/admin/academic-integrity/brain-context" in paths
