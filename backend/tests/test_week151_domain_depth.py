"""W151 — communications: deep domain hardening pack.

Guard under test (W117):
- student-targeted message blocked when no active enrollments
- student-targeted message blocked when recipients_count > active enrollment population
- lookup failure is fail-closed
- validate-before-persist in create_message
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.communications.service as svc


TENANT_ID = 501


def _payload(**overrides):
    base = {
        "message_code": "MSG-151-1",
        "title": "System notice",
        "message_type": "announcement",
        "target_audience": "students",
        "status": "draft",
        "recipients_count": 10,
        "delivered_count": 0,
        "opened_count": 0,
    }
    base.update(overrides)
    return base


def _enrollment(status: str):
    return {"id": 1, "status": status}


class TestConstants:
    def test_student_targets_contains_students(self):
        assert "students" in svc._STUDENT_AUDIENCE_TARGETS

    def test_student_targets_contains_aliases(self):
        assert "student" in svc._STUDENT_AUDIENCE_TARGETS
        assert "all_students" in svc._STUDENT_AUDIENCE_TARGETS

    def test_active_enrollment_statuses_contains_core(self):
        assert "active" in svc._ACTIVE_ENROLLMENT_STATUSES
        assert "enrolled" in svc._ACTIVE_ENROLLMENT_STATUSES
        assert "registered" in svc._ACTIVE_ENROLLMENT_STATUSES

    def test_guard_callable(self):
        assert callable(svc._check_student_audience_population)


class TestNonStudentBypass:
    @pytest.mark.parametrize("audience", ["staff", "alumni", "faculty", "all", "parents"])
    def test_non_student_audience_skips_enrollment_lookup(self, audience):
        with patch("app.modules.communications.service.list_entities_for_tenant") as mock_list:
            svc._check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience=audience,
                recipients_count=100,
                message_code="M1",
            )
            mock_list.assert_not_called()


class TestFailClosedLookup:
    def test_lookup_exception_blocks(self):
        with patch(
            "app.modules.communications.service.list_entities_for_tenant",
            side_effect=RuntimeError("db unavailable"),
        ):
            with pytest.raises(DomainValidationError, match="lookup failed"):
                svc._check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=10,
                    message_code="M2",
                )

    def test_lookup_exception_chains_cause(self):
        with patch(
            "app.modules.communications.service.list_entities_for_tenant",
            side_effect=RuntimeError("network"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=10,
                    message_code="M3",
                )
            assert exc_info.value.__cause__ is not None


class TestNoActivePopulation:
    @pytest.mark.parametrize("statuses", [["withdrawn", "completed"], ["inactive"], ["suspended", "graduated"], []])
    def test_no_active_population_blocks(self, statuses):
        rows = [_enrollment(s) for s in statuses]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError, match="no active enrollments"):
                svc._check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=1,
                    message_code="M4",
                )


class TestPopulationCap:
    def test_recipients_above_active_population_blocks(self):
        rows = [_enrollment("active") for _ in range(5)]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError, match="exceeds active enrollment population"):
                svc._check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=6,
                    message_code="M5",
                )

    @pytest.mark.parametrize("recipients", [0, 1, 5])
    def test_recipients_within_active_population_passes(self, recipients):
        rows = [_enrollment("active") for _ in range(5)]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            svc._check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience="students",
                recipients_count=recipients,
                message_code="M6",
            )


class TestStatusNormalization:
    @pytest.mark.parametrize("status", ["active", "ACTIVE", " enrolled ", "Registered", "registered"])
    def test_active_like_statuses_count_as_active(self, status):
        rows = [_enrollment(status)]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            svc._check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience="students",
                recipients_count=1,
                message_code="M7",
            )


class TestCreateMessageIntegration:
    def test_guard_blocks_before_persist_when_no_population(self):
        payload = _payload(recipients_count=1)
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=[]), patch(
            "app.modules.communications.service.create_entity_for_tenant"
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                svc.create_message(payload, TENANT_ID)
            mock_create.assert_not_called()

    def test_guard_blocks_before_persist_when_over_count(self):
        payload = _payload(recipients_count=10)

        def _list(entity_name, tenant_id):
            assert tenant_id == TENANT_ID
            if entity_name == "enrollments":
                return [_enrollment("active") for _ in range(3)]
            return []

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.communications.service.create_entity_for_tenant"
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                svc.create_message(payload, TENANT_ID)
            mock_create.assert_not_called()

    def test_guard_passes_and_persists_when_population_valid(self):
        payload = _payload(recipients_count=3)

        def _list(entity_name, tenant_id):
            if entity_name == "enrollments":
                return [_enrollment("active") for _ in range(5)]
            if entity_name == "communication_messages":
                return []
            if entity_name == "communication_broadcast_audits":
                return []
            if entity_name == "communication_broadcast_risk_alerts":
                return []
            return []

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.communications.service.create_entity_for_tenant",
            return_value={"id": 9001, **payload},
        ) as mock_create:
            result = svc.create_message(payload, TENANT_ID)
            assert result["id"] == 9001
            mock_create.assert_called()

    def test_non_student_audience_does_not_require_enrollments(self):
        payload = _payload(target_audience="staff", recipients_count=999)

        def _list(entity_name, tenant_id):
            if entity_name == "communication_messages":
                return []
            if entity_name == "communication_broadcast_audits":
                return []
            if entity_name == "communication_broadcast_risk_alerts":
                return []
            return []

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.communications.service.create_entity_for_tenant",
            return_value={"id": 42, **payload},
        ) as mock_create:
            result = svc.create_message(payload, TENANT_ID)
            assert result["id"] == 42
            created_entities = [call.args[0] for call in mock_create.call_args_list]
            assert "communication_messages" in created_entities


class TestTargetAudienceAliases:
    @pytest.mark.parametrize("audience", ["students", "student", "all_students", " Students "])
    def test_student_aliases_trigger_guard(self, audience):
        rows = [_enrollment("active")]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            svc._check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience=audience,
                recipients_count=1,
                message_code="M8",
            )


class TestOrderOfOperations:
    def test_guard_runs_before_message_cap_lookup(self):
        payload = _payload(recipients_count=4)
        call_order: list[str] = []

        def _list(entity_name, tenant_id):
            call_order.append(entity_name)
            if entity_name == "enrollments":
                return [_enrollment("active") for _ in range(3)]
            if entity_name == "communication_messages":
                pytest.fail("communication_messages lookup must not happen after guard failure")
            return []

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.communications.service.create_entity_for_tenant"
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                svc.create_message(payload, TENANT_ID)
            mock_create.assert_not_called()

        assert call_order[0] == "enrollments"


class TestMetadataAndTenantIsolation:
    def test_error_contains_message_code_and_audience(self):
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=1,
                    message_code="CODE-X",
                )
        msg = str(exc_info.value)
        assert "CODE-X" in msg
        assert "students" in msg

    def test_guard_uses_current_tenant_scope(self):
        seen_tenants: list[int] = []

        def _list(entity_name, tenant_id):
            seen_tenants.append(tenant_id)
            return [_enrollment("active")]

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list):
            svc._check_student_audience_population(
                tenant_id=777,
                target_audience="students",
                recipients_count=1,
                message_code="M9",
            )

        assert seen_tenants == [777]


class TestRouterStructure:
    def _router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/communications/router.py").read_text(encoding="utf-8")

    def test_router_imports_service_alias(self):
        source = self._router_source()
        assert "import app.modules.communications.service as _svc" in source

    def test_router_has_no_direct_service_imports(self):
        source = self._router_source()
        assert "from app.modules.communications.service import" not in source

    def test_create_endpoint_catches_domain_validation_error(self):
        source = self._router_source()
        assert "except (ValueError, DomainValidationError) as exc" in source
        assert "status_code=422" in source

    def test_router_has_expected_paths(self):
        from app.modules.communications import router as router_obj

        paths = {r.path for r in router_obj.router.routes}
        assert "/api/admin/communications/messages" in paths
        assert "/api/admin/communications/brain-context" in paths
