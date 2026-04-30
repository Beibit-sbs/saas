"""W149 — career_services: Deep domain hardening pack.

Rules from SBS UB FULL SYSTEM HARDENING.md:
- Prove behaviour, not only structure
- validate() before persist()
- fail-closed on external lookup failure

Guard under test:
- W121: create_career_opportunity blocked unless student has active enrollment
"""
from __future__ import annotations

from pathlib import Path

import pytest

import app.modules.career_services.service as svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.career_services.schemas import CareerOpportunityCreateSchema


ACTIVE = {"student_id": 42, "status": "active", "tenant_id": 1}
ENROLLED = {"student_id": 43, "status": "enrolled", "tenant_id": 1}
REGISTERED = {"student_id": 44, "status": "registered", "tenant_id": 1}
WITHDRAWN = {"student_id": 50, "status": "withdrawn", "tenant_id": 1}
EXPELLED = {"student_id": 51, "status": "expelled", "tenant_id": 1}
COMPLETED = {"student_id": 52, "status": "completed", "tenant_id": 1}


def _payload(student_id: int = 42, opportunity_type: str = "internship") -> CareerOpportunityCreateSchema:
    return CareerOpportunityCreateSchema(
        student_id=student_id,
        title="Software Intern",
        company="Acme Corp",
        opportunity_type=opportunity_type,  # type: ignore[arg-type]
    )


class TestConstants:
    def test_status_set_type(self):
        assert isinstance(svc._CAREER_ACCESS_ENROLLMENT_STATUSES, frozenset)

    def test_active_allowed(self):
        assert "active" in svc._CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_enrolled_allowed(self):
        assert "enrolled" in svc._CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_registered_allowed(self):
        assert "registered" in svc._CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_withdrawn_blocked(self):
        assert "withdrawn" not in svc._CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_expelled_blocked(self):
        assert "expelled" not in svc._CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_completed_blocked(self):
        assert "completed" not in svc._CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_open_cap_dict_exists(self):
        assert isinstance(svc._OPPORTUNITY_TYPE_MAX_OPEN, dict)

    def test_review_cap_dict_exists(self):
        assert isinstance(svc._OPPORTUNITY_PIPELINE_MAX_REVIEW, dict)


class TestW121Guard:
    def test_unknown_student_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no enrollment records found"):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=999,
                opportunity_type="internship",
            )

    def test_withdrawn_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [WITHDRAWN],
        )
        with pytest.raises(DomainValidationError, match="not actively enrolled"):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=50,
                opportunity_type="job",
            )

    def test_expelled_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [EXPELLED],
        )
        with pytest.raises(DomainValidationError):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=51,
                opportunity_type="job",
            )

    def test_completed_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [COMPLETED],
        )
        with pytest.raises(DomainValidationError):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=52,
                opportunity_type="mentorship",
            )

    def test_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [ACTIVE],
        )
        svc._check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=42,
            opportunity_type="internship",
        )

    def test_enrolled_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [ENROLLED],
        )
        svc._check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=43,
            opportunity_type="internship",
        )

    def test_registered_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [REGISTERED],
        )
        svc._check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=44,
            opportunity_type="internship",
        )

    def test_case_insensitive_status_passes(self, monkeypatch):
        mixed = {"student_id": 42, "status": "Active", "tenant_id": 1}
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity, tenant_id: [mixed],
        )
        svc._check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1,
            student_id=42,
            opportunity_type="internship",
        )


class TestFailClosed:
    def test_lookup_exception_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise RuntimeError("db down")

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="lookup failed"):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=42,
                opportunity_type="internship",
            )

    def test_lookup_error_contains_student_id(self, monkeypatch):
        def boom(entity, tenant_id):
            raise Exception("boom")

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="student_id=42"):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1,
                student_id=42,
                opportunity_type="internship",
            )

    def test_wrong_tenant_has_no_enrollment(self, monkeypatch):
        def mock_list(entity, tenant_id):
            if entity == "enrollments" and tenant_id == 1:
                return [ACTIVE]
            return []

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        with pytest.raises(DomainValidationError):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=2,
                student_id=42,
                opportunity_type="internship",
            )


class TestCreateOpportunity:
    def _setup_ok(self, monkeypatch, enrollments, opportunities=None):
        opportunities = opportunities or []

        def mock_list(entity, tenant_id):
            if entity == "enrollments":
                return enrollments
            if entity == "career_opportunities":
                return opportunities
            return []

        def mock_create(entity, payload, tenant_id):
            row = dict(payload)
            row["id"] = 501
            row["tenant_id"] = str(tenant_id)
            return row

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.career_services.service.create_entity_for_tenant", mock_create)
        monkeypatch.setattr("app.modules.career_services.service.log_admin_action", lambda *a, **k: None)

    def test_active_student_allows_create(self, monkeypatch):
        self._setup_ok(monkeypatch, enrollments=[ACTIVE])
        result = svc.create_career_opportunity(1, _payload(42), actor="admin")
        assert result.id == 501

    def test_withdrawn_blocks_create(self, monkeypatch):
        self._setup_ok(monkeypatch, enrollments=[WITHDRAWN])
        with pytest.raises(DomainValidationError):
            svc.create_career_opportunity(1, _payload(50), actor="admin")

    def test_unknown_student_blocks_create(self, monkeypatch):
        self._setup_ok(monkeypatch, enrollments=[])
        with pytest.raises(DomainValidationError):
            svc.create_career_opportunity(1, _payload(999), actor="admin")

    def test_validate_before_persist_when_guard_fails(self, monkeypatch):
        calls = []

        def mock_list(entity, tenant_id):
            if entity == "enrollments":
                return [WITHDRAWN]
            return []

        def mock_create(entity, payload, tenant_id):
            calls.append(entity)
            return {"id": 1}

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.career_services.service.create_entity_for_tenant", mock_create)
        monkeypatch.setattr("app.modules.career_services.service.log_admin_action", lambda *a, **k: None)

        with pytest.raises(DomainValidationError):
            svc.create_career_opportunity(1, _payload(50), actor="admin")

        assert "career_opportunities" not in calls

    def test_guard_runs_before_opportunity_caps(self, monkeypatch):
        order = []

        def mock_list(entity, tenant_id):
            order.append(entity)
            if entity == "enrollments":
                return []
            return []

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.career_services.service.create_entity_for_tenant", lambda *a, **k: {"id": 1})
        monkeypatch.setattr("app.modules.career_services.service.log_admin_action", lambda *a, **k: None)

        with pytest.raises(DomainValidationError):
            svc.create_career_opportunity(1, _payload(999), actor="admin")

        assert order[0] == "enrollments"


class TestOpenAndReviewCaps:
    def _setup(self, monkeypatch, existing):
        def mock_list(entity, tenant_id):
            if entity == "enrollments":
                return [ACTIVE]
            if entity == "career_opportunities":
                return existing
            return []

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.career_services.service.create_entity_for_tenant", lambda e, p, t: {**p, "id": 1, "tenant_id": str(t)})
        monkeypatch.setattr("app.modules.career_services.service.log_admin_action", lambda *a, **k: None)

    def test_open_cap_blocks_internship_at_2(self, monkeypatch):
        existing = [
            {"student_id": 42, "opportunity_type": "internship", "status": "open"},
            {"student_id": 42, "opportunity_type": "internship", "status": "open"},
        ]
        self._setup(monkeypatch, existing)
        with pytest.raises(ValueError, match="max"):
            svc.create_career_opportunity(1, _payload(42, "internship"), actor="admin")

    def test_open_cap_allows_below_limit(self, monkeypatch):
        existing = [{"student_id": 42, "opportunity_type": "internship", "status": "open"}]
        self._setup(monkeypatch, existing)
        result = svc.create_career_opportunity(1, _payload(42, "internship"), actor="admin")
        assert result.id == 1

    def test_review_cap_blocks_when_reached(self, monkeypatch):
        existing = [
            {"student_id": 42, "opportunity_type": "internship", "status": "in_review"},
            {"student_id": 42, "opportunity_type": "internship", "status": "in_review"},
            {"student_id": 42, "opportunity_type": "internship", "status": "in_review"},
        ]
        self._setup(monkeypatch, existing)
        with pytest.raises(ValueError, match="pipeline cap"):
            svc.create_career_opportunity(1, _payload(42, "internship"), actor="admin")


class TestTenantIsolation:
    def test_list_opportunities_scoped(self, monkeypatch):
        captured = []

        def mock_list(entity, tenant_id):
            captured.append((entity, tenant_id))
            return []

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        svc.list_career_opportunities(tenant_id=77)
        assert captured == [("career_opportunities", 77)]

    def test_guard_uses_enrollments_entity(self, monkeypatch):
        captured = []

        def mock_list(entity, tenant_id):
            captured.append((entity, tenant_id))
            return []

        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", mock_list)
        with pytest.raises(DomainValidationError):
            svc._check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=5,
                student_id=404,
                opportunity_type="job",
            )
        assert captured[0] == ("enrollments", 5)


class TestRouterStructure:
    def _router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/career_services/router.py").read_text(encoding="utf-8")

    def test_router_imports_service_alias(self):
        source = self._router_source()
        assert "import app.modules.career_services.service as _svc" in source

    def test_router_has_no_direct_service_symbols(self):
        source = self._router_source()
        assert "from app.modules.career_services.service import" not in source

    def test_create_endpoint_catches_domain_validation_error(self):
        source = self._router_source()
        assert "DomainValidationError" in source
        assert "422" in source

    def test_router_has_expected_routes(self):
        from app.modules.career_services import router as router_obj

        paths = {r.path for r in router_obj.routes}
        assert "/api/admin/career-services" in paths
        assert "/api/admin/career-services/{opportunity_id}/status" in paths
        assert "/api/admin/career-services/brain-context" in paths


class TestUpdateStatusBehavior:
    def _setup(self, monkeypatch, rows):
        monkeypatch.setattr("app.modules.career_services.service.list_entities_for_tenant", lambda e, t: rows)
        monkeypatch.setattr(
            "app.modules.career_services.service.update_entity_for_tenant",
            lambda e, _id, payload, t: {**payload, "id": _id, "tenant_id": str(t)},
        )
        monkeypatch.setattr("app.modules.career_services.service.log_admin_action", lambda *a, **k: None)

    def test_not_found_returns_value_error(self, monkeypatch):
        self._setup(monkeypatch, rows=[])
        with pytest.raises(ValueError, match="not found"):
            svc.update_career_opportunity_status(
                tenant_id=1,
                opportunity_id=999,
                request=svc.CareerOpportunityStatusUpdateSchema(status="closed"),
                actor="admin",
            )

    def test_invalid_transition_blocked(self, monkeypatch):
        self._setup(monkeypatch, rows=[{"id": 1, "status": "archived"}])
        with pytest.raises(ValueError, match="not allowed"):
            svc.update_career_opportunity_status(
                tenant_id=1,
                opportunity_id=1,
                request=svc.CareerOpportunityStatusUpdateSchema(status="open"),
                actor="admin",
            )
