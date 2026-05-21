"""Document Workflow OS — Service layer.

Business logic, status transitions, audit event writes, status history writes.
No hard delete. No fake dashboard. No external notification dispatch.
No AI/autonomous status changes. No provider calls.
Tenant fail-closed: tenant_id required on every operation.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.document_workflow_os.models import (
    AuditEventType,
    CorrespondenceDirection,
    DecreeStatus,
    DocumentStatus,
    DocumentType,
    IncomingCorrespondenceStatus,
    OutgoingCorrespondenceStatus,
    ReviewDecision,
)
from app.modules.document_workflow_os.repository import (
    repo_add_audit_event,
    repo_archive_correspondence,
    repo_archive_decree,
    repo_archive_document,
    repo_compute_dashboard_summary,
    repo_create_correspondence,
    repo_create_decree,
    repo_create_document,
    repo_create_document_review,
    repo_create_document_version,
    repo_create_resolution,
    repo_get_correspondence,
    repo_get_decree,
    repo_get_document,
    repo_link_document_to_assignment,
    repo_link_resolution_to_assignment,
    repo_list_assignment_links,
    repo_list_correspondence,
    repo_list_correspondence_routes,
    repo_list_decrees,
    repo_list_document_audit,
    repo_list_document_history,
    repo_list_document_reviews,
    repo_list_document_versions,
    repo_list_documents,
    repo_register_correspondence,
    repo_register_decree,
    repo_require_correspondence,
    repo_require_decree,
    repo_require_document,
    repo_require_resolution,
    repo_route_correspondence,
    repo_set_correspondence_status,
    repo_set_decree_status,
    repo_set_document_status,
    repo_update_decree,
    repo_update_document,
)
from app.modules.document_workflow_os.schemas import DashboardSummaryResponse


ALLOWED_DOCUMENT_TRANSITIONS = DocumentStatus.ALLOWED_TRANSITIONS
ALLOWED_DECREE_TRANSITIONS = DecreeStatus.ALLOWED_TRANSITIONS
ALLOWED_INCOMING_CORRESPONDENCE_TRANSITIONS = IncomingCorrespondenceStatus.ALLOWED_TRANSITIONS
ALLOWED_OUTGOING_CORRESPONDENCE_TRANSITIONS = OutgoingCorrespondenceStatus.ALLOWED_TRANSITIONS
_MODULE = "document_workflow_os"


def _validate_transition(current_status: str, new_status: str, allowed_map: dict[str, frozenset[str]]) -> None:
    allowed = allowed_map.get(current_status, frozenset())
    if new_status not in allowed:
        raise DomainValidationError(f"invalid_status_transition: {current_status} -> {new_status}")


def _audit(
    db: Session,
    tenant_id: int,
    entity_type: str,
    entity_id: int,
    event_type: str,
    actor_user_id: int,
    action: str,
    payload: dict | None = None,
    actor_role: str | None = None,
) -> None:
    repo_add_audit_event(
        db,
        tenant_id,
        entity_type,
        entity_id,
        event_type,
        actor_user_id,
        action,
        payload=payload,
        actor_role=actor_role,
    )
    try:
        log_admin_action(
            actor=str(actor_user_id),
            action=action,
            path=f"/api/admin/documents/{entity_type}/{entity_id}",
            client_ip="service",
            entity=entity_type,
            metadata=payload or {},
            tenant_id=tenant_id,
        )
    except Exception:
        pass


def _finalize(db: Session, entity):
    db.commit()
    db.refresh(entity)
    return entity


# ===========================================================================
# Documents
# ===========================================================================

def create_document(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    title: str,
    document_type: str,
    source_department_id: int | None = None,
    owner_user_id: int | None = None,
    linked_assignment_id: int | None = None,
):
    validate_tenant_id_provided(tenant_id)
    if document_type not in DocumentType.ALL:
        raise DomainValidationError(f"invalid_document_type: {document_type}")
    obj = repo_create_document(
        db,
        tenant_id,
        title=title,
        document_type=document_type,
        source_department_id=source_department_id,
        owner_user_id=owner_user_id,
        linked_assignment_id=linked_assignment_id,
        created_by_user_id=actor_user_id,
    )
    repo_create_document_version(
        db,
        tenant_id,
        obj.id,
        version_number=1,
        title=title,
        body_text=None,
        metadata_json={},
        created_by_user_id=actor_user_id,
    )
    _audit(
        db,
        tenant_id,
        "document",
        obj.id,
        AuditEventType.DOCUMENT_CREATED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "create"),
        payload={"status": obj.status, "document_type": document_type},
    )
    return _finalize(db, obj)


def update_document(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    version: int,
    **kwargs,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    if obj.status not in {DocumentStatus.DRAFT, DocumentStatus.RETURNED_FOR_REVISION}:
        raise DomainValidationError("document can only be updated in DRAFT or RETURNED_FOR_REVISION")
    if "registry_number" in kwargs:
        raise DomainValidationError("registry_number is immutable via update")
    updated = repo_update_document(db, tenant_id, document_id, version, **kwargs)
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_UPDATED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "update"),
        payload={"fields": sorted(kwargs.keys())},
    )
    return _finalize(db, updated)


def register_document(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    registry_number: str,
    version: int,
    registry_date: datetime | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DocumentStatus.REGISTERED, ALLOWED_DOCUMENT_TRANSITIONS)
    if obj.registry_number:
        raise DomainValidationError("registry_number already assigned")
    updated = repo_update_document(
        db,
        tenant_id,
        document_id,
        version,
        registry_number=registry_number,
        registry_date=registry_date or datetime.now(UTC),
    )
    updated = repo_set_document_status(
        db,
        tenant_id,
        document_id,
        DocumentStatus.REGISTERED,
        actor_user_id,
        reason="registered",
    )
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_REGISTERED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "register"),
        payload={"registry_number": registry_number},
    )
    return _finalize(db, updated)


def submit_document_for_review(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    version: int,
    reviewer_user_id: int | None = None,
    note: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DocumentStatus.UNDER_REVIEW, ALLOWED_DOCUMENT_TRANSITIONS)
    updated = repo_set_document_status(
        db,
        tenant_id,
        document_id,
        DocumentStatus.UNDER_REVIEW,
        actor_user_id,
        reason=note,
    )
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_SUBMITTED_FOR_REVIEW,
        actor_user_id,
        build_audit_action(_MODULE, "document", "submit_review"),
        payload={"reviewer_user_id": reviewer_user_id, "note": note},
    )
    return _finalize(db, updated)


def return_document_for_revision(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    version: int,
    reason: str,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DocumentStatus.RETURNED_FOR_REVISION, ALLOWED_DOCUMENT_TRANSITIONS)
    repo_create_document_review(
        db,
        tenant_id,
        document_id,
        actor_user_id,
        ReviewDecision.RETURNED_FOR_REVISION,
        comment=reason,
    )
    updated = repo_set_document_status(
        db,
        tenant_id,
        document_id,
        DocumentStatus.RETURNED_FOR_REVISION,
        actor_user_id,
        reason=reason,
    )
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_RETURNED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "return"),
        payload={"reason": reason},
    )
    return _finalize(db, updated)


def approve_document(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    version: int,
    comment: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DocumentStatus.APPROVED, ALLOWED_DOCUMENT_TRANSITIONS)
    repo_create_document_review(
        db,
        tenant_id,
        document_id,
        actor_user_id,
        ReviewDecision.APPROVED,
        comment=comment,
    )
    updated = repo_set_document_status(
        db,
        tenant_id,
        document_id,
        DocumentStatus.APPROVED,
        actor_user_id,
        reason=comment,
    )
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_APPROVED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "approve"),
        payload={"comment": comment},
    )
    return _finalize(db, updated)


def record_signed_metadata(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    signed_by_user_id: int,
    version: int,
    signed_at: datetime | None = None,
    note: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    if not signed_by_user_id:
        raise DomainValidationError("signed_by_user_id is required")
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DocumentStatus.SIGNED, ALLOWED_DOCUMENT_TRANSITIONS)
    updated = repo_set_document_status(
        db,
        tenant_id,
        document_id,
        DocumentStatus.SIGNED,
        actor_user_id,
        reason=note,
    )
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_SIGNED_METADATA_RECORDED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "signed_metadata"),
        payload={"signed_by_user_id": signed_by_user_id, "signed_at": (signed_at or datetime.now(UTC)).isoformat()},
    )
    return _finalize(db, updated)


def issue_document(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    version: int,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DocumentStatus.ISSUED, ALLOWED_DOCUMENT_TRANSITIONS)
    updated = repo_set_document_status(
        db,
        tenant_id,
        document_id,
        DocumentStatus.ISSUED,
        actor_user_id,
        reason="issued",
    )
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_ISSUED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "issue"),
    )
    return _finalize(db, updated)


def archive_document(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    reason: str | None,
    version: int,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_document(db, tenant_id, document_id)
    validate_version_match(version, obj.version)
    if obj.status not in {DocumentStatus.ISSUED, DocumentStatus.EXECUTION_REPORTED, DocumentStatus.CANCELLED}:
        raise DomainValidationError("document cannot be archived from current status")
    updated = repo_archive_document(db, tenant_id, document_id, reason, actor_user_id)
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.DOCUMENT_ARCHIVED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "archive"),
        payload={"reason": reason},
    )
    return updated


# ===========================================================================
# Decrees
# ===========================================================================

def create_order_decree(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    title: str,
    decree_type: str,
    effective_date=None,
    linked_document_id: int | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_create_decree(
        db,
        tenant_id,
        title=title,
        decree_type=decree_type,
        effective_date=effective_date,
        linked_document_id=linked_document_id,
        created_by_user_id=actor_user_id,
    )
    _audit(
        db,
        tenant_id,
        "decree",
        obj.id,
        AuditEventType.DECREE_CREATED,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "create"),
        payload={"decree_type": decree_type},
    )
    return _finalize(db, obj)


def update_order_decree(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    decree_id: int,
    version: int,
    **kwargs,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_decree(db, tenant_id, decree_id)
    validate_version_match(obj.version, version)
    updated = repo_update_decree(db, tenant_id, decree_id, version, **kwargs)
    _audit(
        db,
        tenant_id,
        "decree",
        decree_id,
        AuditEventType.DECREE_UPDATED,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "update"),
        payload={"fields": sorted(kwargs.keys())},
    )
    return _finalize(db, updated)


def submit_decree_for_legal_review(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    decree_id: int,
    version: int,
    note: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_decree(db, tenant_id, decree_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DecreeStatus.LEGAL_REVIEW, ALLOWED_DECREE_TRANSITIONS)
    updated = repo_set_decree_status(db, tenant_id, decree_id, DecreeStatus.LEGAL_REVIEW, actor_user_id, note)
    _audit(
        db,
        tenant_id,
        "decree",
        decree_id,
        AuditEventType.DECREE_LEGAL_REVIEW_STARTED,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "legal_review"),
        payload={"note": note},
    )
    return _finalize(db, updated)


def approve_decree_for_signing(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    decree_id: int,
    version: int,
    comment: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_decree(db, tenant_id, decree_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DecreeStatus.APPROVED_FOR_SIGNING, ALLOWED_DECREE_TRANSITIONS)
    updated = repo_set_decree_status(db, tenant_id, decree_id, DecreeStatus.APPROVED_FOR_SIGNING, actor_user_id, comment)
    _audit(
        db,
        tenant_id,
        "decree",
        decree_id,
        AuditEventType.DECREE_APPROVED_FOR_SIGNING,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "approve_signing"),
        payload={"comment": comment},
    )
    return _finalize(db, updated)


def record_decree_signed_metadata(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    decree_id: int,
    signed_by_user_id: int,
    version: int,
    signed_at: datetime | None = None,
):
    validate_tenant_id_provided(tenant_id)
    if not signed_by_user_id:
        raise DomainValidationError("signed_by_user_id is required")
    obj = repo_require_decree(db, tenant_id, decree_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DecreeStatus.SIGNED, ALLOWED_DECREE_TRANSITIONS)
    updated = repo_update_decree(
        db,
        tenant_id,
        decree_id,
        version,
        signed_by_user_id=signed_by_user_id,
        signed_at=signed_at or datetime.now(UTC),
    )
    updated = repo_set_decree_status(db, tenant_id, decree_id, DecreeStatus.SIGNED, actor_user_id)
    _audit(
        db,
        tenant_id,
        "decree",
        decree_id,
        AuditEventType.DECREE_SIGNED_METADATA_RECORDED,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "signed_metadata"),
        payload={"signed_by_user_id": signed_by_user_id},
    )
    return _finalize(db, updated)


def register_decree(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    decree_id: int,
    registry_number: str,
    version: int,
    registry_date: datetime | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_decree(db, tenant_id, decree_id)
    validate_version_match(obj.version, version)
    _validate_transition(obj.status, DecreeStatus.REGISTERED, ALLOWED_DECREE_TRANSITIONS)
    registry_dt = registry_date or datetime.now(UTC)
    repo_register_decree(db, tenant_id, decree_id, registry_number, registry_dt, actor_user_id)
    updated = repo_update_decree(
        db,
        tenant_id,
        decree_id,
        version,
        registry_number=registry_number,
        registry_date=registry_dt,
    )
    updated = repo_set_decree_status(db, tenant_id, decree_id, DecreeStatus.REGISTERED, actor_user_id)
    _audit(
        db,
        tenant_id,
        "decree",
        decree_id,
        AuditEventType.DECREE_REGISTERED,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "register"),
        payload={"registry_number": registry_number},
    )
    return _finalize(db, updated)


def archive_decree(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    decree_id: int,
    reason: str | None,
    version: int,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_decree(db, tenant_id, decree_id)
    validate_version_match(obj.version, version)
    if obj.status not in {DecreeStatus.COMPLETED, DecreeStatus.CANCELLED, DecreeStatus.PUBLISHED_INTERNAL}:
        raise DomainValidationError("decree cannot be archived from current status")
    updated = repo_archive_decree(db, tenant_id, decree_id, reason, actor_user_id)
    _audit(
        db,
        tenant_id,
        "decree",
        decree_id,
        AuditEventType.DECREE_ARCHIVED,
        actor_user_id,
        build_audit_action(_MODULE, "decree", "archive"),
        payload={"reason": reason},
    )
    return _finalize(db, updated)


# ===========================================================================
# Correspondence
# ===========================================================================

def create_incoming_correspondence(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    subject: str,
    correspondence_type: str,
    sender_name: str | None = None,
    sender_organization: str | None = None,
    received_at: datetime | None = None,
    linked_document_id: int | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_create_correspondence(
        db,
        tenant_id,
        CorrespondenceDirection.INCOMING,
        subject=subject,
        correspondence_type=correspondence_type,
        sender_name=sender_name,
        sender_organization=sender_organization,
        received_at=received_at,
        linked_document_id=linked_document_id,
        created_by_user_id=actor_user_id,
        status=IncomingCorrespondenceStatus.RECEIVED,
    )
    return _finalize(db, obj)


def create_outgoing_correspondence(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    subject: str,
    correspondence_type: str,
    recipient_name: str | None = None,
    recipient_organization: str | None = None,
    linked_document_id: int | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_create_correspondence(
        db,
        tenant_id,
        CorrespondenceDirection.OUTGOING,
        subject=subject,
        correspondence_type=correspondence_type,
        recipient_name=recipient_name,
        recipient_organization=recipient_organization,
        linked_document_id=linked_document_id,
        created_by_user_id=actor_user_id,
        status=OutgoingCorrespondenceStatus.DRAFT,
    )
    return _finalize(db, obj)


def register_correspondence(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    correspondence_id: int,
    registry_number: str,
    registry_date: datetime | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_correspondence(db, tenant_id, correspondence_id)
    registry_dt = registry_date or datetime.now(UTC)
    target_status = "REGISTERED"
    if obj.direction == CorrespondenceDirection.INCOMING:
        _validate_transition(obj.status, IncomingCorrespondenceStatus.REGISTERED, ALLOWED_INCOMING_CORRESPONDENCE_TRANSITIONS)
    else:
        _validate_transition(obj.status, OutgoingCorrespondenceStatus.REGISTERED, ALLOWED_OUTGOING_CORRESPONDENCE_TRANSITIONS)
    entry = repo_register_correspondence(db, tenant_id, correspondence_id, registry_number, registry_dt, actor_user_id)
    entry.direction = obj.direction
    updated = repo_set_correspondence_status(db, tenant_id, correspondence_id, target_status, actor_user_id)
    updated.registry_number = registry_number
    updated.registry_date = registry_dt
    db.flush()
    _audit(
        db,
        tenant_id,
        "correspondence",
        correspondence_id,
        AuditEventType.CORRESPONDENCE_REGISTERED,
        actor_user_id,
        build_audit_action(_MODULE, "correspondence", "register"),
        payload={"registry_number": registry_number},
    )
    return _finalize(db, updated)


def route_correspondence(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    correspondence_id: int,
    to_user_id: int | None = None,
    to_role: str | None = None,
    comment: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_correspondence(db, tenant_id, correspondence_id)
    if obj.direction == CorrespondenceDirection.INCOMING:
        _validate_transition(obj.status, IncomingCorrespondenceStatus.ROUTED, ALLOWED_INCOMING_CORRESPONDENCE_TRANSITIONS)
        repo_set_correspondence_status(db, tenant_id, correspondence_id, IncomingCorrespondenceStatus.ROUTED, actor_user_id)
    repo_route_correspondence(db, tenant_id, correspondence_id, actor_user_id, to_user_id=to_user_id, to_role=to_role, comment=comment)
    updated = repo_get_correspondence(db, tenant_id, correspondence_id)
    _audit(
        db,
        tenant_id,
        "correspondence",
        correspondence_id,
        AuditEventType.CORRESPONDENCE_ROUTED,
        actor_user_id,
        build_audit_action(_MODULE, "correspondence", "route"),
        payload={"to_user_id": to_user_id, "to_role": to_role},
    )
    return _finalize(db, updated)


def mark_outgoing_sent_metadata(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    correspondence_id: int,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_require_correspondence(db, tenant_id, correspondence_id)
    if obj.direction != CorrespondenceDirection.OUTGOING:
        raise DomainValidationError("sent metadata only applies to outgoing correspondence")
    _validate_transition(obj.status, OutgoingCorrespondenceStatus.SENT_METADATA_ONLY, ALLOWED_OUTGOING_CORRESPONDENCE_TRANSITIONS)
    updated = repo_set_correspondence_status(
        db,
        tenant_id,
        correspondence_id,
        OutgoingCorrespondenceStatus.SENT_METADATA_ONLY,
        actor_user_id,
    )
    updated.sent_at = datetime.now(UTC)
    db.flush()
    _audit(
        db,
        tenant_id,
        "correspondence",
        correspondence_id,
        AuditEventType.CORRESPONDENCE_SENT_METADATA_RECORDED,
        actor_user_id,
        build_audit_action(_MODULE, "correspondence", "sent_metadata"),
        payload={"metadata_only": True},
    )
    return _finalize(db, updated)


def archive_correspondence(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    correspondence_id: int,
    reason: str | None = None,
):
    validate_tenant_id_provided(tenant_id)
    updated = repo_archive_correspondence(db, tenant_id, correspondence_id, reason, actor_user_id)
    _audit(
        db,
        tenant_id,
        "correspondence",
        correspondence_id,
        AuditEventType.CORRESPONDENCE_ARCHIVED,
        actor_user_id,
        build_audit_action(_MODULE, "correspondence", "archive"),
        payload={"reason": reason},
    )
    return _finalize(db, updated)


# ===========================================================================
# Resolutions / links
# ===========================================================================

def create_resolution(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    title: str,
    text: str,
    assigned_to_user_id: int | None = None,
    linked_document_id: int | None = None,
    linked_decree_id: int | None = None,
):
    validate_tenant_id_provided(tenant_id)
    obj = repo_create_resolution(
        db,
        tenant_id,
        title=title,
        text=text,
        created_by_user_id=actor_user_id,
        assigned_to_user_id=assigned_to_user_id,
        linked_document_id=linked_document_id,
        linked_decree_id=linked_decree_id,
    )
    _audit(
        db,
        tenant_id,
        "resolution",
        obj.id,
        AuditEventType.RESOLUTION_CREATED,
        actor_user_id,
        build_audit_action(_MODULE, "resolution", "create"),
    )
    return _finalize(db, obj)


def link_document_to_assignment(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    document_id: int,
    assignment_id: int,
    link_type: str = "SOURCE_DOCUMENT",
):
    validate_tenant_id_provided(tenant_id)
    repo_require_document(db, tenant_id, document_id)
    obj = repo_link_document_to_assignment(db, tenant_id, document_id, assignment_id, link_type, actor_user_id)
    _audit(
        db,
        tenant_id,
        "document",
        document_id,
        AuditEventType.ASSIGNMENT_LINKED,
        actor_user_id,
        build_audit_action(_MODULE, "document", "link_assignment"),
        payload={"assignment_id": assignment_id, "link_type": link_type},
    )
    return _finalize(db, obj)


def link_resolution_to_assignment(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
    resolution_id: int,
    assignment_id: int,
):
    validate_tenant_id_provided(tenant_id)
    repo_require_resolution(db, tenant_id, resolution_id)
    obj = repo_link_resolution_to_assignment(db, tenant_id, resolution_id, assignment_id, actor_user_id)
    _audit(
        db,
        tenant_id,
        "resolution",
        resolution_id,
        AuditEventType.RESOLUTION_ASSIGNMENT_LINKED,
        actor_user_id,
        build_audit_action(_MODULE, "resolution", "link_assignment"),
        payload={"assignment_id": assignment_id},
    )
    return _finalize(db, obj)


# ===========================================================================
# Read helpers used by router
# ===========================================================================

def get_document_detail(db: Session, tenant_id: int, document_id: int):
    obj = repo_require_document(db, tenant_id, document_id)
    obj.versions = repo_list_document_versions(db, tenant_id, document_id)
    obj.reviews = repo_list_document_reviews(db, tenant_id, document_id)
    obj.assignment_links = repo_list_assignment_links(db, tenant_id, document_id)
    return obj


def get_document_audit(db: Session, tenant_id: int, document_id: int):
    repo_require_document(db, tenant_id, document_id)
    return repo_list_document_audit(db, tenant_id, document_id)


def get_document_history(db: Session, tenant_id: int, document_id: int):
    repo_require_document(db, tenant_id, document_id)
    return repo_list_document_history(db, tenant_id, document_id)


def get_documents(db: Session, tenant_id: int, *, status=None, document_type=None, page=1, page_size=20):
    return repo_list_documents(db, tenant_id, status=status, document_type=document_type, page=page, page_size=page_size)


def get_decrees(db: Session, tenant_id: int, *, status=None, decree_type=None, page=1, page_size=20):
    return repo_list_decrees(db, tenant_id, status=status, decree_type=decree_type, page=page, page_size=page_size)


def get_correspondence(db: Session, tenant_id: int, *, direction=None, status=None, page=1, page_size=20):
    return repo_list_correspondence(db, tenant_id, direction=direction, status=status, page=page, page_size=page_size)


def get_correspondence_detail(db: Session, tenant_id: int, correspondence_id: int):
    return repo_require_correspondence(db, tenant_id, correspondence_id)


def get_decree_detail(db: Session, tenant_id: int, decree_id: int):
    return repo_require_decree(db, tenant_id, decree_id)


# ===========================================================================
# Dashboard
# ===========================================================================

def get_document_workflow_dashboard_summary(
    db: Session,
    tenant_id: int,
    actor_user_id: int,
) -> DashboardSummaryResponse:
    validate_tenant_id_provided(tenant_id)
    incomplete_data = False
    try:
        data = repo_compute_dashboard_summary(db, tenant_id)
    except Exception:
        data = {
            "total_documents": 0,
            "registered_documents": 0,
            "under_review_count": 0,
            "returned_for_revision_count": 0,
            "approved_count": 0,
            "signed_count": 0,
            "archived_count": 0,
            "incoming_correspondence_count": 0,
            "outgoing_correspondence_count": 0,
            "overdue_document_reviews": 0,
            "documents_linked_to_assignments": 0,
            "decrees_pending_signature": 0,
            "average_review_cycle_days": None,
        }
        incomplete_data = True
    _audit(
        db,
        tenant_id,
        "dashboard",
        tenant_id,
        AuditEventType.DASHBOARD_VIEWED,
        actor_user_id,
        build_audit_action(_MODULE, "dashboard", "view"),
    )
    return DashboardSummaryResponse(
        tenant_id=tenant_id,
        generated_at=datetime.now(UTC),
        fake_metrics=False,
        data_source="computed_from_documents",
        incomplete_data=incomplete_data,
        **data,
    )
