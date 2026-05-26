"""Document / Decree / Correspondence repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.document_decree_correspondence import models


MODEL_REGISTRY = {
    "readiness": models.ReadinessProfile,
    "dashboard": models.DashboardSnapshot,
    "document_intake": models.DocumentIntakeRecord,
    "document_registration": models.DocumentRegistrationRecord,
    "document_routing": models.DocumentRoutingRecord,
    "document_workflow": models.DocumentWorkflowMetadata,
    "rector_resolutions": models.RectorResolutionRecord,
    "decrees": models.DecreeRegistryRecord,
    "decree_drafts": models.DecreeDraftMetadata,
    "incoming_correspondence": models.IncomingCorrespondenceRecord,
    "outgoing_correspondence": models.OutgoingCorrespondenceRecord,
    "templates": models.TemplateMetadata,
    "committee_decisions": models.CommitteeDecisionBridgeRecord,
    "assignments": models.AssignmentBridgeRecord,
    "execution_control": models.ExecutionControlRecord,
    "sla_deadlines": models.SlaDeadlineRecord,
    "overdue_visibility": models.OverdueVisibilityRecord,
    "attachments": models.AttachmentMetadata,
    "archive": models.ArchiveReadinessRecord,
    "retention": models.RetentionMetadata,
    "signature_readiness": models.SignatureReadinessProfile,
    "delivery_readiness": models.DeliveryReadinessProfile,
    "bridges": models.BridgeRecord,
    "limitations": models.Limitation,
}


def verify_tenant_scope(tenant_id: int) -> int:
    if isinstance(tenant_id, bool) or not isinstance(tenant_id, int) or tenant_id <= 0:
        raise DomainValidationError("tenant_id must be a positive integer")
    return tenant_id


def _now() -> datetime:
    return datetime.now(UTC)


def list_records(db: Session, model_key: str, tenant_id: int):
    tenant_id = verify_tenant_scope(tenant_id)
    model_cls = MODEL_REGISTRY[model_key]
    stmt = select(model_cls).where(model_cls.tenant_id == tenant_id).order_by(model_cls.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_record(db: Session, model_key: str, tenant_id: int, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    model_cls = MODEL_REGISTRY[model_key]
    if "created_at" not in kwargs and hasattr(model_cls, "created_at"):
        kwargs["created_at"] = _now()
    if "updated_at" not in kwargs and hasattr(model_cls, "updated_at"):
        kwargs["updated_at"] = _now()
    obj = model_cls(tenant_id=tenant_id, **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def create_audit_event(db: Session, tenant_id: int, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    obj = models.AuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_audit_events(db: Session, tenant_id: int):
    tenant_id = verify_tenant_scope(tenant_id)
    stmt = select(models.AuditEvent).where(models.AuditEvent.tenant_id == tenant_id).order_by(models.AuditEvent.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_evidence_item(db: Session, tenant_id: int, **kwargs):
    tenant_id = verify_tenant_scope(tenant_id)
    obj = models.EvidenceItem(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_evidence_items(db: Session, tenant_id: int):
    tenant_id = verify_tenant_scope(tenant_id)
    stmt = select(models.EvidenceItem).where(models.EvidenceItem.tenant_id == tenant_id).order_by(models.EvidenceItem.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_attachment_metadata(db: Session, tenant_id: int, **kwargs):
    return create_record(db, "attachments", tenant_id, **kwargs)


def get_dashboard_inputs(db: Session, tenant_id: int) -> dict[str, int]:
    tenant_id = verify_tenant_scope(tenant_id)
    return {
        "documents": len(list_records(db, "document_workflow", tenant_id)),
        "decrees": len(list_records(db, "decrees", tenant_id)),
        "correspondence": len(list_records(db, "incoming_correspondence", tenant_id)) + len(list_records(db, "outgoing_correspondence", tenant_id)),
        "assignments": len(list_records(db, "assignments", tenant_id)),
    }


def get_bridge_inputs(db: Session, tenant_id: int):
    return list_records(db, "bridges", tenant_id)
