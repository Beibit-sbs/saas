"""W107 — Security Operations: Visitor Access Facility Incident Guard (cross-entity: security_visitors × security_incidents).

Business invariant: A visitor check-in is blocked when the facility has an active
critical/high security incident.

Bad outcomes if guard is missing:
  - Visitors gain access to facilities under lockdown/evacuation/chemical hazard
  - Physical safety liability — unauthorized access during critical incidents
  - Security KPIs corrupted (phantom visitor records during unsafe periods)
  - Incident response compromised by uncontrolled facility access

Guard location: security_operations/service.py :: create_security_visitor() → _check_facility_has_no_active_critical_incident()
                BEFORE create_entity_for_tenant("security_visitors", ...)
"""
from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
SERVICE_MODULE = "app.modules.security_operations.service"


def _svc():
    """Return freshly imported service module."""
    return importlib.import_module(SERVICE_MODULE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_incident(
    facility_code: str, status: str, severity: str, **extra
) -> dict:
    return {
        "id": 1,
        "facility_code": facility_code,
        "status": status,
        "severity": severity,
        **extra,
    }


def _visitor_payload(facility_code: str = "FAC-001") -> dict:
    return {"facility_code": facility_code, "visitor_name": "John Doe", "badge_id": "V123"}


TENANT = 42

# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestW107Constants:
    def test_blocked_incident_statuses_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_BLOCKED_INCIDENT_STATUSES")

    def test_blocked_incident_statuses_is_frozenset(self):
        svc = _svc()
        assert isinstance(svc._BLOCKED_INCIDENT_STATUSES, frozenset)

    def test_blocked_incident_statuses_contains_open(self):
        svc = _svc()
        assert "open" in svc._BLOCKED_INCIDENT_STATUSES

    def test_blocked_incident_statuses_contains_investigating(self):
        svc = _svc()
        assert "investigating" in svc._BLOCKED_INCIDENT_STATUSES

    def test_blocked_incident_severities_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_BLOCKED_INCIDENT_SEVERITIES")

    def test_blocked_incident_severities_is_frozenset(self):
        svc = _svc()
        assert isinstance(svc._BLOCKED_INCIDENT_SEVERITIES, frozenset)

    def test_blocked_incident_severities_contains_critical(self):
        svc = _svc()
        assert "critical" in svc._BLOCKED_INCIDENT_SEVERITIES

    def test_blocked_incident_severities_contains_high(self):
        svc = _svc()
        assert "high" in svc._BLOCKED_INCIDENT_SEVERITIES

    def test_blocked_incident_severities_does_not_contain_medium(self):
        svc = _svc()
        assert "medium" not in svc._BLOCKED_INCIDENT_SEVERITIES

    def test_blocked_incident_severities_does_not_contain_low(self):
        svc = _svc()
        assert "low" not in svc._BLOCKED_INCIDENT_SEVERITIES


# ---------------------------------------------------------------------------
# 2. Guard unit tests (_check_facility_has_no_active_critical_incident)
# ---------------------------------------------------------------------------

class TestCheckFacilityHasNoActiveIncident:
    def _call(self, incidents: list[dict], facility_code: str = "FAC-001"):
        from app.modules.security_operations.service import (
            _check_facility_has_no_active_critical_incident,
        )

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=incidents,
        ):
            return _check_facility_has_no_active_critical_incident(
                tenant_id=TENANT, facility_code=facility_code
            )

    def test_passes_no_incidents(self):
        """Guard passes: no incidents at all for facility."""
        self._call([])

    def test_passes_other_facility_has_critical(self):
        """Guard passes: another facility has critical incident but not our facility."""
        self._call([_make_incident("FAC-999", "open", "critical")])

    def test_passes_facility_has_low_incident(self):
        """Guard passes: facility has low-severity incident (not blocking)."""
        self._call([_make_incident("FAC-001", "open", "low")])

    def test_passes_facility_has_medium_incident(self):
        """Guard passes: facility has medium-severity incident (not blocking)."""
        self._call([_make_incident("FAC-001", "open", "medium")])

    def test_passes_facility_has_resolved_critical(self):
        """Guard passes: facility has critical incident but status is resolved/closed."""
        self._call([_make_incident("FAC-001", "resolved", "critical")])

    def test_passes_facility_has_closed_critical(self):
        """Guard passes: facility has critical incident but status is closed."""
        self._call([_make_incident("FAC-001", "closed", "critical")])

    def test_blocks_facility_has_open_critical(self):
        """Guard blocks: facility has open critical incident."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("FAC-001", "open", "critical")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )

    def test_blocks_facility_has_investigating_critical(self):
        """Guard blocks: facility has investigating critical incident."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("FAC-001", "investigating", "critical")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )

    def test_blocks_facility_has_open_high(self):
        """Guard blocks: facility has open high incident."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("FAC-001", "open", "high")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )

    def test_blocks_facility_has_investigating_high(self):
        """Guard blocks: facility has investigating high incident."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("FAC-001", "investigating", "high")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )

    def test_facility_code_match_is_case_insensitive(self):
        """Guard: facility_code matching is case-insensitive."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("fac-001", "open", "critical")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )

    def test_fail_closed_lookup_error_raises_domain_error(self):
        """FAIL-CLOSED: if list_entities_for_tenant raises, guard raises DomainValidationError."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            side_effect=RuntimeError("db timeout"),
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )

    def test_error_message_contains_facility_code(self):
        """Error message must reference the facility_code for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("FAC-XYZ", "open", "critical")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError, match="FAC-XYZ"):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-XYZ"
                )

    def test_error_message_contains_severity(self):
        """Error message must state the incident severity for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError

        with patch(
            "app.modules.security_operations.service.list_entities_for_tenant",
            return_value=[_make_incident("FAC-001", "open", "critical")],
        ):
            from app.modules.security_operations.service import (
                _check_facility_has_no_active_critical_incident,
            )

            with pytest.raises(DomainValidationError, match="critical"):
                _check_facility_has_no_active_critical_incident(
                    tenant_id=TENANT, facility_code="FAC-001"
                )


# ---------------------------------------------------------------------------
# 3. Integration: create_security_visitor wires the guard
# ---------------------------------------------------------------------------

class TestCreateSecurityVisitorGuard:
    def _run(
        self,
        incidents: list[dict],
        payload: dict | None = None,
        create_return: dict | None = None,
    ) -> tuple[object, MagicMock]:
        from app.modules.security_operations.service import create_security_visitor

        _payload = payload or _visitor_payload()
        _create_ret = create_return or {"id": 99, **_payload}

        mock_create = MagicMock(return_value=_create_ret)
        with (
            patch(
                "app.modules.security_operations.service.list_entities_for_tenant",
                return_value=incidents,
            ),
            patch(
                "app.modules.security_operations.service.create_entity_for_tenant", mock_create
            ),
        ):
            result = create_security_visitor(_payload, TENANT)
        return result, mock_create

    def test_visitor_allowed_no_incident(self):
        """create_security_visitor succeeds when no incidents for facility."""
        result, mock_create = self._run([])
        mock_create.assert_called_once()

    def test_visitor_allowed_low_incident(self):
        """create_security_visitor succeeds when facility has low incident."""
        result, mock_create = self._run([_make_incident("FAC-001", "open", "low")])
        mock_create.assert_called_once()

    def test_visitor_allowed_resolved_critical(self):
        """create_security_visitor succeeds when facility has resolved critical incident."""
        result, mock_create = self._run([_make_incident("FAC-001", "resolved", "critical")])
        mock_create.assert_called_once()

    def test_visitor_blocked_open_critical(self):
        """create_security_visitor raises for open critical incident — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.security_operations.service import create_security_visitor

        mock_create = MagicMock()
        with (
            patch(
                "app.modules.security_operations.service.list_entities_for_tenant",
                return_value=[_make_incident("FAC-001", "open", "critical")],
            ),
            patch(
                "app.modules.security_operations.service.create_entity_for_tenant", mock_create
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_security_visitor(_visitor_payload(), TENANT)

        mock_create.assert_not_called()

    def test_visitor_blocked_investigating_high(self):
        """create_security_visitor raises for investigating high incident — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.security_operations.service import create_security_visitor

        mock_create = MagicMock()
        with (
            patch(
                "app.modules.security_operations.service.list_entities_for_tenant",
                return_value=[_make_incident("FAC-001", "investigating", "high")],
            ),
            patch(
                "app.modules.security_operations.service.create_entity_for_tenant", mock_create
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_security_visitor(_visitor_payload(), TENANT)

        mock_create.assert_not_called()

    def test_guard_fires_before_persist(self):
        """Guard is invoked BEFORE create_entity_for_tenant — persist never called on block."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.security_operations.service import create_security_visitor

        call_order: list[str] = []

        def fake_list(table, tid):
            call_order.append("list")
            return [_make_incident("FAC-001", "open", "critical")]

        def fake_create(table, payload, tid):
            call_order.append("create")
            return payload

        with (
            patch(
                "app.modules.security_operations.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
            patch(
                "app.modules.security_operations.service.create_entity_for_tenant",
                side_effect=fake_create,
            ),
        ):
            with pytest.raises(DomainValidationError):
                create_security_visitor(_visitor_payload(), TENANT)

        assert "list" in call_order
        assert "create" not in call_order

    def test_no_facility_code_in_payload_skips_guard(self):
        """If facility_code is absent from payload, guard is skipped (no breakage)."""
        from app.modules.security_operations.service import create_security_visitor

        mock_create = MagicMock(return_value={"id": 1})
        with (
            patch(
                "app.modules.security_operations.service.list_entities_for_tenant",
                return_value=[],
            ),
            patch(
                "app.modules.security_operations.service.create_entity_for_tenant", mock_create
            ),
        ):
            create_security_visitor({"visitor_name": "John"}, TENANT)

        mock_create.assert_called_once()

    def test_multiple_incidents_first_blocking_one_cited(self):
        """Error message cites first blocking incident found."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.security_operations.service import create_security_visitor

        with (
            patch(
                "app.modules.security_operations.service.list_entities_for_tenant",
                return_value=[
                    _make_incident("FAC-001", "open", "high"),
                    _make_incident("FAC-001", "open", "critical"),
                ],
            ),
            patch(
                "app.modules.security_operations.service.create_entity_for_tenant",
                return_value={"id": 1},
            ),
        ):
            with pytest.raises(DomainValidationError, match="high"):
                create_security_visitor(_visitor_payload(), TENANT)
