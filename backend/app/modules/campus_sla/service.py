"""Phase VI-VI3: Campus SLA service."""
from __future__ import annotations

from uuid import uuid4

from app.core.module_helpers.service_validation import DomainValidationError
from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)

_BREACHED_STATUS = "breached"

# Maximum target_sla_minutes allowed per priority tier.
# Requests exceeding this ceiling are rejected to prevent SLA gaming.
_SLA_MAX_TARGET_BY_PRIORITY: dict[str, int] = {
    "critical": 60,
    "high": 240,
    "medium": 1440,
    "low": 4320,
}

# W59: active record count cap per priority tier
_SLA_PRIORITY_MAX_ACTIVE: dict[str, int] = {
    "critical": 10,
    "high": 25,
    "medium": 50,
    "low": 100,
}
_ACTIVE_SLA_STATUSES: frozenset[str] = frozenset({"open", "in_progress"})
_BREACH_RISK_STATUSES: frozenset[str] = frozenset({"breached"})

# W120: maintenance request must be in one of these statuses to allow SLA record creation
_ACTIVE_MAINTENANCE_STATUSES: frozenset[str] = frozenset({"open", "pending", "in_progress"})


def _check_facility_has_active_maintenance_request(
    *,
    tenant_id: int,
    facility_code: str,
) -> None:
    """Fail-closed guard: facility_code must have an active maintenance request.

    Dangerous action: creating a campus SLA record that consumes SLA monitoring capacity
                      and feeds breach-rate compliance analytics.
    Real-world constraint: SLA records must correspond to an actual open/pending maintenance
                           issue at that facility — otherwise the compliance data is phantom.
    External entity: facilities_maintenance_requests.
    Validates BEFORE create_entity_for_tenant("campus_sla_records", ...).
    Bad outcome prevented: Ghost SLA records for non-existent facility issues inflate breach
                           counts and corrupt institutional SLA compliance reporting.
    """
    try:
        requests = list_entities_for_tenant("facilities_maintenance_requests", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot verify facility maintenance request: lookup failed ({exc})"
        ) from exc

    normalized_code = str(facility_code).strip().lower()
    active_request = next(
        (
            row for row in requests
            if str(row.get("facility_code") or "").strip().lower() == normalized_code
            and str(row.get("status") or "").strip().lower() in _ACTIVE_MAINTENANCE_STATUSES
        ),
        None,
    )
    if active_request is None:
        raise DomainValidationError(
            f"Facility '{facility_code}' has no active maintenance request in this tenant. "
            "Campus SLA records may only be created for facilities with open or pending "
            "maintenance requests."
        )


def _is_breached(row: dict[str, object]) -> bool:
    """Return True when the record is a SLA breach."""
    if str(row.get("status") or "").strip().lower() == _BREACHED_STATUS:
        return True
    actual = row.get("actual_minutes")
    target = row.get("target_sla_minutes")
    if actual is not None and target is not None:
        try:
            return int(actual) > int(target)
        except (TypeError, ValueError):
            pass
    return False


def list_sla_records(
    tenant_id: int,
    status: str | None = None,
    service_type: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("campus_sla_records", tenant_id)
    status_filter = str(status or "").strip().lower()
    service_filter = str(service_type or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        if service_filter and str(row.get("service_type") or "").strip().lower() != service_filter:
            continue
        enriched = dict(row)
        enriched["breached"] = _is_breached(row)
        result.append(enriched)
    return result


def create_sla_record(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    facility_code = str(payload.get("facility_code") or "").strip()
    if not facility_code:
        raise DomainValidationError("facility_code is required for campus SLA records")

    priority = str(payload.get("priority") or "").strip().lower()
    target_minutes = payload.get("target_sla_minutes")
    if priority and target_minutes is not None:
        max_allowed = _SLA_MAX_TARGET_BY_PRIORITY.get(priority)
        if max_allowed is not None:
            try:
                if int(target_minutes) > max_allowed:
                    raise ValueError(
                        f"priority='{priority}' exceeds maximum target_sla_minutes={max_allowed}; "
                        f"got {target_minutes}"
                    )
            except (TypeError, ValueError) as exc:
                if "exceeds maximum" in str(exc):
                    raise

    # W120: fail-closed guard — facility must have an active maintenance request BEFORE any persist
    _check_facility_has_active_maintenance_request(
        tenant_id=tenant_id, facility_code=facility_code
    )

    # W59: count-cap guard — reject when active records per priority exceed cap
    if priority:
        active_cap = _SLA_PRIORITY_MAX_ACTIVE.get(priority)
        if active_cap is not None:
            active_records = [
                r for r in list_entities_for_tenant("campus_sla_records", tenant_id)
                if str(r.get("priority") or "").strip().lower() == priority
                and str(r.get("status") or "").strip().lower() in _ACTIVE_SLA_STATUSES
            ]
            if len(active_records) >= active_cap:
                raise ValueError(
                    f"active SLA record cap reached for priority='{priority}'; "
                    f"max={active_cap}"
                )

    record = create_entity_for_tenant("campus_sla_records", payload, tenant_id)
    breached = _is_breached(record)
    enriched = dict(record)
    enriched["breached"] = breached

    if breached:
        record_id = str(record.get("id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.sla.breach_detected",
            aggregate_type="campus_sla_record",
            aggregate_id=record_id,
            payload_json={
                "service_type": record.get("service_type"),
                "facility_code": record.get("facility_code"),
                "target_sla_minutes": record.get("target_sla_minutes"),
                "actual_minutes": record.get("actual_minutes"),
                "integration_source": record.get("integration_source"),
                "source_entity_type": "campus_sla_record",
                "source_entity_id": record_id,
            },
        )
        _ensure_escalation_work_order(tenant_id, record_id, record)
        _ensure_sla_breach_risk_alert(tenant_id, record_id, record)

    return enriched


def _ensure_sla_breach_risk_alert(
    tenant_id: int,
    record_id: str,
    record_data: dict[str, object],
) -> None:
    """Idempotent: creates one breach risk alert per SLA breach record."""
    existing = list_entities_for_tenant("campus_sla_breach_risk_alerts", tenant_id)
    already_exists = any(
        str(r.get("integration_source")) == "campus_sla_breach_queue"
        and str(r.get("source_entity_id")) == record_id
        for r in existing
    )
    if already_exists:
        return
    create_entity_for_tenant(
        "campus_sla_breach_risk_alerts",
        {
            "record_id": record_id,
            "service_type": record_data.get("service_type"),
            "facility_code": record_data.get("facility_code"),
            "priority": record_data.get("priority"),
            "status": "open",
            "alert_level": "high",
            "risk_status": "breach_detected",
            "integration_source": "campus_sla_breach_queue",
            "source_entity_id": record_id,
        },
        tenant_id,
    )


def _ensure_escalation_work_order(
    tenant_id: int,
    sla_record_id: str,
    sla_record: dict[str, object],
) -> None:
    """Idempotent: creates one escalation work order per SLA breach record."""
    existing = list_entities_for_tenant("facilities_work_orders", tenant_id)
    already_exists = any(
        str(r.get("integration_source")) == "campus_sla_breach"
        and str(r.get("source_entity_id")) == sla_record_id
        for r in existing
    )
    if already_exists:
        return
    order_code = f"SLA-WO-{uuid4().hex[:8].upper()}"
    create_entity_for_tenant(
        "facilities_work_orders",
        {
            "order_code": order_code,
            "facility_code": str(sla_record.get("facility_code") or "UNKNOWN"),
            "title": f"SLA breach escalation – {sla_record.get('service_type', 'service')}",
            "work_type": "corrective",
            "priority": "high",
            "assigned_to": None,
            "status": "open",
            "integration_source": "campus_sla_breach",
            "source_entity_id": sla_record_id,
        },
        tenant_id,
    )


def get_campus_sla_brain_context(tenant_id: int) -> dict[str, object]:
    rows = list_entities_for_tenant("campus_sla_records", tenant_id)

    total = len(rows)
    open_count = 0
    resolved_count = 0
    breached_count = 0

    for row in rows:
        row_status = str(row.get("status") or "").strip().lower()
        if row_status == "open":
            open_count += 1
        elif row_status in {"resolved", "closed"}:
            resolved_count += 1
        if _is_breached(row):
            breached_count += 1

    breach_rate = round(breached_count / total, 3) if total > 0 else 0.0

    if breach_rate >= 0.3:
        compliance_level = "low"
    elif breach_rate >= 0.1:
        compliance_level = "medium"
    else:
        compliance_level = "high"

    return {
        "module": "campus_sla",
        "tenant_id": tenant_id,
        "total_records": total,
        "open_records": open_count,
        "resolved_records": resolved_count,
        "breached_records": breached_count,
        "breach_rate": breach_rate,
        "compliance_level": compliance_level,
    }
