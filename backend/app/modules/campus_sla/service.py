"""Phase VI-VI3: Campus SLA service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)

_BREACHED_STATUS = "breached"


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

    return enriched


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
