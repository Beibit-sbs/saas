"""W117 — communications: student audience must match active enrollment population.

Root fix:
- Cross-entity guard in create_message() checks enrollments BEFORE persist.
- target_audience in students/student/all_students requires active enrollments > 0.
- recipients_count must not exceed active enrollment population.
- Lookup failure is fail-closed via DomainValidationError.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.communications.service import (
    _ACTIVE_ENROLLMENT_STATUSES,
    _STUDENT_AUDIENCE_TARGETS,
    _check_student_audience_population,
    create_message,
)


TENANT_ID = 501


def _payload(**overrides):
    base = {
        "message_code": "MSG-117-1",
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


class TestW117Constants:
    def test_student_targets_constant_exists(self):
        assert "students" in _STUDENT_AUDIENCE_TARGETS

    def test_active_enrollment_statuses_constant_exists(self):
        assert "active" in _ACTIVE_ENROLLMENT_STATUSES

    def test_guard_callable(self):
        assert callable(_check_student_audience_population)


class TestW117AudienceNonStudentBypass:
    @pytest.mark.parametrize("audience", ["staff", "alumni", "faculty", "all", "parents"])
    def test_non_student_audience_skips_enrollment_lookup(self, audience):
        with patch("app.modules.communications.service.list_entities_for_tenant") as mock_list:
            _check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience=audience,
                recipients_count=100,
                message_code="M1",
            )
            mock_list.assert_not_called()


class TestW117FailClosedLookup:
    def test_lookup_exception_blocks(self):
        with patch(
            "app.modules.communications.service.list_entities_for_tenant",
            side_effect=RuntimeError("db unavailable"),
        ):
            with pytest.raises(DomainValidationError, match="lookup failed"):
                _check_student_audience_population(
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
                _check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=10,
                    message_code="M3",
                )
            assert exc_info.value.__cause__ is not None


class TestW117NoActivePopulation:
    @pytest.mark.parametrize("statuses", [
        ["withdrawn", "completed"],
        ["inactive"],
        ["suspended", "graduated"],
        [],
    ])
    def test_no_active_population_blocks(self, statuses):
        rows = [_enrollment(s) for s in statuses]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError, match="no active enrollments"):
                _check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=1,
                    message_code="M4",
                )


class TestW117PopulationCap:
    def test_recipients_above_active_population_blocks(self):
        rows = [_enrollment("active") for _ in range(5)]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError, match="exceeds active enrollment population"):
                _check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=6,
                    message_code="M5",
                )

    @pytest.mark.parametrize("recipients", [0, 1, 5])
    def test_recipients_within_active_population_passes(self, recipients):
        rows = [_enrollment("active") for _ in range(5)]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            _check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience="students",
                recipients_count=recipients,
                message_code="M6",
            )


class TestW117StatusNormalization:
    @pytest.mark.parametrize("status", ["active", "ACTIVE", " enrolled ", "Registered", "registered"])
    def test_active_like_statuses_count_as_active(self, status):
        rows = [_enrollment(status)]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            _check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience="students",
                recipients_count=1,
                message_code="M7",
            )


class TestW117CreateMessageIntegration:
    def test_student_guard_blocks_before_persist_when_no_population(self):
        payload = _payload(recipients_count=1)

        with patch(
            "app.modules.communications.service.list_entities_for_tenant",
            return_value=[],
        ), patch(
            "app.modules.communications.service.create_entity_for_tenant"
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                create_message(payload, TENANT_ID)
            mock_create.assert_not_called()

    def test_student_guard_blocks_before_persist_when_over_count(self):
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
                create_message(payload, TENANT_ID)
            mock_create.assert_not_called()

    def test_student_guard_passes_and_persists_when_population_valid(self):
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
            result = create_message(payload, TENANT_ID)
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
            result = create_message(payload, TENANT_ID)
            assert result["id"] == 42
            created_entities = [call.args[0] for call in mock_create.call_args_list]
            assert "communication_messages" in created_entities
            assert "communication_broadcast_audits" in created_entities
            assert "communication_broadcast_risk_alerts" in created_entities


class TestW117TargetAudienceAliases:
    @pytest.mark.parametrize("audience", ["students", "student", "all_students", " Students "])
    def test_student_aliases_trigger_guard(self, audience):
        rows = [_enrollment("active")]
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=rows):
            _check_student_audience_population(
                tenant_id=TENANT_ID,
                target_audience=audience,
                recipients_count=1,
                message_code="M8",
            )


class TestW117OrderOfOperations:
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
                create_message(payload, TENANT_ID)
            mock_create.assert_not_called()

        assert call_order[0] == "enrollments"


class TestW117MessageMetadataInErrors:
    def test_error_contains_message_code_and_audience(self):
        with patch("app.modules.communications.service.list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_student_audience_population(
                    tenant_id=TENANT_ID,
                    target_audience="students",
                    recipients_count=1,
                    message_code="CODE-X",
                )
        msg = str(exc_info.value)
        assert "CODE-X" in msg
        assert "students" in msg


class TestW117TenantIsolation:
    def test_guard_uses_current_tenant_scope(self):
        seen_tenants: list[int] = []

        def _list(entity_name, tenant_id):
            seen_tenants.append(tenant_id)
            return [_enrollment("active")]

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list):
            _check_student_audience_population(
                tenant_id=777,
                target_audience="students",
                recipients_count=1,
                message_code="M9",
            )

        assert seen_tenants == [777]


class TestW117LargeBroadcastPathStillWorks:
    def test_large_broadcast_triggers_secondary_helpers_after_guard_pass(self):
        payload = _payload(recipients_count=600)

        created_message = {"id": 321, **payload}
        created_records: list[str] = []

        def _list(entity_name, tenant_id):
            if entity_name == "enrollments":
                return [_enrollment("active") for _ in range(700)]
            if entity_name == "communication_messages":
                return []
            if entity_name == "communication_broadcast_audits":
                return []
            if entity_name == "communication_broadcast_risk_alerts":
                return []
            return []

        def _create(entity_name, payload_obj, tenant_id):
            created_records.append(entity_name)
            if entity_name == "communication_messages":
                return created_message
            return {"id": 999, **payload_obj}

        with patch("app.modules.communications.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.communications.service.create_entity_for_tenant",
            side_effect=_create,
        ), patch("app.modules.communications.service.EventPublisher"):
            result = create_message(payload, TENANT_ID)

        assert result["id"] == 321
        assert "communication_messages" in created_records
        assert "communication_broadcast_audits" in created_records
        assert "communication_broadcast_risk_alerts" in created_records
