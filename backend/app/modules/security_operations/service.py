"""Phase VI-VI1: Security operations service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


_HIGH_SEVERITIES = {"high", "critical"}


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
    record = create_entity_for_tenant("security_incidents", payload, tenant_id)
    severity = str(record.get("severity") or "").strip().lower()
    if severity in _HIGH_SEVERITIES:
        record_id = str(record.get("id") or "unknown")
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
