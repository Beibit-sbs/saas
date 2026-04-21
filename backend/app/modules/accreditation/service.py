from __future__ import annotations

import logging

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.accreditation.schemas import (
    AccreditationCreateSchema,
    AccreditationRecordSchema,
    AccreditationStandardType,
    AccreditationStatus,
    AccreditationStatusUpdateSchema,
)
from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"evidence_requested", "under_review"},
    "evidence_requested": {"evidence_collected", "remediation_required"},
    "evidence_collected": {"under_review", "remediation_required"},
    "under_review": {"compliant", "remediation_required", "evidence_requested"},
    "remediation_required": {"evidence_collected", "under_review"},
    "compliant": set(),
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
        entity="accreditation_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


_logger = logging.getLogger("app.modules.accreditation")


def _emit_domain_event(
    *,
    tenant_id: int,
    record_id: int,
    standard_code: str,
    owner_department: str,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget: publish accreditation.status_changed to the outbox for B/C-domain consumers."""
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="accreditation.status_changed",
            aggregate_type="accreditation_record",
            aggregate_id=record_id,
            payload_json={
                "accreditation_id": record_id,
                "standard_code": standard_code,
                "owner_department": owner_department,
                "from_status": from_status,
                "to_status": to_status,
                "source_module": "accreditation",
            },
        )
    except Exception:  # noqa: BLE001
        _logger.exception(
            "accreditation.status_changed event failed silently for tenant_id=%s record_id=%s",
            tenant_id,
            record_id,
        )


def list_accreditation_records(
    tenant_id: int,
    status: AccreditationStatus | None = None,
    standard_type: AccreditationStandardType | None = None,
) -> list[AccreditationRecordSchema]:
    rows = list_entities_for_tenant("accreditation_records", tenant_id)
    if status is not None:
        rows = [row for row in rows if str(row.get("status") or "") == status]
    if standard_type is not None:
        rows = [row for row in rows if str(row.get("standard_type") or "") == standard_type]
    return [AccreditationRecordSchema.model_validate(row) for row in rows]


def get_accreditation_record(tenant_id: int, record_id: int) -> AccreditationRecordSchema:
    rows = list_entities_for_tenant("accreditation_records", tenant_id)
    current = next((row for row in rows if int(row.get("id") or 0) == record_id), None)
    if current is None:
        raise ValueError("accreditation record not found")
    return AccreditationRecordSchema.model_validate(current)


def create_accreditation_record(
    tenant_id: int,
    request: AccreditationCreateSchema,
    actor: str,
) -> AccreditationRecordSchema:
    existing = list_entities_for_tenant("accreditation_records", tenant_id)
    standard_code = request.standard_code.strip()
    if any(
        str(row.get("standard_code") or "").strip().lower() == standard_code.lower()
        and int(row.get("review_cycle_year") or 0) == int(request.review_cycle_year)
        for row in existing
    ):
        raise ValueError("standard_code already exists for review cycle")

    created = create_entity_for_tenant(
        "accreditation_records",
        {
            "standard_code": standard_code,
            "standard_type": request.standard_type,
            "title": request.title.strip(),
            "owner_department": request.owner_department.strip(),
            "review_cycle_year": int(request.review_cycle_year),
            "due_date": request.due_date.isoformat() if request.due_date else None,
            "evidence_summary": _normalize_optional(request.evidence_summary),
            "risk_level": request.risk_level,
            "status": "draft",
            "reviewer_notes": None,
            "remediation_plan": None,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("accreditation", "record", "create"),
        path="/internal/accreditation/records",
        metadata={
            "resource_id": str(created.get("id")),
            "standard_code": standard_code,
            "review_cycle_year": request.review_cycle_year,
        },
        tenant_id=tenant_id,
    )

    return AccreditationRecordSchema.model_validate(created)


def update_accreditation_status(
    tenant_id: int,
    record_id: int,
    request: AccreditationStatusUpdateSchema,
    actor: str,
) -> AccreditationRecordSchema:
    rows = list_entities_for_tenant("accreditation_records", tenant_id)
    current = next((row for row in rows if int(row.get("id") or 0) == record_id), None)
    if current is None:
        raise ValueError("accreditation record not found")

    current_status = str(current.get("status") or "draft")
    next_status = request.status
    if next_status != current_status and next_status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"invalid status transition: {current_status} -> {next_status}")

    if next_status == "remediation_required" and not _normalize_optional(request.remediation_plan):
        raise ValueError("remediation_plan is required when status is remediation_required")

    updated = update_entity_for_tenant(
        "accreditation_records",
        record_id,
        {
            "status": next_status,
            "reviewer_notes": _normalize_optional(request.reviewer_notes),
            "remediation_plan": _normalize_optional(request.remediation_plan),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("accreditation", "record", "status_update"),
        path=f"/internal/accreditation/records/{record_id}/status",
        metadata={"resource_id": str(record_id), "from": current_status, "to": next_status},
        tenant_id=tenant_id,
    )

    # Cross-domain event: notify B (Student Success) + C (Faculty) on remediation_required
    _emit_domain_event(
        tenant_id=tenant_id,
        record_id=record_id,
        standard_code=str(current.get("standard_code") or ""),
        owner_department=str(current.get("owner_department") or ""),
        from_status=current_status,
        to_status=next_status,
    )

    return AccreditationRecordSchema.model_validate(updated)
