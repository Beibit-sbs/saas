from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.financial_aid.schemas import (
    AidStatus,
    FinancialAidRecordCreateSchema,
    FinancialAidRecordSchema,
    FinancialAidRecordStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected"},
    "approved": {"disbursed", "rejected"},
    "disbursed": set(),
    "rejected": set(),
}


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="financial_aid_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _emit_financial_aid_warning_signal(
    *,
    tenant_id: int,
    record_id: int,
    student_id: int,
    aid_type: str,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget bridge signal for student-success/financial risk scenarios."""
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="financial_aid.warning.detected",
        aggregate_type="financial_aid_record",
        aggregate_id=record_id,
        payload_json={
            "record_id": record_id,
            "student_id": student_id,
            "aid_type": aid_type,
            "from_status": from_status,
            "to_status": to_status,
            "source_module": "financial_aid",
            "source_entity_type": "financial_aid_record",
            "source_entity_id": str(record_id),
        },
    )


def list_financial_aid_records(
    tenant_id: int,
    status: AidStatus | None = None,
    student_id: int | None = None,
) -> list[FinancialAidRecordSchema]:
    rows = list_entities_for_tenant("financial_aid_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [FinancialAidRecordSchema.model_validate(r) for r in rows]


def create_financial_aid_record(
    tenant_id: int,
    request: FinancialAidRecordCreateSchema,
    actor: str,
) -> FinancialAidRecordSchema:
    created = create_entity_for_tenant(
        "financial_aid_records",
        {
            "student_id": int(request.student_id),
            "aid_type": request.aid_type,
            "amount": float(request.amount),
            "currency": request.currency.upper(),
            "status": "pending",
            "term": request.term.strip(),
            "reviewer_id": (request.reviewer_id or "aid-office").strip() or "aid-office",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("financial_aid", "record", "create"),
        path="/internal/financial-aid/records",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "aid_type": request.aid_type,
        },
        tenant_id=tenant_id,
    )
    return FinancialAidRecordSchema.model_validate(created)


def update_financial_aid_status(
    tenant_id: int,
    record_id: int,
    request: FinancialAidRecordStatusUpdateSchema,
    actor: str,
) -> FinancialAidRecordSchema:
    rows = list_entities_for_tenant("financial_aid_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        raise ValueError(f"record {record_id} not found")

    current_status = str(existing.get("status") or "pending")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    updated = update_entity_for_tenant(
        "financial_aid_records",
        record_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "aid_type": str(existing.get("aid_type") or "scholarship"),
            "amount": float(existing.get("amount") or 0),
            "currency": str(existing.get("currency") or "USD"),
            "status": request.status,
            "term": str(existing.get("term") or "unknown"),
            "reviewer_id": str(existing.get("reviewer_id") or "aid-office"),
            "notes": (request.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("financial_aid", "record", "status_update"),
        path=f"/internal/financial-aid/records/{record_id}/status",
        metadata={
            "resource_id": str(record_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    if request.status == "rejected":
        _emit_financial_aid_warning_signal(
            tenant_id=tenant_id,
            record_id=record_id,
            student_id=int(updated.get("student_id") or 0),
            aid_type=str(updated.get("aid_type") or "unknown"),
            from_status=current_status,
            to_status=request.status,
        )

    return FinancialAidRecordSchema.model_validate(updated)
