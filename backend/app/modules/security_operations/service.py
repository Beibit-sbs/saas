"""Phase VI-VI1: Security operations service (A-018.6 readiness closure)."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.platform.event_ingestion import service as event_ingestion_service
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.modules.university_core.tenant_entity_api import update_entity_for_tenant
from app.core.module_helpers.service_validation import DomainValidationError


_HIGH_SEVERITIES = {"high", "critical"}

# ---------------------------------------------------------------------------
# A-019.3: Incident lifecycle FSM
# ---------------------------------------------------------------------------
_INCIDENT_FSM: dict[str, frozenset[str]] = {
    "open": frozenset({"acknowledged", "escalated", "resolved", "dismissed"}),
    "acknowledged": frozenset({"escalated", "resolved", "dismissed"}),
    "escalated": frozenset({"resolved", "dismissed"}),
    "resolved": frozenset(),
    "dismissed": frozenset(),
}
_TERMINAL_INCIDENT_STATES = frozenset({"resolved", "dismissed"})
_SEVERITY_MAX_ACTIVE_INCIDENTS: dict[str, int] = {
    "critical": 2,
    "high": 6,
    "medium": 20,
    "low": 50,
}
_ACTIVE_INCIDENT_STATUSES = frozenset({"open", "investigating"})

# ---------------------------------------------------------------------------
# W107: Security visitor facility incident guard
# Visitor check-in blocked when facility has active critical/high incident.
# Prevents unauthorized access to unsafe facilities during lockdown/chemical hazard.
# ---------------------------------------------------------------------------
_BLOCKED_INCIDENT_STATUSES: frozenset[str] = frozenset({"open", "investigating"})
_BLOCKED_INCIDENT_SEVERITIES: frozenset[str] = frozenset({"critical", "high"})


def _check_facility_has_no_active_critical_incident(
    *,
    tenant_id: int,
    facility_code: str,
) -> None:
    """W107: Cross-entity guard — security_visitors × security_incidents.

    A visitor check-in is blocked when there is an open critical/high incident
    for the same facility_code. Prevents unauthorized access to unsafe facilities
    during lockdown, evacuation, chemical hazard, or other critical security events.

    FAIL-CLOSED: if incident lookup fails (any exception), the visitor check-in is BLOCKED.
    """
    try:
        all_incidents = list_entities_for_tenant("security_incidents", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Visitor check-in blocked for facility_code='{facility_code}': "
            f"incident lookup failed — {exc}. Cannot verify facility safety."
        ) from exc

    blocking = [
        row for row in all_incidents
        if str(row.get("facility_code") or "").strip().lower() == str(facility_code).strip().lower()
        and str(row.get("status") or "").strip().lower() in _BLOCKED_INCIDENT_STATUSES
        and str(row.get("severity") or "").strip().lower() in _BLOCKED_INCIDENT_SEVERITIES
    ]

    if blocking:
        incident = blocking[0]
        raise DomainValidationError(
            f"Visitor check-in blocked for facility_code='{facility_code}': "
            f"active {incident.get('severity')} security incident exists for this facility. "
            "Visitor access is prohibited during active critical/high security incidents."
        )


def _ensure_incident_escalation_record(
    incident: dict[str, object],
    tenant_id: int,
    response_team: str | None = None,
) -> None:
    incident_id = str(incident.get("id") or "").strip()
    if not incident_id:
        return

    for row in list_entities_for_tenant("security_incident_escalation_records", tenant_id):
        if (
            str(row.get("integration_source") or "").strip() == "security_incident_escalation"
            and str(row.get("source_entity_id") or "").strip() == incident_id
        ):
            return

    incident_code = str(incident.get("incident_code") or "").strip() or f"INC-{incident_id}"
    create_entity_for_tenant(
        "security_incident_escalation_records",
        {
            "incident_id": incident_id,
            "incident_code": incident_code,
            "facility_code": str(incident.get("facility_code") or "").strip(),
            "category": str(incident.get("category") or "").strip(),
            "response_team": response_team or "security_command",
            "escalation_level": "critical",
            "status": "open",
            "integration_source": "security_incident_escalation",
            "source_entity_id": incident_id,
        },
        tenant_id,
    )


def list_security_incidents(
    tenant_id: int,
    severity: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("security_incidents", tenant_id)
    severity_filter = str(severity or "").strip().lower()
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        row_severity = str(row.get("severity") or "").strip().lower()
        row_status = str(row.get("status") or "").strip().lower()
        if severity_filter and row_severity != severity_filter:
            continue
        if status_filter and row_status != status_filter:
            continue
        result.append(row)
    return result


def create_security_incident(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    severity = str(payload.get("severity") or "").strip().lower()
    status = str(payload.get("status") or "").strip().lower()
    if severity:
        cap = _SEVERITY_MAX_ACTIVE_INCIDENTS.get(severity)
        if cap is not None and status in _ACTIVE_INCIDENT_STATUSES:
            active_count = sum(
                1
                for row in list_entities_for_tenant("security_incidents", tenant_id)
                if str(row.get("severity") or "").strip().lower() == severity
                and str(row.get("status") or "").strip().lower() in _ACTIVE_INCIDENT_STATUSES
            )
            if active_count >= cap:
                raise ValueError(
                    f"severity='{severity}' active incident cap exceeded; max={cap}"
                )

    record = create_entity_for_tenant("security_incidents", payload, tenant_id)
    severity = str(record.get("severity") or "").strip().lower()
    record_id = str(record.get("id") or "unknown")
    incident_status = str(record.get("status") or "").strip().lower()

    # A-018.6: Emit incident lifecycle event to event_ingestion for KPI tracking.
    try:
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type="security.incident.opened",
            payload={
                "incident_id": record_id,
                "severity": severity,
                "status": incident_status,
                "facility_code": record.get("facility_code"),
            },
        )
    except Exception:
        pass

    if severity in _HIGH_SEVERITIES:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.security_incident.detected",
            aggregate_type="security_incident",
            aggregate_id=record_id,
            payload_json={
                "incident_code": record.get("incident_code"),
                "facility_code": record.get("facility_code"),
                "issue_type": record.get("category"),
                "severity": severity,
                "visitor_id": record.get("visitor_id"),
                "access_control_event_id": record.get("access_control_event_id"),
                "integration_source": record.get("integration_source"),
                "source_entity_type": "security_incident",
                "source_entity_id": record_id,
            },
        )
    if severity == "critical":
        _ensure_incident_escalation_record(
            record,
            tenant_id,
            response_team=str(payload.get("response_team") or "").strip() or None,
        )
        # A-018.6: Emit escalation event for KPI tracking.
        try:
            event_ingestion_service.record_event(
                tenant_id=tenant_id,
                event_type="security.incident.escalated",
                payload={"incident_id": record_id, "severity": severity},
            )
        except Exception:
            pass
    return record


def list_security_visitors(
    tenant_id: int,
    status: str | None = None,
    access_status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("security_visitors", tenant_id)
    status_filter = str(status or "").strip().lower()
    access_filter = str(access_status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        row_status = str(row.get("status") or "").strip().lower()
        row_access_status = str(row.get("access_status") or "").strip().lower()
        if status_filter and row_status != status_filter:
            continue
        if access_filter and row_access_status != access_filter:
            continue
        result.append(row)
    return result


def create_security_visitor(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    # W107: Facility incident guard — no visitor check-in during active critical/high incident
    facility_code = str(payload.get("facility_code") or "").strip()
    if facility_code:
        _check_facility_has_no_active_critical_incident(
            tenant_id=tenant_id, facility_code=facility_code
        )
    return create_entity_for_tenant("security_visitors", payload, tenant_id)


def get_security_operations_brain_context(tenant_id: int) -> dict[str, object]:
    incidents = list_entities_for_tenant("security_incidents", tenant_id)
    visitors = list_entities_for_tenant("security_visitors", tenant_id)

    open_incidents = sum(
        1
        for row in incidents
        if str(row.get("status") or "").strip().lower() in {"open", "investigating"}
    )
    critical_incidents = sum(
        1 for row in incidents if str(row.get("severity") or "").strip().lower() == "critical"
    )
    active_visitors = sum(
        1 for row in visitors if str(row.get("status") or "").strip().lower() == "checked_in"
    )
    denied_access_events = sum(
        1 for row in visitors if str(row.get("access_status") or "").strip().lower() == "denied"
    )

    if critical_incidents > 0 or denied_access_events >= 2:
        risk_level = "high"
    elif open_incidents > 0 or denied_access_events > 0:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "module": "security_operations",
        "tenant_id": tenant_id,
        "total_incidents": len(incidents),
        "open_incidents": open_incidents,
        "critical_incidents": critical_incidents,
        "total_visitors": len(visitors),
        "active_visitors": active_visitors,
        "denied_access_events": denied_access_events,
        "risk_level": risk_level,
    }


# ---------------------------------------------------------------------------
# A-019.3: Incident lifecycle helper + FSM transition functions
# ---------------------------------------------------------------------------

def _get_incident_for_tenant(incident_id: str | int, tenant_id: int) -> dict[str, object]:
    """Return the incident row or raise DomainValidationError if not found."""
    target_id = str(incident_id).strip()
    rows = list_entities_for_tenant("security_incidents", tenant_id)
    for row in rows:
        if str(row.get("id") or "").strip() == target_id:
            return row
    raise DomainValidationError(f"Security incident id={incident_id!r} not found for tenant_id={tenant_id}")


def _do_incident_transition(
    incident_id: str | int,
    tenant_id: int,
    target_status: str,
    event_type: str,
    extra_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    """Validate FSM transition, update record, and emit lifecycle event."""
    incident = _get_incident_for_tenant(incident_id, tenant_id)
    current_status = str(incident.get("status") or "").strip().lower()
    allowed = _INCIDENT_FSM.get(current_status, frozenset())
    if target_status not in allowed:
        raise DomainValidationError(
            f"Invalid incident transition: {current_status!r} → {target_status!r}"
        )
    record_id = int(incident["id"])
    # tenant_entity update performs full normalization (required fields included),
    # so transition updates must preserve existing required fields.
    update_payload = dict(incident)
    update_payload["status"] = target_status
    updated = update_entity_for_tenant(
        "security_incidents", record_id, update_payload, tenant_id
    )
    try:
        payload: dict[str, object] = {
            "incident_id": str(record_id),
            "severity": str(incident.get("severity") or ""),
            "from_status": current_status,
            "to_status": target_status,
        }
        if extra_payload:
            payload.update(extra_payload)
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass
    return updated


def acknowledge_incident(incident_id: str | int, tenant_id: int) -> dict[str, object]:
    """Transition a security incident to ACKNOWLEDGED (open → acknowledged)."""
    return _do_incident_transition(
        incident_id, tenant_id, "acknowledged", "security.incident.acknowledged"
    )


def escalate_incident(
    incident_id: str | int,
    tenant_id: int,
    response_team: str | None = None,
) -> dict[str, object]:
    """Transition a security incident to ESCALATED and ensure escalation record."""
    result = _do_incident_transition(
        incident_id, tenant_id, "escalated", "security.incident.escalated",
        extra_payload={"response_team": response_team or "security_command"},
    )
    # Ensure escalation record for evidence audit trail.
    _ensure_incident_escalation_record(result, tenant_id, response_team=response_team)
    return result


def resolve_incident(incident_id: str | int, tenant_id: int) -> dict[str, object]:
    """Transition a security incident to RESOLVED."""
    return _do_incident_transition(
        incident_id, tenant_id, "resolved", "security.incident.resolved"
    )


def dismiss_incident(incident_id: str | int, tenant_id: int) -> dict[str, object]:
    """Transition a security incident to DISMISSED (human review decision)."""
    return _do_incident_transition(
        incident_id, tenant_id, "dismissed", "security.incident.dismissed"
    )
