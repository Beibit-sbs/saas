from __future__ import annotations

import logging
from datetime import date

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.thesis.schemas import ThesisCreateSchema, ThesisRecordSchema, ThesisStatus, ThesisStatusUpdateSchema
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)

logger = logging.getLogger("app.modules.thesis")


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted"},
    "submitted": {"under_review", "rejected"},
    "under_review": {"approved", "rejected"},
    "approved": {"defended"},
    "rejected": {"submitted"},
    "defended": set(),
}


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="thesis_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _emit_domain_event(
    *,
    tenant_id: int,
    thesis_id: int,
    student_id: int,
    advisor_faculty_id: str,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget: publish thesis.status_changed to the outbox for B-domain consumers."""
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="thesis.status_changed",
            aggregate_type="thesis_record",
            aggregate_id=thesis_id,
            payload_json={
                "thesis_id": thesis_id,
                "student_id": student_id,
                "advisor_faculty_id": advisor_faculty_id,
                "from_status": from_status,
                "to_status": to_status,
                "source_module": "thesis",
            },
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "thesis.status_changed event failed silently for tenant_id=%s thesis_id=%s",
            tenant_id,
            thesis_id,
        )


def list_thesis_records(tenant_id: int, status: ThesisStatus | None = None) -> list[ThesisRecordSchema]:
    rows = list_entities_for_tenant("thesis_records", tenant_id)
    if status is not None:
        rows = [row for row in rows if str(row.get("status") or "") == status]
    return [ThesisRecordSchema.model_validate(row) for row in rows]


def create_thesis_record(
    tenant_id: int,
    request: ThesisCreateSchema,
    actor: str,
) -> ThesisRecordSchema:
    existing = list_entities_for_tenant("thesis_records", tenant_id)
    thesis_code = request.thesis_code.strip()
    if any(str(row.get("thesis_code") or "").strip().lower() == thesis_code.lower() for row in existing):
        raise ValueError("thesis_code already exists")

    created = create_entity_for_tenant(
        "thesis_records",
        {
            "thesis_code": thesis_code,
            "student_id": int(request.student_id),
            "title": request.title.strip(),
            "advisor_faculty_id": _normalize_optional(request.advisor_faculty_id),
            "status": "draft",
            "defense_date": None,
            "repository_url": _normalize_optional(request.repository_url),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("thesis", "record", "create"),
        path="/internal/thesis/records",
        metadata={"resource_id": str(created.get("id")), "thesis_code": thesis_code},
        tenant_id=tenant_id,
    )

    return ThesisRecordSchema.model_validate(created)


def update_thesis_status(
    tenant_id: int,
    thesis_id: int,
    request: ThesisStatusUpdateSchema,
    actor: str,
) -> ThesisRecordSchema:
    all_rows = list_entities_for_tenant("thesis_records", tenant_id)
    current = next((row for row in all_rows if int(row.get("id") or 0) == thesis_id), None)
    if current is None:
        raise ValueError("thesis record not found")

    current_status = str(current.get("status") or "draft")
    next_status = request.status
    if next_status != current_status and next_status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"invalid status transition: {current_status} -> {next_status}")

    defense_date_value: date | None = request.defense_date
    if next_status == "defended" and defense_date_value is None:
        raise ValueError("defense_date is required when status is defended")

    updated = update_entity_for_tenant(
        "thesis_records",
        thesis_id,
        {
            "status": next_status,
            "defense_date": defense_date_value.isoformat() if defense_date_value else None,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("thesis", "record", "status_update"),
        path=f"/internal/thesis/records/{thesis_id}/status",
        metadata={"resource_id": str(thesis_id), "from": current_status, "to": next_status},
        tenant_id=tenant_id,
    )

    # Cross-domain event: notify B (Student Success) on risk statuses
    _emit_domain_event(
        tenant_id=tenant_id,
        thesis_id=thesis_id,
        student_id=int(current.get("student_id") or 0),
        advisor_faculty_id=str(current.get("advisor_faculty_id") or ""),
        from_status=current_status,
        to_status=next_status,
    )

    return ThesisRecordSchema.model_validate(updated)
