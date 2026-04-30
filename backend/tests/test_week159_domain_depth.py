"""W159 — delinquency_collections: Router _svc Hardening (Enrollment History Guard).

W115: create_delinquency_record blocked if student has no enrollment history.
W87: legal escalation thresholds.
W23: per-stage active cap.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import app.modules.delinquency_collections.service as _svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.delinquency_collections.schemas import (
    DelinquencyEscalationUpdateSchema,
    DelinquencyRecordCreateSchema,
)


class TestConstants:
    def test_active_statuses_dc_exists(self):
        assert isinstance(_svc._ACTIVE_STATUSES_DC, frozenset)
        assert "open" in _svc._ACTIVE_STATUSES_DC
        assert "in_review" in _svc._ACTIVE_STATUSES_DC
        assert "escalated" in _svc._ACTIVE_STATUSES_DC

    def test_stage_caps_exist(self):
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["stage_1"] == 5
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["stage_2"] == 3
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["stage_3"] == 1
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["legal"] == 1

    def test_legal_thresholds_exist(self):
        assert _svc._LEGAL_ESCALATION_MIN_AMOUNT_DUE == 500.0
        assert _svc._LEGAL_ESCALATION_MIN_DAYS_OVERDUE == 90

    def test_legal_stage_set(self):
        assert "legal" in _svc._LEGAL_ESCALATION_STAGES

    def test_enrollment_requirement_flag(self):
        assert _svc._DELINQUENCY_REQUIRES_ENROLLMENT_HISTORY is True


class TestW115EnrollmentGuard:
    def test_guard_callable(self):
        assert callable(_svc._check_student_has_enrollment_history)

    def test_guard_blocks_no_enrollment(self, monkeypatch):
        monkeypatch.setattr(_svc, "list_entities_for_tenant", lambda entity, tid: [])
        with pytest.raises(DomainValidationError, match="no enrollment history"):
            _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

    def test_guard_passes_with_enrollment(self, monkeypatch):
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"student_id": "S001"}] if entity == "enrollments" else [],
        )
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

    def test_guard_case_insensitive(self, monkeypatch):
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"student_id": "s001"}] if entity == "enrollments" else [],
        )
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

    def test_guard_whitespace_trim(self, monkeypatch):
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"student_id": "S001"}] if entity == "enrollments" else [],
        )
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="  S001  ")

    def test_guard_fail_closed_lookup_error(self, monkeypatch):
        def boom(entity, tid):
            raise RuntimeError("db down")

        monkeypatch.setattr(_svc, "list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestW87LegalEscalationGuard:
    def test_guard_callable(self):
        assert callable(_svc._check_legal_escalation_threshold)

    def test_passes_when_both_thresholds_met(self):
        _svc._check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=500.0,
            days_overdue=90,
            target_stage="legal",
        )

    def test_blocks_when_amount_low(self):
        with pytest.raises(DomainValidationError, match="below the legal-action minimum"):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=499.0,
                days_overdue=90,
                target_stage="legal",
            )

    def test_blocks_when_days_low(self):
        with pytest.raises(DomainValidationError, match="below the required minimum"):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=500.0,
                days_overdue=89,
                target_stage="legal",
            )

    def test_blocks_when_both_low(self):
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=100.0,
                days_overdue=20,
                target_stage="legal",
            )
        msg = str(exc_info.value)
        assert "amount_due" in msg and "days_overdue" in msg

    def test_non_legal_stage_bypasses_threshold(self):
        _svc._check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=0.0,
            days_overdue=0,
            target_stage="stage_1",
        )

    def test_negative_amount_blocks(self):
        with pytest.raises(DomainValidationError):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=-1.0,
                days_overdue=100,
                target_stage="legal",
            )

    def test_negative_days_blocks(self):
        with pytest.raises(DomainValidationError):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=600.0,
                days_overdue=-1,
                target_stage="legal",
            )


class TestW23EscalationCapGuard:
    def test_cap_blocks_create_when_limit_reached(self, monkeypatch):
        def mock_list(entity, tid):
            if entity == "enrollments":
                return [{"student_id": "S001"}]
            if entity == "delinquency_records":
                return [
                    {"student_id": "S001", "escalation_stage": "stage_2", "status": "open"},
                    {"student_id": "S001", "escalation_stage": "stage_2", "status": "in_review"},
                    {"student_id": "S001", "escalation_stage": "stage_2", "status": "escalated"},
                ]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        req = DelinquencyRecordCreateSchema(
            student_id="S001",
            invoice_code="INV-1",
            amount_due=1000.0,
            days_overdue=30,
            escalation_stage="stage_2",
            status="open",
        )
        with pytest.raises(ValueError, match="already has 3 active"):
            _svc.create_delinquency_record(1, req, "actor")

    def test_caps_are_stage_specific(self, monkeypatch):
        def mock_list(entity, tid):
            if entity == "enrollments":
                return [{"student_id": "S001"}]
            if entity == "delinquency_records":
                return [{"student_id": "S001", "escalation_stage": "stage_1", "status": "open"}] * 5
            if entity == "collections_agent_records":
                return []
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", lambda entity, data, tid: {"id": 10, **data})
        monkeypatch.setattr("app.modules.delinquency_collections.service.log_admin_action", lambda *a, **k: None)
        monkeypatch.setattr(
            "app.modules.delinquency_collections.service.EventPublisher",
            lambda: type("P", (), {"publish_event": lambda *a, **k: None})(),
        )

        req = DelinquencyRecordCreateSchema(
            student_id="S001",
            invoice_code="INV-2",
            amount_due=1000.0,
            days_overdue=40,
            escalation_stage="stage_2",
            status="open",
        )
        result = _svc.create_delinquency_record(1, req, "actor")
        assert result is not None

    def test_cap_counts_only_active_statuses(self, monkeypatch):
        def mock_list(entity, tid):
            if entity == "enrollments":
                return [{"student_id": "S001"}]
            if entity == "delinquency_records":
                return [{"student_id": "S001", "escalation_stage": "legal", "status": "closed"}]
            if entity == "collections_agent_records":
                return []
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", lambda entity, data, tid: {"id": 11, **data})
        monkeypatch.setattr("app.modules.delinquency_collections.service.log_admin_action", lambda *a, **k: None)
        monkeypatch.setattr(
            "app.modules.delinquency_collections.service.EventPublisher",
            lambda: type("P", (), {"publish_event": lambda *a, **k: None})(),
        )

        req = DelinquencyRecordCreateSchema(
            student_id="S001",
            invoice_code="INV-3",
            amount_due=1200.0,
            days_overdue=120,
            escalation_stage="legal",
            status="open",
        )
        result = _svc.create_delinquency_record(1, req, "actor")
        assert result is not None


class TestTenantIsolation:
    def test_enrollment_lookup_uses_tenant_id(self, monkeypatch):
        calls = []

        def mock_list(entity, tid):
            calls.append((entity, tid))
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        with pytest.raises(DomainValidationError):
            _svc._check_student_has_enrollment_history(tenant_id=77, student_id="S001")
        assert ("enrollments", 77) in calls

    def test_other_tenant_enrollment_does_not_match(self, monkeypatch):
        def mock_list(entity, tid):
            if entity == "enrollments" and tid == 1:
                return [{"student_id": "S001"}]
            if entity == "enrollments" and tid == 2:
                return []
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")
        with pytest.raises(DomainValidationError):
            _svc._check_student_has_enrollment_history(tenant_id=2, student_id="S001")


class TestRouterStructure:
    def _source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/delinquency_collections/router.py").read_text()

    def test_router_imports_service_module_as_svc(self):
        source = self._source()
        assert "import app.modules.delinquency_collections.service as _svc" in source

    def test_router_create_uses_svc_call(self):
        source = self._source()
        assert "_svc.create_delinquency_record" in source

    def test_router_status_uses_svc_call(self):
        source = self._source()
        assert "_svc.update_delinquency_status" in source

    def test_router_escalation_uses_svc_call(self):
        source = self._source()
        assert "_svc.update_delinquency_escalation" in source

    def test_router_has_no_direct_service_import(self):
        source = self._source()
        assert "from app.modules.delinquency_collections.service import" not in source

    def test_router_maps_domain_validation_to_422(self):
        source = self._source()
        assert "except (ValueError, DomainValidationError)" in source
        assert "status_code=422" in source

    def test_router_paths_present(self):
        mod = importlib.import_module("app.modules.delinquency_collections.router")
        paths = [r.path for r in mod.router.routes]
        assert any("/status" in p for p in paths)
        assert any("/escalation" in p for p in paths)
        assert any("{record_id}" in p for p in paths)


class TestErrorHandlingPaths:
    def test_create_blocks_on_missing_enrollment(self, monkeypatch):
        monkeypatch.setattr(_svc, "list_entities_for_tenant", lambda entity, tid: [])
        req = DelinquencyRecordCreateSchema(
            student_id="S404",
            invoice_code="INV-X",
            amount_due=900.0,
            days_overdue=45,
            escalation_stage="stage_1",
            status="open",
        )
        with pytest.raises(DomainValidationError):
            _svc.create_delinquency_record(1, req, "actor")

    def test_escalation_blocks_on_legal_threshold_violation(self, monkeypatch):
        def mock_list(entity, tid):
            if entity == "delinquency_records":
                return [{"id": 1, "student_id": "S001", "amount_due": 100.0, "days_overdue": 30, "status": "open"}]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        req = DelinquencyEscalationUpdateSchema(escalation_stage="legal")
        with pytest.raises(DomainValidationError):
            _svc.update_delinquency_escalation(1, 1, req, "actor")

    def test_not_found_update_returns_none(self, monkeypatch):
        monkeypatch.setattr(_svc, "list_entities_for_tenant", lambda entity, tid: [])
        req = DelinquencyEscalationUpdateSchema(escalation_stage="stage_2")
        assert _svc.update_delinquency_escalation(1, 999, req, "actor") is None
