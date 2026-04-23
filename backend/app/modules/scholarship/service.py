"""Phase VIII-1: Scholarship service."""
from __future__ import annotations

from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


def list_scholarship_applications(
    tenant_id: int,
    status: str | None = None,
    scholarship_type: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("scholarship_applications", tenant_id)
    status_filter = str(status or "").strip().lower()
    type_filter = str(scholarship_type or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        if type_filter and str(row.get("scholarship_type") or "").strip().lower() != type_filter:
            continue
        result.append(row)
    return result


def create_scholarship_application(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("scholarship_applications", payload, tenant_id)


def list_scholarship_awards(
    tenant_id: int,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("scholarship_awards", tenant_id)
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        at_risk = _is_award_at_risk(row)
        result.append({**row, "at_risk": at_risk})
    return result


def _is_award_at_risk(row: dict[str, object]) -> bool:
    try:
        current_gpa = float(row.get("current_gpa") or 0)
        gpa_threshold = float(row.get("gpa_threshold") or 2.5)
    except (TypeError, ValueError):
        return False
    if current_gpa < gpa_threshold:
        return True
    if str(row.get("status") or "").strip().lower() == "at_risk":
        return True
    return False


def create_scholarship_award(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    """Create award and emit signal if award is at risk."""
    record = create_entity_for_tenant("scholarship_awards", payload, tenant_id)
    at_risk = _is_award_at_risk(payload)
    enriched = {**record, "at_risk": at_risk}

    if at_risk:
        record_id = str(record.get("id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="scholarship.award.at_risk_detected",
            aggregate_type="scholarship_award",
            aggregate_id=record_id,
            payload_json={
                "award_code": record.get("award_code"),
                "student_id": record.get("student_id"),
                "current_gpa": record.get("current_gpa"),
                "gpa_threshold": record.get("gpa_threshold"),
                "status": record.get("status"),
                "source_entity_type": "scholarship_award",
                "source_entity_id": record_id,
            },
        )

    return enriched


def get_scholarship_brain_context(tenant_id: int) -> dict[str, object]:
    applications = list_entities_for_tenant("scholarship_applications", tenant_id)
    awards = list_entities_for_tenant("scholarship_awards", tenant_id)

    total_applications = len(applications)
    pending_applications = sum(
        1 for r in applications if str(r.get("status") or "").strip().lower() == "pending"
    )
    total_awards = len(awards)
    at_risk_awards = sum(1 for r in awards if _is_award_at_risk(r))

    at_risk_rate = round(at_risk_awards / total_awards, 4) if total_awards > 0 else 0.0

    if at_risk_rate >= 0.25:
        retention_health = "critical"
    elif at_risk_rate >= 0.10:
        retention_health = "at_risk"
    else:
        retention_health = "healthy"

    return {
        "module": "scholarship",
        "tenant_id": tenant_id,
        "total_applications": total_applications,
        "pending_applications": pending_applications,
        "total_awards": total_awards,
        "at_risk_awards": at_risk_awards,
        "at_risk_rate": at_risk_rate,
        "retention_health": retention_health,
    }
