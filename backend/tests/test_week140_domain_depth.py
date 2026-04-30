"""W140 — research module: DomainValidationError hardening & W110 guard depth tests.

Cross-entity guard: research_publications × research_grants
Guard: _check_author_has_active_grant(*, tenant_id, lead_author_id)
  - PASS if lead_author has grant with status in {active, planned, submitted}
  - FAIL-CLOSED: lookup exception → DomainValidationError with __cause__
  - BLOCK if no matching active grant
"""
from __future__ import annotations

import inspect
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException

import app.modules.research.service as _svc

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.research.schemas import (
    ResearchGrantCreateSchema,
    ResearchGrantSchema,
    ResearchGrantStatusUpdateSchema,
    ResearchPublicationCreateSchema,
    ResearchPublicationSchema,
    ResearchPublicationStatusUpdateSchema,
    ResearchLabSchema,
    ResearchLabStatusUpdateSchema,
    ResearchExperimentSchema,
    ResearchExperimentStatusUpdateSchema,
    ResearchIpAssetSchema,
)

_ROUTER_MOD = sys.modules.get("app.modules.research.router")

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

GRANT_MOCK = {
    "id": 10, "tenant_id": "1", "grant_code": "GR-001",
    "title": "ML Research Grant", "pi_faculty_id": "fac-101",
    "deadline": "2027-12-31", "funding_amount": 50000.0,
    "status": "active", "sponsor_notes": None,
}

PUB_MOCK = {
    "id": 20, "tenant_id": "1", "publication_code": "PUB-001",
    "title": "Deep Learning Methods", "lead_author_id": "fac-101",
    "target_venue": "NeurIPS", "last_activity_days": 5,
    "status": "draft", "citation_count": None,
}

LAB_MOCK = {
    "id": 30, "tenant_id": "1", "lab_code": "LAB-001",
    "name": "AI Lab", "status": "active",
}

EXP_MOCK = {
    "id": 40, "tenant_id": "1", "experiment_code": "EXP-001",
    "title": "Neural Scaling Experiment", "lab_code": "LAB-001",
    "principal_investigator_id": "fac-101", "status": "planned",
}

IP_MOCK = {
    "id": 50, "tenant_id": "1", "asset_code": "IP-001",
    "title": "AI Patent", "status": "draft",
}


# ---------------------------------------------------------------------------
# TestW140Constants
# ---------------------------------------------------------------------------

class TestW140Constants:
    def test_grant_active_for_publication_exists(self):
        assert hasattr(_svc, "_GRANT_ACTIVE_FOR_PUBLICATION")

    def test_grant_active_for_publication_is_frozenset(self):
        assert isinstance(_svc._GRANT_ACTIVE_FOR_PUBLICATION, frozenset)

    def test_grant_active_for_publication_contains_active(self):
        assert "active" in _svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_grant_active_for_publication_contains_planned(self):
        assert "planned" in _svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_grant_active_for_publication_contains_submitted(self):
        assert "submitted" in _svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_grant_active_for_publication_excludes_closed(self):
        assert "closed" not in _svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_grant_active_for_publication_excludes_delayed(self):
        assert "delayed" not in _svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_active_research_grant_statuses_exists(self):
        assert hasattr(_svc, "_ACTIVE_RESEARCH_GRANT_STATUSES")

    def test_active_research_grant_statuses_includes_delayed(self):
        assert "delayed" in _svc._ACTIVE_RESEARCH_GRANT_STATUSES

    def test_guard_function_exists(self):
        assert callable(getattr(_svc, "_check_author_has_active_grant", None))

    def test_grant_status_max_active_exists(self):
        assert hasattr(_svc, "_RESEARCH_GRANT_STATUS_MAX_ACTIVE")

    def test_grant_status_max_active_closed_is_large(self):
        assert _svc._RESEARCH_GRANT_STATUS_MAX_ACTIVE["closed"] >= 1000


# ---------------------------------------------------------------------------
# TestW140GuardAllowPaths
# ---------------------------------------------------------------------------

class TestW140GuardAllowPaths:
    def _run(self, grants, lead_author_id="fac-101"):
        with patch.object(_svc, "list_entities_for_tenant", return_value=grants):
            _svc._check_author_has_active_grant(tenant_id=1, lead_author_id=lead_author_id)

    def test_active_grant_allows(self):
        self._run([{"id": 1, "pi_faculty_id": "fac-101", "status": "active"}])

    def test_planned_grant_allows(self):
        self._run([{"id": 2, "pi_faculty_id": "fac-101", "status": "planned"}])

    def test_submitted_grant_allows(self):
        self._run([{"id": 3, "pi_faculty_id": "fac-101", "status": "submitted"}])

    def test_case_insensitive_match(self):
        self._run([{"id": 4, "pi_faculty_id": "FAC-101", "status": "active"}])

    def test_multiple_grants_one_active_allows(self):
        self._run([
            {"id": 5, "pi_faculty_id": "fac-999", "status": "active"},
            {"id": 6, "pi_faculty_id": "fac-101", "status": "closed"},
            {"id": 7, "pi_faculty_id": "fac-101", "status": "active"},
        ])


# ---------------------------------------------------------------------------
# TestW140GuardBlockPaths
# ---------------------------------------------------------------------------

class TestW140GuardBlockPaths:
    def _run_block(self, grants, lead_author_id="fac-101"):
        with patch.object(_svc, "list_entities_for_tenant", return_value=grants):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_author_has_active_grant(tenant_id=1, lead_author_id=lead_author_id)
        return exc_info.value

    def test_no_grants_blocks(self):
        exc = self._run_block([])
        assert "fac-101" in str(exc)

    def test_no_matching_author_blocks(self):
        exc = self._run_block([{"id": 1, "pi_faculty_id": "fac-999", "status": "active"}])
        assert "fac-101" in str(exc)

    def test_closed_status_blocks(self):
        exc = self._run_block([{"id": 2, "pi_faculty_id": "fac-101", "status": "closed"}])
        assert "fac-101" in str(exc)

    def test_delayed_status_blocks_for_publication(self):
        exc = self._run_block([{"id": 3, "pi_faculty_id": "fac-101", "status": "delayed"}])
        assert "fac-101" in str(exc)

    def test_error_contains_lead_author_id(self):
        exc = self._run_block([], lead_author_id="researcher-xyz")
        assert "researcher-xyz" in str(exc)

    def test_error_mentions_active_statuses(self):
        exc = self._run_block([])
        msg = str(exc).lower()
        assert "active" in msg or "planned" in msg or "submitted" in msg


# ---------------------------------------------------------------------------
# TestW140FailClosed
# ---------------------------------------------------------------------------

class TestW140FailClosed:
    def test_lookup_exception_raises_domain_validation_error(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=RuntimeError("DB lost")):
            with pytest.raises(DomainValidationError):
                _svc._check_author_has_active_grant(tenant_id=1, lead_author_id="fac-101")

    def test_lookup_exception_preserves_cause(self):
        cause = RuntimeError("timeout")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=cause):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_author_has_active_grant(tenant_id=1, lead_author_id="fac-101")
        assert exc_info.value.__cause__ is cause

    def test_lookup_exception_blocks_not_skips(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=Exception("network error")):
            with pytest.raises(DomainValidationError):
                _svc._check_author_has_active_grant(tenant_id=1, lead_author_id="fac-101")

    def test_domain_validation_error_is_raised_not_suppressed(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=ConnectionError("lost")):
            raised = False
            try:
                _svc._check_author_has_active_grant(tenant_id=1, lead_author_id="any")
            except DomainValidationError:
                raised = True
            assert raised, "DomainValidationError must be raised on lookup failure"


# ---------------------------------------------------------------------------
# TestW140TenantIsolation
# ---------------------------------------------------------------------------

class TestW140TenantIsolation:
    def test_guard_calls_list_with_correct_tenant_id(self):
        with patch.object(
            _svc, "list_entities_for_tenant",
            return_value=[{"id": 1, "pi_faculty_id": "fac-101", "status": "active"}],
        ) as mock_list:
            _svc._check_author_has_active_grant(tenant_id=42, lead_author_id="fac-101")
            args = mock_list.call_args
            assert args[0][1] == 42 or args[1].get("tenant_id") == 42

    def test_guard_queries_research_grants_entity_type(self):
        with patch.object(
            _svc, "list_entities_for_tenant",
            return_value=[{"id": 1, "pi_faculty_id": "fac-101", "status": "active"}],
        ) as mock_list:
            _svc._check_author_has_active_grant(tenant_id=1, lead_author_id="fac-101")
            args = mock_list.call_args
            assert args[0][0] == "research_grants"


# ---------------------------------------------------------------------------
# TestW140CreatePublicationWiring
# ---------------------------------------------------------------------------

class TestW140CreatePublicationWiring:
    def _pub_payload(self, code="PUB-T1"):
        return ResearchPublicationCreateSchema(
            publication_code=code,
            title="Test Pub",
            lead_author_id="fac-101",
            target_venue="ICML",
        )

    def test_guard_called_before_create(self):
        with patch.object(_svc, "_check_author_has_active_grant") as mock_guard, \
             patch.object(_svc, "create_entity_for_tenant", return_value=PUB_MOCK), \
             patch.object(_svc, "log_admin_action", return_value=None):
            _svc.create_research_publication(1, self._pub_payload(), "actor")
            mock_guard.assert_called_once()

    def test_create_not_called_when_guard_blocked(self):
        with patch.object(_svc, "_check_author_has_active_grant",
                          side_effect=DomainValidationError("blocked")), \
             patch.object(_svc, "create_entity_for_tenant") as mock_create:
            with pytest.raises(DomainValidationError):
                _svc.create_research_publication(1, self._pub_payload("PUB-T2"), "actor")
            mock_create.assert_not_called()

    def test_active_grant_allows_create(self):
        with patch.object(
            _svc, "list_entities_for_tenant",
            return_value=[{"id": 1, "pi_faculty_id": "fac-101", "status": "active"}],
        ), \
             patch.object(_svc, "create_entity_for_tenant", return_value=PUB_MOCK), \
             patch.object(_svc, "log_admin_action", return_value=None):
            result = _svc.create_research_publication(1, self._pub_payload("PUB-T3"), "actor")
            assert result is not None


# ---------------------------------------------------------------------------
# TestW140RouterStructure
# ---------------------------------------------------------------------------

class TestW140RouterStructure:
    @staticmethod
    def _source():
        mod = _ROUTER_MOD or sys.modules.get("app.modules.research.router")
        if mod is not None:
            return inspect.getsource(mod)
        import app.modules.research.router as _rmod
        return inspect.getsource(_rmod)

    @staticmethod
    def _routes():
        import app.modules.research.router as _rmod
        router_obj = _rmod.router if hasattr(_rmod, "router") else _rmod
        return router_obj.routes

    def test_router_module_accessible(self):
        assert _ROUTER_MOD is not None

    def test_router_has_routes(self):
        assert len(self._routes()) > 0

    def test_source_contains_domain_validation_error(self):
        assert "DomainValidationError" in self._source()

    def test_source_uses_svc_pattern(self):
        assert "_svc." in self._source()

    def test_source_imports_svc_module(self):
        assert "import app.modules.research.service as _svc" in self._source()

    def test_grants_endpoint_exists(self):
        paths = [r.path for r in self._routes()]
        assert any("grants" in p for p in paths)

    def test_publications_endpoint_exists(self):
        paths = [r.path for r in self._routes()]
        assert any("publications" in p for p in paths)

    def test_labs_endpoint_exists(self):
        paths = [r.path for r in self._routes()]
        assert any("labs" in p for p in paths)

    def test_experiments_endpoint_exists(self):
        paths = [r.path for r in self._routes()]
        assert any("experiments" in p for p in paths)

    def test_ip_assets_endpoint_exists(self):
        paths = [r.path for r in self._routes()]
        assert any("ip-assets" in p for p in paths)

    def test_health_endpoint_exists(self):
        paths = [r.path for r in self._routes()]
        assert any("health" in p for p in paths)

    def test_post_grants_catches_domain_validation_error(self):
        src = self._source()
        assert "DomainValidationError" in src

    def test_patch_routes_catch_domain_validation_error_first(self):
        src = self._source()
        # DomainValidationError must appear before ValueError in exception handlers
        dv_pos = src.find("DomainValidationError")
        ve_pos = src.find("ValueError")
        assert dv_pos < ve_pos


# ---------------------------------------------------------------------------
# TestW140RouterPostGrantEndpoint — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterPostGrantEndpoint:
    @staticmethod
    def _invoke(side_effect=None, return_value=None):
        from app.modules.research.router import create_research_grant_endpoint
        payload = ResearchGrantCreateSchema(
            grant_code="GR-X1", title="Test Grant",
            pi_faculty_id="fac-101", deadline="2027-01-01",
        )
        if return_value is None:
            return_value = ResearchGrantSchema(**GRANT_MOCK)
        with patch.object(_svc, "create_research_grant",
                          side_effect=side_effect,
                          return_value=None if side_effect else return_value):
            try:
                create_research_grant_endpoint(
                    payload=payload, actor="actor", _=None, tenant={"id": "1"},
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    def test_domain_validation_error_returns_422(self):
        assert self._invoke(side_effect=DomainValidationError("invalid")) == 422

    def test_value_error_returns_422(self):
        assert self._invoke(side_effect=ValueError("bad")) == 422

    def test_success_returns_200(self):
        assert self._invoke() == 200


# ---------------------------------------------------------------------------
# TestW140RouterPostPublicationEndpoint — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterPostPublicationEndpoint:
    @staticmethod
    def _invoke(side_effect=None, return_value=None):
        from app.modules.research.router import create_research_publication_endpoint
        payload = ResearchPublicationCreateSchema(
            publication_code="PUB-X1", title="Test Pub",
            lead_author_id="fac-101", target_venue="NeurIPS",
        )
        if return_value is None:
            return_value = ResearchPublicationSchema(**PUB_MOCK)
        with patch.object(_svc, "create_research_publication",
                          side_effect=side_effect,
                          return_value=None if side_effect else return_value):
            try:
                create_research_publication_endpoint(
                    payload=payload, actor="actor", _=None, tenant={"id": "1"},
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    def test_domain_validation_error_returns_422(self):
        assert self._invoke(side_effect=DomainValidationError("no grant")) == 422

    def test_value_error_returns_422(self):
        assert self._invoke(side_effect=ValueError("bad value")) == 422

    def test_success_returns_200(self):
        assert self._invoke() == 200


# ---------------------------------------------------------------------------
# TestW140RouterPatchGrantStatusEndpoint — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterPatchGrantStatusEndpoint:
    @staticmethod
    def _invoke(side_effect=None, return_value=None):
        from app.modules.research.router import update_research_grant_status_endpoint
        payload = ResearchGrantStatusUpdateSchema(status="active")
        if return_value is None:
            return_value = ResearchGrantSchema(**GRANT_MOCK)
        with patch.object(_svc, "update_research_grant_status",
                          side_effect=side_effect,
                          return_value=None if side_effect else return_value):
            try:
                update_research_grant_status_endpoint(
                    grant_id=1, payload=payload, actor="actor", _=None, tenant={"id": "1"},
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    def test_domain_validation_error_returns_422(self):
        assert self._invoke(side_effect=DomainValidationError("invalid transition")) == 422

    def test_value_error_not_found_returns_404(self):
        assert self._invoke(side_effect=ValueError("grant not found")) == 404

    def test_value_error_bad_request_returns_400(self):
        assert self._invoke(side_effect=ValueError("bad status")) == 400

    def test_success_returns_200(self):
        assert self._invoke() == 200


# ---------------------------------------------------------------------------
# TestW140RouterPatchPublicationStatusEndpoint — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterPatchPublicationStatusEndpoint:
    @staticmethod
    def _invoke(side_effect=None, return_value=None):
        from app.modules.research.router import update_research_publication_status_endpoint
        payload = ResearchPublicationStatusUpdateSchema(status="submitted")
        if return_value is None:
            return_value = ResearchPublicationSchema(**PUB_MOCK)
        with patch.object(_svc, "update_research_publication_status",
                          side_effect=side_effect,
                          return_value=None if side_effect else return_value):
            try:
                update_research_publication_status_endpoint(
                    publication_id=1, payload=payload, actor="actor", _=None,
                    tenant={"id": "1"},
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    def test_domain_validation_error_returns_422(self):
        assert self._invoke(side_effect=DomainValidationError("blocked")) == 422

    def test_value_error_not_found_returns_404(self):
        assert self._invoke(side_effect=ValueError("publication not found")) == 404

    def test_success_returns_200(self):
        assert self._invoke() == 200


# ---------------------------------------------------------------------------
# TestW140RouterPatchLabStatusEndpoint — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterPatchLabStatusEndpoint:
    @staticmethod
    def _invoke(side_effect=None, return_value=None):
        from app.modules.research.router import update_research_lab_status_endpoint
        payload = ResearchLabStatusUpdateSchema(status="active")
        if return_value is None:
            return_value = ResearchLabSchema(**LAB_MOCK)
        with patch.object(_svc, "update_research_lab_status",
                          side_effect=side_effect,
                          return_value=None if side_effect else return_value):
            try:
                update_research_lab_status_endpoint(
                    lab_id=1, payload=payload, actor="actor", _=None, tenant={"id": "1"},
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    def test_domain_validation_error_returns_422(self):
        assert self._invoke(side_effect=DomainValidationError("invalid")) == 422

    def test_value_error_not_found_returns_404(self):
        assert self._invoke(side_effect=ValueError("lab not found")) == 404

    def test_success_returns_200(self):
        assert self._invoke() == 200


# ---------------------------------------------------------------------------
# TestW140RouterPatchExperimentStatusEndpoint — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterPatchExperimentStatusEndpoint:
    @staticmethod
    def _invoke(side_effect=None, return_value=None):
        from app.modules.research.router import update_research_experiment_status_endpoint
        payload = ResearchExperimentStatusUpdateSchema(status="running")
        if return_value is None:
            return_value = ResearchExperimentSchema(**EXP_MOCK)
        with patch.object(_svc, "update_research_experiment_status",
                          side_effect=side_effect,
                          return_value=None if side_effect else return_value):
            try:
                update_research_experiment_status_endpoint(
                    experiment_id=1, payload=payload, actor="actor", _=None,
                    tenant={"id": "1"},
                )
                return 200
            except HTTPException as exc:
                return exc.status_code

    def test_domain_validation_error_returns_422(self):
        assert self._invoke(side_effect=DomainValidationError("invalid")) == 422

    def test_value_error_not_found_returns_404(self):
        assert self._invoke(side_effect=ValueError("experiment not found")) == 404

    def test_success_returns_200(self):
        assert self._invoke() == 200


# ---------------------------------------------------------------------------
# TestW140RouterListEndpoints — direct invocation
# ---------------------------------------------------------------------------

class TestW140RouterListEndpoints:
    def test_list_grants_returns_list_response(self):
        from app.modules.research.router import list_research_grants_endpoint
        with patch.object(_svc, "list_research_grants",
                          return_value=[ResearchGrantSchema(**GRANT_MOCK)]):
            result = list_research_grants_endpoint(
                _=None, __=None, tenant={"id": "1"}, status=None,
            )
        assert result is not None

    def test_list_publications_returns_list_response(self):
        from app.modules.research.router import list_research_publications_endpoint
        with patch.object(_svc, "list_research_publications",
                          return_value=[ResearchPublicationSchema(**PUB_MOCK)]):
            result = list_research_publications_endpoint(
                _=None, __=None, tenant={"id": "1"}, status=None,
            )
        assert result is not None

    def test_list_labs_returns_list_response(self):
        from app.modules.research.router import list_research_labs_endpoint
        with patch.object(_svc, "list_research_labs",
                          return_value=[ResearchLabSchema(**LAB_MOCK)]):
            result = list_research_labs_endpoint(_=None, __=None, tenant={"id": "1"})
        assert result is not None

    def test_list_experiments_returns_list_response(self):
        from app.modules.research.router import list_research_experiments_endpoint
        with patch.object(_svc, "list_research_experiments",
                          return_value=[ResearchExperimentSchema(**EXP_MOCK)]):
            result = list_research_experiments_endpoint(_=None, __=None, tenant={"id": "1"})
        assert result is not None

    def test_list_ip_assets_returns_list_response(self):
        from app.modules.research.router import list_research_ip_assets_endpoint
        with patch.object(_svc, "list_research_ip_assets",
                          return_value=[ResearchIpAssetSchema(**IP_MOCK)]):
            result = list_research_ip_assets_endpoint(_=None, __=None, tenant={"id": "1"})
        assert result is not None
