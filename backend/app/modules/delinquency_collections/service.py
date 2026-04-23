"""Phase X-X3: Delinquency & Collections service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.delinquency_collections.schemas import (
    DelinquencyEscalationUpdateSchema,
    DelinquencyRecordCreateSchema,
    DelinquencyRecordSchema,
    DelinquencyStatus,
    DelinquencyStatusUpdateSchema,
    EscalationStage,
)
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="delinquency_collections",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_delinquency_records(
    tenant_id: int,
    status: DelinquencyStatus | None = None,
    escalation_stage: EscalationStage | None = None,
) -> list[DelinquencyRecordSchema]:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if escalation_stage is not None:
        rows = [r for r in rows if str(r.get("escalation_stage") or "") == escalation_stage]
    return [DelinquencyRecordSchema.model_validate(r) for r in rows]


def get_delinquency_record(tenant_id: int, record_id: int) -> DelinquencyRecordSchema | None:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if row is None:
        return None
    return DelinquencyRecordSchema.model_validate(row)


def create_delinquency_record(
    tenant_id: int,
    request: DelinquencyRecordCreateSchema,
    actor: str,
) -> DelinquencyRecordSchema:
    created = create_entity_for_tenant(
        "delinquency_records",
        {
            "student_id": request.student_id.strip(),
            "invoice_code": request.invoice_code.strip(),
            "amount_due": float(request.amount_due),
            "days_overdue": int(request.days_overdue),
            "escalation_stage": request.escalation_stage,
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("delinquency_collections", "record", "create"),
        path="/internal/delinquency-collections",
        metadata={"resource_id": str(created.get("id")), "student_id": request.student_id},
        tenant_id=tenant_id,
    )
    # Brain signal for high overdue
    try:
        days = int(created.get("days_overdue") or 0)
    except (TypeError, ValueError):
        days = 0

    if days >= 90:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="collections.delinquency.critical_overdue",
            aggregate_type="delinquency_records",
            aggregate_id=str(created.get("id") or "unknown"),
            payload_json={
                "student_id": request.student_id,
                "days_overdue": days,
                "amount_due": float(request.amount_due),
            },
        )
    return DelinquencyRecordSchema.model_validate(created)


def update_delinquency_status(
    tenant_id: int,
    record_id: int,
    request: DelinquencyStatusUpdateSchema,
    actor: str,
) -> DelinquencyRecordSchema | None:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        return None
    updated = update_entity_for_tenant(
        "delinquency_records", record_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("delinquency_collections", "record", "status_update"),
        path=f"/internal/delinquency-collections/{record_id}/status",
        metadata={"resource_id": str(record_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return DelinquencyRecordSchema.model_validate(updated)


def update_delinquency_escalation(
    tenant_id: int,
    record_id: int,
    request: DelinquencyEscalationUpdateSchema,
    actor: str,
) -> DelinquencyRecordSchema | None:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        return None
    updated = update_entity_for_tenant(
        "delinquency_records", record_id, {**existing, "escalation_stage": request.escalation_stage}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("delinquency_collections", "record", "escalation_update"),
        path=f"/internal/delinquency-collections/{record_id}/escalation",
        metadata={"resource_id": str(record_id), "new_stage": request.escalation_stage},
        tenant_id=tenant_id,
    )
    return DelinquencyRecordSchema.model_validate(updated)
