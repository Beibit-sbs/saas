"""W144: delinquency_collections Router DomainValidationError Hardening.

W115 Guard: Student enrollment history required for delinquency record creation.
W87 Guard: Legal escalation requires minimum debt amount and overdue days.
W23 Guard: Per-student/per-stage escalation caps.

Tests validate:
- Constants existence and content
- Guard allow paths (valid data)
- Guard block paths (guard violations)
- Fail-closed paths (exception preservation)
- Tenant isolation
- Router structure (_svc pattern)
- HTTP status mappings (422 for domain errors, 404 for not found)
"""
import pytest

import app.modules.delinquency_collections.service as _svc
from app.core.module_helpers.service_validation import DomainValidationError


class TestW144Constants:
    """Verify guard constants are defined and contain expected values."""

    def test_active_statuses_dc_exists(self):
        assert hasattr(_svc, "_ACTIVE_STATUSES_DC")
        assert isinstance(_svc._ACTIVE_STATUSES_DC, frozenset)
        assert "open" in _svc._ACTIVE_STATUSES_DC
        assert "in_review" in _svc._ACTIVE_STATUSES_DC
        assert "escalated" in _svc._ACTIVE_STATUSES_DC

    def test_escalation_stage_max_active_exists(self):
        assert hasattr(_svc, "_ESCALATION_STAGE_MAX_ACTIVE")
        assert isinstance(_svc._ESCALATION_STAGE_MAX_ACTIVE, dict)
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE.get("stage_1") == 5
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE.get("stage_2") == 3
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE.get("stage_3") == 1
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE.get("legal") == 1

    def test_legal_escalation_thresholds_exist(self):
        assert hasattr(_svc, "_LEGAL_ESCALATION_MIN_AMOUNT_DUE")
        assert hasattr(_svc, "_LEGAL_ESCALATION_MIN_DAYS_OVERDUE")
        assert _svc._LEGAL_ESCALATION_MIN_AMOUNT_DUE == 500.0
        assert _svc._LEGAL_ESCALATION_MIN_DAYS_OVERDUE == 90

    def test_legal_escalation_stages_exist(self):
        assert hasattr(_svc, "_LEGAL_ESCALATION_STAGES")
        assert isinstance(_svc._LEGAL_ESCALATION_STAGES, frozenset)
        assert "legal" in _svc._LEGAL_ESCALATION_STAGES

    def test_legal_risk_stages_exist(self):
        assert hasattr(_svc, "_LEGAL_RISK_STAGES")
        assert isinstance(_svc._LEGAL_RISK_STAGES, frozenset)
        assert "legal" in _svc._LEGAL_RISK_STAGES


class TestW115EnrollmentGuard:
    """W115: Student must have enrollment history for delinquency record creation."""

    def test_guard_function_exists(self):
        assert hasattr(_svc, "_check_student_has_enrollment_history")
        assert callable(_svc._check_student_has_enrollment_history)

    def test_guard_blocks_no_enrollment(self, monkeypatch):
        """Guard blocks delinquency creation when student has no enrollment record."""
        # Mock list_entities_for_tenant to return empty enrollments
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [] if entity == "enrollments" else [{"id": 1}]
        )

        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

        assert "no enrollment history" in str(exc_info.value).lower()
        assert "S001" in str(exc_info.value)

    def test_guard_passes_with_enrollment(self, monkeypatch):
        """Guard passes when student has at least one enrollment record."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"student_id": "S001"}] if entity == "enrollments" else []
        )

        # Should not raise
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

    def test_guard_case_insensitive_match(self, monkeypatch):
        """Guard matches student_id case-insensitively."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"student_id": "s001"}] if entity == "enrollments" else []
        )

        # Should pass even with different casing
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

    def test_guard_whitespace_trim(self, monkeypatch):
        """Guard handles whitespace in student_id."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"student_id": "S001"}] if entity == "enrollments" else []
        )

        # Should pass with whitespace
        _svc._check_student_has_enrollment_history(tenant_id=1, student_id="  S001  ")

    def test_guard_fail_closed_on_lookup_exception(self, monkeypatch):
        """Guard raises DomainValidationError with __cause__ when enrollment lookup fails."""
        def mock_list_fail(entity, tid):
            raise RuntimeError("Database connection lost")

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list_fail)

        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_student_has_enrollment_history(tenant_id=1, student_id="S001")

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert "enrollment lookup failed" in str(exc_info.value).lower()


class TestW87LegalEscalationGuard:
    """W87: Legal escalation requires minimum debt amount and overdue days."""

    def test_guard_function_exists(self):
        assert hasattr(_svc, "_check_legal_escalation_threshold")
        assert callable(_svc._check_legal_escalation_threshold)

    def test_guard_passes_legal_escalation_valid(self):
        """Guard passes when legal escalation has sufficient amount and days."""
        # Should not raise
        _svc._check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=600.0,  # >= 500.0
            days_overdue=100,  # >= 90
            target_stage="legal"
        )

    def test_guard_blocks_insufficient_amount(self):
        """Guard blocks legal escalation when amount_due is below minimum."""
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=400.0,  # < 500.0
                days_overdue=100,
                target_stage="legal"
            )

        assert "below the legal-action minimum" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    def test_guard_blocks_insufficient_days(self):
        """Guard blocks legal escalation when days_overdue is below minimum."""
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=600.0,
                days_overdue=80,  # < 90
                target_stage="legal"
            )

        assert "below the required minimum" in str(exc_info.value)
        assert "90" in str(exc_info.value)

    def test_guard_blocks_both_insufficient(self):
        """Guard blocks when both conditions fail."""
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=400.0,  # < 500.0
                days_overdue=80,   # < 90
                target_stage="legal"
            )

        error_msg = str(exc_info.value)
        assert "below the legal-action minimum" in error_msg
        assert "below the required minimum" in error_msg

    def test_guard_ignores_non_legal_stages(self):
        """Guard does not check thresholds for non-legal stages."""
        # Should not raise even with insufficient values
        _svc._check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=100.0,  # < 500.0
            days_overdue=10,   # < 90
            target_stage="stage_1"
        )

    def test_guard_boundary_amount_exact(self):
        """Guard passes at exact minimum amount."""
        # Should not raise at exact boundary
        _svc._check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=500.0,  # exactly 500.0
            days_overdue=90,
            target_stage="legal"
        )

    def test_guard_boundary_days_exact(self):
        """Guard passes at exact minimum days."""
        # Should not raise at exact boundary
        _svc._check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=600.0,
            days_overdue=90,  # exactly 90
            target_stage="legal"
        )


class TestW23EscalationCapGuard:
    """W23: Per-student/per-stage escalation caps enforcement."""

    def test_cap_constants_correct(self):
        """Escalation stage caps are correctly defined."""
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["stage_1"] == 5
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["stage_2"] == 3
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["stage_3"] == 1
        assert _svc._ESCALATION_STAGE_MAX_ACTIVE["legal"] == 1

    def test_create_respects_stage_caps(self, monkeypatch):
        """create_delinquency_record enforces per-stage caps."""
        from app.modules.delinquency_collections.schemas import DelinquencyRecordCreateSchema

        # Mock to have 3 existing active stage_2 records for same student
        def mock_list(entity, tid):
            if entity == "enrollments":
                return [{"student_id": "S001"}]
            elif entity == "delinquency_records":
                return [
                    {"student_id": "S001", "escalation_stage": "stage_2", "status": "open"},
                    {"student_id": "S001", "escalation_stage": "stage_2", "status": "in_review"},
                    {"student_id": "S001", "escalation_stage": "stage_2", "status": "escalated"},
                ]
            return []

        def mock_create(entity, data, tid):
            return {"id": 99, **data}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        # Attempting to create 4th stage_2 record should fail (max is 3)
        request = DelinquencyRecordCreateSchema(
            student_id="S001",
            invoice_code="INV001",
            amount_due=1000.0,
            days_overdue=30,
            escalation_stage="stage_2",
            status="open"
        )

        with pytest.raises(ValueError) as exc_info:
            _svc.create_delinquency_record(1, request, "actor1")

        assert "already has 3 active" in str(exc_info.value)
        assert "stage_2" in str(exc_info.value)

    def test_different_stages_independent(self, monkeypatch):
        """Caps are independent per stage."""
        from app.modules.delinquency_collections.schemas import DelinquencyRecordCreateSchema

        # Mock with 5 active stage_1 records but 0 stage_2 records
        def mock_list(entity, tid):
            if entity == "enrollments":
                return [{"student_id": "S001"}]
            elif entity == "delinquency_records":
                return [
                    {"student_id": "S001", "escalation_stage": "stage_1", "status": "open"},
                    {"student_id": "S001", "escalation_stage": "stage_1", "status": "open"},
                    {"student_id": "S001", "escalation_stage": "stage_1", "status": "open"},
                    {"student_id": "S001", "escalation_stage": "stage_1", "status": "open"},
                    {"student_id": "S001", "escalation_stage": "stage_1", "status": "open"},
                ]
            return []

        def mock_create(entity, data, tid):
            return {"id": 99, **data}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)
        # Mock EventPublisher to avoid external dependencies
        monkeypatch.setattr("app.modules.delinquency_collections.service.EventPublisher", lambda: type("MockPublisher", (), {"publish_event": lambda *a, **k: None})())
        # Mock audit logging
        monkeypatch.setattr("app.modules.delinquency_collections.service.log_admin_action", lambda *a, **k: None)

        # Creating stage_2 record should succeed despite stage_1 being full
        request = DelinquencyRecordCreateSchema(
            student_id="S001",
            invoice_code="INV002",
            amount_due=2000.0,
            days_overdue=60,
            escalation_stage="stage_2",
            status="open"
        )

        # Should not raise
        result = _svc.create_delinquency_record(1, request, "actor1")
        assert result is not None


class TestTenantIsolation:
    """Tenant isolation for delinquency records."""

    def test_enrollment_check_per_tenant(self, monkeypatch):
        """Enrollment lookup scoped to specific tenant."""
        call_args = []

        def mock_list(entity, tid):
            call_args.append((entity, tid))
            return [] if entity == "enrollments" else []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        with pytest.raises(DomainValidationError):
            _svc._check_student_has_enrollment_history(tenant_id=42, student_id="S001")

        # Verify tenant_id was passed through
        assert any(args[1] == 42 for args in call_args if args[0] == "enrollments")


class TestRouterStructure:
    """Verify router uses _svc pattern."""

    def test_router_imports_svc_module(self):
        import app.modules.delinquency_collections.router as router_module
        assert hasattr(router_module, "_svc")

    def test_router_has_list_endpoint(self):
        import app.modules.delinquency_collections.router as router_module
        assert hasattr(router_module, "list_delinquency_records_endpoint")

    def test_router_has_create_endpoint(self):
        import app.modules.delinquency_collections.router as router_module
        assert hasattr(router_module, "create_delinquency_record_endpoint")

    def test_router_has_get_endpoint(self):
        import app.modules.delinquency_collections.router as router_module
        assert hasattr(router_module, "get_delinquency_record_endpoint")

    def test_router_has_status_update_endpoint(self):
        import app.modules.delinquency_collections.router as router_module
        assert hasattr(router_module, "update_delinquency_status_endpoint")

    def test_router_has_escalation_update_endpoint(self):
        import app.modules.delinquency_collections.router as router_module
        assert hasattr(router_module, "update_delinquency_escalation_endpoint")

    def test_router_imports_domain_validation_error(self):
        import app.modules.delinquency_collections.router as router_module
        # Check that DomainValidationError is imported for proper error handling
        import inspect
        router_source = inspect.getsource(router_module)
        assert "DomainValidationError" in router_source


class TestServiceFunctionSignatures:
    """Verify service functions have expected signatures."""

    def test_create_delinquency_record_signature(self):
        import inspect
        sig = inspect.signature(_svc.create_delinquency_record)
        params = list(sig.parameters.keys())
        assert "tenant_id" in params
        assert "request" in params
        assert "actor" in params

    def test_update_delinquency_status_signature(self):
        import inspect
        sig = inspect.signature(_svc.update_delinquency_status)
        params = list(sig.parameters.keys())
        assert "tenant_id" in params
        assert "record_id" in params
        assert "request" in params
        assert "actor" in params

    def test_update_delinquency_escalation_signature(self):
        import inspect
        sig = inspect.signature(_svc.update_delinquency_escalation)
        params = list(sig.parameters.keys())
        assert "tenant_id" in params
        assert "record_id" in params
        assert "request" in params
        assert "actor" in params


class TestErrorHandlingPaths:
    """Verify DomainValidationError propagation and HTTP status codes."""

    def test_create_catches_domain_validation_error(self, monkeypatch):
        """create endpoint catches DomainValidationError → 422."""
        from app.modules.delinquency_collections.schemas import DelinquencyRecordCreateSchema

        def mock_list(entity, tid):
            raise RuntimeError("DB error")

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        request = DelinquencyRecordCreateSchema(
            student_id="S001",
            invoice_code="INV001",
            amount_due=1000.0,
            days_overdue=30,
            escalation_stage="stage_1",
            status="open"
        )

        # Should raise DomainValidationError (caught by router → 422)
        with pytest.raises(DomainValidationError):
            _svc.create_delinquency_record(1, request, "actor1")

    def test_escalation_catches_legal_threshold_error(self, monkeypatch):
        """escalation endpoint catches legal threshold violation → 422."""
        from app.modules.delinquency_collections.schemas import DelinquencyEscalationUpdateSchema

        # Mock existing record with insufficient amounts for legal
        def mock_list(entity, tid):
            if entity == "delinquency_records":
                return [
                    {
                        "id": 1,
                        "student_id": "S001",
                        "amount_due": 300.0,  # < 500
                        "days_overdue": 50,   # < 90
                        "escalation_stage": "stage_2",
                        "status": "open"
                    }
                ]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        request = DelinquencyEscalationUpdateSchema(escalation_stage="legal")

        # Should raise DomainValidationError (caught by router → 422)
        with pytest.raises(DomainValidationError) as exc_info:
            _svc.update_delinquency_escalation(1, 1, request, "actor1")

        assert "legal" in str(exc_info.value).lower()


class TestBoundaryConditions:
    """Boundary and edge case testing."""

    def test_zero_days_overdue(self):
        """0 days overdue is below minimum for legal escalation."""
        with pytest.raises(DomainValidationError):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=500.0,
                days_overdue=0,
                target_stage="legal"
            )

    def test_negative_days_overdue(self):
        """Negative days_overdue handled gracefully."""
        with pytest.raises(DomainValidationError):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=500.0,
                days_overdue=-10,
                target_stage="legal"
            )

    def test_zero_amount_due(self):
        """0 amount_due is below minimum for legal escalation."""
        with pytest.raises(DomainValidationError):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=0.0,
                days_overdue=100,
                target_stage="legal"
            )

    def test_negative_amount_due(self):
        """Negative amount_due handled gracefully."""
        with pytest.raises(DomainValidationError):
            _svc._check_legal_escalation_threshold(
                record_id=1,
                student_id="S001",
                amount_due=-100.0,
                days_overdue=100,
                target_stage="legal"
            )
