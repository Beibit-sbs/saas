from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.alumni.schemas import (
    AlumniRecordCreateSchema,
    AlumniRecordSchema,
    AlumniStatus,
    AlumniRecordStatusUpdateSchema,
)
from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "active": {"engaged", "donor", "inactive"},
    "engaged": {"donor", "inactive"},
    "donor": {"engaged", "inactive"},
    "inactive": {"active"},
}


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="alumni_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_alumni_records(
    tenant_id: int,
    status: AlumniStatus | None = None,
    student_id: int | None = None,
) -> list[AlumniRecordSchema]:
    rows = list_entities_for_tenant("alumni_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [AlumniRecordSchema.model_validate(r) for r in rows]


def create_alumni_record(
    tenant_id: int,
    request: AlumniRecordCreateSchema,
    actor: str,
) -> AlumniRecordSchema:
    created = create_entity_for_tenant(
        "alumni_records",
        {
            "student_id": int(request.student_id),
            "graduation_year": int(request.graduation_year),
            "status": "active",
            "engagement_type": request.engagement_type,
            "employer": (request.employer or "unknown").strip() or "unknown",
            "contact_email": (request.contact_email or "unknown@example.com").strip()
            or "unknown@example.com",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("alumni", "record", "create"),
        path="/internal/alumni/records",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "graduation_year": str(request.graduation_year),
        },
        tenant_id=tenant_id,
    )
    return AlumniRecordSchema.model_validate(created)


def update_alumni_status(
    tenant_id: int,
    record_id: int,
    request: AlumniRecordStatusUpdateSchema,
    actor: str,
) -> AlumniRecordSchema:
    rows = list_entities_for_tenant("alumni_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        raise ValueError(f"record {record_id} not found")

    current_status = str(existing.get("status") or "active")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    updated = update_entity_for_tenant(
        "alumni_records",
        record_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "graduation_year": int(existing.get("graduation_year") or 2000),
            "status": request.status,
            "engagement_type": str(existing.get("engagement_type") or "event"),
            "employer": str(existing.get("employer") or "unknown"),
            "contact_email": str(existing.get("contact_email") or "unknown@example.com"),
            "notes": (request.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("alumni", "record", "status_update"),
        path=f"/internal/alumni/records/{record_id}/status",
        metadata={
            "resource_id": str(record_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    if request.status in _DISENGAGEMENT_TRIGGER_STATUSES:
        try:
            _emit_alumni_engagement_risk_signal(
                tenant_id=tenant_id,
                record_id=record_id,
                student_id=int(existing.get("student_id") or 0),
                from_status=current_status,
                to_status=request.status,
            )
        except Exception:  # noqa: BLE001
            pass

    return AlumniRecordSchema.model_validate(updated)


# ---------------------------------------------------------------------------
# Brain-readiness: signal emitter + context snapshot
# ---------------------------------------------------------------------------

_DISENGAGEMENT_TRIGGER_STATUSES: frozenset[str] = frozenset({"inactive"})


def _emit_alumni_engagement_risk_signal(
    *,
    tenant_id: int,
    record_id: int,
    student_id: int,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for alumni engagement risk."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="alumni.engagement.risk_detected",
        aggregate_type="alumni_record",
        aggregate_id=record_id,
        payload_json={
            "record_id": record_id,
            "student_id": student_id,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "alumni",
            "source_entity_type": "alumni_record",
            "source_entity_id": str(record_id),
        },
    )


def get_alumni_brain_context(tenant_id: int) -> dict:
    """Return aggregated alumni context snapshot for Brain Core."""
    rows = list_entities_for_tenant("alumni_records", tenant_id)
    total = len(rows)
    by_status: dict[str, int] = {}
    by_engagement: dict[str, int] = {}
    for r in rows:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        et = str(r.get("engagement_type") or "unknown")
        by_engagement[et] = by_engagement.get(et, 0) + 1

    inactive = by_status.get("inactive", 0)
    risk_level = "high" if (total > 0 and inactive / total > 0.4) else ("medium" if inactive > 0 else "low")

    return {
        "module": "alumni",
        "tenant_id": tenant_id,
        "total_records": total,
        "by_status": by_status,
        "by_engagement_type": by_engagement,
        "inactive_count": inactive,
        "risk_level": risk_level,
    }
