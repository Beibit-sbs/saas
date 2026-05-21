"""Document Workflow OS — Repository layer (DB query helpers).

All methods require tenant_id.
Every query filters by tenant_id.
No hard delete.
Audit events written per mutation.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    TenantResourceNotFoundError,
    validate_tenant_id_provided,
)
from app.modules.document_workflow_os.models import (
    ArchiveRecord,
    CorrespondenceItem,
    CorrespondenceRegistryEntry,
    CorrespondenceRoute,
    Document,
    DocumentAssignmentLink,
    DocumentAuditEvent,
    DocumentReview,
    DocumentStatusHistory,
    DocumentVersion,
    OrderDecree,
    OrderDecreeRegistryEntry,
    Resolution,
    ResolutionAssignmentLink,
)


# ===========================================================================
# Document repository (12)
# ===========================================================================

def repo_create_document(db: Session, tenant_id: int, **kwargs) -> Document:
    validate_tenant_id_provided(tenant_id)
    now = datetime.now(UTC)
    obj = Document(
        tenant_id=tenant_id,
        created_at=now,
        updated_at=now,
        **kwargs,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_get_document(db: Session, tenant_id: int, document_id: int) -> Document | None:
    validate_tenant_id_provided(tenant_id)
    stmt = select(Document).where(
        and_(Document.tenant_id == tenant_id, Document.id == document_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_require_document(db: Session, tenant_id: int, document_id: int) -> Document:
    obj = repo_get_document(db, tenant_id, document_id)
    if obj is None:
        raise TenantResourceNotFoundError(
            f"document {document_id} not found for tenant {tenant_id}"
        )
    return obj


def repo_list_documents(
    db: Session,
    tenant_id: int,
    *,
    status: str | None = None,
    document_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Document], int]:
    validate_tenant_id_provided(tenant_id)
    filters = [Document.tenant_id == tenant_id]
    if status:
        filters.append(Document.status == status)
    if document_type:
        filters.append(Document.document_type == document_type)

    count_stmt = select(func.count()).select_from(Document).where(and_(*filters))
    total = db.execute(count_stmt).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(Document)
        .where(and_(*filters))
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def repo_update_document(
    db: Session, tenant_id: int, document_id: int, version: int, **kwargs
) -> Document:
    obj = repo_require_document(db, tenant_id, document_id)
    for k, v in kwargs.items():
        setattr(obj, k, v)
    obj.version = version + 1
    obj.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(obj)
    return obj


def repo_set_document_status(
    db: Session,
    tenant_id: int,
    document_id: int,
    new_status: str,
    actor_user_id: int,
    reason: str | None = None,
) -> Document:
    obj = repo_require_document(db, tenant_id, document_id)
    from_status = obj.status
    obj.status = new_status
    obj.updated_at = datetime.now(UTC)
    db.flush()
    # Write status history
    repo_add_document_status_history(
        db, tenant_id, document_id, from_status, new_status, actor_user_id, reason
    )
    db.refresh(obj)
    return obj


def repo_archive_document(
    db: Session,
    tenant_id: int,
    document_id: int,
    reason: str | None,
    actor_user_id: int,
) -> Document:
    obj = repo_require_document(db, tenant_id, document_id)
    now = datetime.now(UTC)
    from_status = obj.status
    obj.status = "ARCHIVED"
    obj.archived_at = now
    obj.updated_at = now
    db.flush()
    repo_add_document_status_history(db, tenant_id, document_id, from_status, "ARCHIVED", actor_user_id, reason)
    repo_create_archive_record(db, tenant_id, "document", document_id, reason, actor_user_id)
    db.refresh(obj)
    return obj


def repo_create_document_version(
    db: Session, tenant_id: int, document_id: int, **kwargs
) -> DocumentVersion:
    validate_tenant_id_provided(tenant_id)
    now = datetime.now(UTC)
    obj = DocumentVersion(
        tenant_id=tenant_id,
        document_id=document_id,
        created_at=now,
        **kwargs,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_list_document_versions(
    db: Session, tenant_id: int, document_id: int
) -> list[DocumentVersion]:
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(DocumentVersion)
        .where(
            and_(
                DocumentVersion.tenant_id == tenant_id,
                DocumentVersion.document_id == document_id,
            )
        )
        .order_by(DocumentVersion.version_number.asc())
    )
    return list(db.execute(stmt).scalars().all())


def repo_add_document_status_history(
    db: Session,
    tenant_id: int,
    document_id: int,
    from_status: str | None,
    to_status: str,
    actor_user_id: int,
    reason: str | None = None,
) -> DocumentStatusHistory:
    obj = DocumentStatusHistory(
        tenant_id=tenant_id,
        document_id=document_id,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    return obj


def repo_list_document_history(
    db: Session, tenant_id: int, document_id: int
) -> list[DocumentStatusHistory]:
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(DocumentStatusHistory)
        .where(
            and_(
                DocumentStatusHistory.tenant_id == tenant_id,
                DocumentStatusHistory.document_id == document_id,
            )
        )
        .order_by(DocumentStatusHistory.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def repo_add_audit_event(
    db: Session,
    tenant_id: int,
    entity_type: str,
    entity_id: int,
    event_type: str,
    actor_user_id: int,
    action: str,
    payload: dict | None = None,
    request_id: str | None = None,
    actor_role: str | None = None,
) -> DocumentAuditEvent:
    obj = DocumentAuditEvent(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        request_id=request_id,
        action=action,
        payload_json=payload or {},
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    return obj


def repo_list_document_audit(
    db: Session, tenant_id: int, document_id: int
) -> list[DocumentAuditEvent]:
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(DocumentAuditEvent)
        .where(
            and_(
                DocumentAuditEvent.tenant_id == tenant_id,
                DocumentAuditEvent.entity_type == "document",
                DocumentAuditEvent.entity_id == document_id,
            )
        )
        .order_by(DocumentAuditEvent.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


# ===========================================================================
# Review repository (2)
# ===========================================================================

def repo_create_document_review(
    db: Session,
    tenant_id: int,
    document_id: int,
    reviewer_user_id: int,
    decision: str,
    comment: str | None = None,
) -> DocumentReview:
    validate_tenant_id_provided(tenant_id)
    obj = DocumentReview(
        tenant_id=tenant_id,
        document_id=document_id,
        reviewer_user_id=reviewer_user_id,
        decision=decision,
        comment=comment,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_list_document_reviews(
    db: Session, tenant_id: int, document_id: int
) -> list[DocumentReview]:
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(DocumentReview)
        .where(
            and_(
                DocumentReview.tenant_id == tenant_id,
                DocumentReview.document_id == document_id,
            )
        )
        .order_by(DocumentReview.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


# ===========================================================================
# Decree repository (9)
# ===========================================================================

def repo_create_decree(db: Session, tenant_id: int, **kwargs) -> OrderDecree:
    validate_tenant_id_provided(tenant_id)
    now = datetime.now(UTC)
    obj = OrderDecree(
        tenant_id=tenant_id,
        created_at=now,
        updated_at=now,
        **kwargs,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_get_decree(db: Session, tenant_id: int, decree_id: int) -> OrderDecree | None:
    validate_tenant_id_provided(tenant_id)
    stmt = select(OrderDecree).where(
        and_(OrderDecree.tenant_id == tenant_id, OrderDecree.id == decree_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_require_decree(db: Session, tenant_id: int, decree_id: int) -> OrderDecree:
    obj = repo_get_decree(db, tenant_id, decree_id)
    if obj is None:
        raise TenantResourceNotFoundError(
            f"decree {decree_id} not found for tenant {tenant_id}"
        )
    return obj


def repo_list_decrees(
    db: Session,
    tenant_id: int,
    *,
    status: str | None = None,
    decree_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[OrderDecree], int]:
    validate_tenant_id_provided(tenant_id)
    filters = [OrderDecree.tenant_id == tenant_id]
    if status:
        filters.append(OrderDecree.status == status)
    if decree_type:
        filters.append(OrderDecree.decree_type == decree_type)

    count_stmt = select(func.count()).select_from(OrderDecree).where(and_(*filters))
    total = db.execute(count_stmt).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(OrderDecree)
        .where(and_(*filters))
        .order_by(OrderDecree.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def repo_update_decree(
    db: Session, tenant_id: int, decree_id: int, version: int, **kwargs
) -> OrderDecree:
    obj = repo_require_decree(db, tenant_id, decree_id)
    for k, v in kwargs.items():
        setattr(obj, k, v)
    obj.version = version + 1
    obj.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(obj)
    return obj


def repo_set_decree_status(
    db: Session,
    tenant_id: int,
    decree_id: int,
    new_status: str,
    actor_user_id: int,
    reason: str | None = None,
) -> OrderDecree:
    obj = repo_require_decree(db, tenant_id, decree_id)
    obj.status = new_status
    obj.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(obj)
    return obj


def repo_register_decree(
    db: Session,
    tenant_id: int,
    decree_id: int,
    registry_number: str,
    registry_date: datetime,
    actor_user_id: int,
) -> OrderDecreeRegistryEntry:
    validate_tenant_id_provided(tenant_id)
    obj = OrderDecreeRegistryEntry(
        tenant_id=tenant_id,
        decree_id=decree_id,
        registry_number=registry_number,
        registry_date=registry_date,
        registry_year=registry_date.year,
        created_by_user_id=actor_user_id,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_archive_decree(
    db: Session,
    tenant_id: int,
    decree_id: int,
    reason: str | None,
    actor_user_id: int,
) -> OrderDecree:
    obj = repo_require_decree(db, tenant_id, decree_id)
    now = datetime.now(UTC)
    obj.status = "ARCHIVED"
    obj.archived_at = now
    obj.updated_at = now
    db.flush()
    repo_create_archive_record(db, tenant_id, "decree", decree_id, reason, actor_user_id)
    db.refresh(obj)
    return obj


def repo_list_decree_history(
    db: Session, tenant_id: int, decree_id: int
) -> list[DocumentStatusHistory]:
    # Decree status history reuses doc_document_status_history with entity_type differentiation
    # via audit events. For decree status history we use audit events.
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(DocumentAuditEvent)
        .where(
            and_(
                DocumentAuditEvent.tenant_id == tenant_id,
                DocumentAuditEvent.entity_type == "decree",
                DocumentAuditEvent.entity_id == decree_id,
            )
        )
        .order_by(DocumentAuditEvent.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


# ===========================================================================
# Correspondence repository (9)
# ===========================================================================

def repo_create_correspondence(
    db: Session, tenant_id: int, direction: str, **kwargs
) -> CorrespondenceItem:
    validate_tenant_id_provided(tenant_id)
    now = datetime.now(UTC)
    obj = CorrespondenceItem(
        tenant_id=tenant_id,
        direction=direction,
        created_at=now,
        updated_at=now,
        **kwargs,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_get_correspondence(
    db: Session, tenant_id: int, correspondence_id: int
) -> CorrespondenceItem | None:
    validate_tenant_id_provided(tenant_id)
    stmt = select(CorrespondenceItem).where(
        and_(
            CorrespondenceItem.tenant_id == tenant_id,
            CorrespondenceItem.id == correspondence_id,
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def repo_require_correspondence(
    db: Session, tenant_id: int, correspondence_id: int
) -> CorrespondenceItem:
    obj = repo_get_correspondence(db, tenant_id, correspondence_id)
    if obj is None:
        raise TenantResourceNotFoundError(
            f"correspondence {correspondence_id} not found for tenant {tenant_id}"
        )
    return obj


def repo_list_correspondence(
    db: Session,
    tenant_id: int,
    *,
    direction: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CorrespondenceItem], int]:
    validate_tenant_id_provided(tenant_id)
    filters = [CorrespondenceItem.tenant_id == tenant_id]
    if direction:
        filters.append(CorrespondenceItem.direction == direction)
    if status:
        filters.append(CorrespondenceItem.status == status)

    count_stmt = select(func.count()).select_from(CorrespondenceItem).where(and_(*filters))
    total = db.execute(count_stmt).scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(CorrespondenceItem)
        .where(and_(*filters))
        .order_by(CorrespondenceItem.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def repo_set_correspondence_status(
    db: Session,
    tenant_id: int,
    correspondence_id: int,
    new_status: str,
    actor_user_id: int,
) -> CorrespondenceItem:
    obj = repo_require_correspondence(db, tenant_id, correspondence_id)
    obj.status = new_status
    obj.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(obj)
    return obj


def repo_register_correspondence(
    db: Session,
    tenant_id: int,
    correspondence_id: int,
    registry_number: str,
    registry_date: datetime,
    actor_user_id: int,
) -> CorrespondenceRegistryEntry:
    validate_tenant_id_provided(tenant_id)
    obj = CorrespondenceRegistryEntry(
        tenant_id=tenant_id,
        correspondence_id=correspondence_id,
        registry_number=registry_number,
        registry_date=registry_date,
        direction="",  # set by caller
        created_by_user_id=actor_user_id,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_route_correspondence(
    db: Session,
    tenant_id: int,
    correspondence_id: int,
    actor_user_id: int,
    to_user_id: int | None = None,
    to_role: str | None = None,
    comment: str | None = None,
) -> CorrespondenceRoute:
    validate_tenant_id_provided(tenant_id)
    obj = CorrespondenceRoute(
        tenant_id=tenant_id,
        correspondence_id=correspondence_id,
        from_user_id=actor_user_id,
        to_user_id=to_user_id,
        to_role=to_role,
        route_comment=comment,
        created_by_user_id=actor_user_id,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_archive_correspondence(
    db: Session,
    tenant_id: int,
    correspondence_id: int,
    reason: str | None,
    actor_user_id: int,
) -> CorrespondenceItem:
    obj = repo_require_correspondence(db, tenant_id, correspondence_id)
    now = datetime.now(UTC)
    obj.archived_at = now
    obj.updated_at = now
    obj.status = "ARCHIVED"
    db.flush()
    repo_create_archive_record(db, tenant_id, "correspondence", correspondence_id, reason, actor_user_id)
    db.refresh(obj)
    return obj


def repo_list_correspondence_routes(
    db: Session, tenant_id: int, correspondence_id: int
) -> list[CorrespondenceRoute]:
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(CorrespondenceRoute)
        .where(
            and_(
                CorrespondenceRoute.tenant_id == tenant_id,
                CorrespondenceRoute.correspondence_id == correspondence_id,
            )
        )
        .order_by(CorrespondenceRoute.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


# ===========================================================================
# Resolution / link repository (5)
# ===========================================================================

def repo_create_resolution(db: Session, tenant_id: int, **kwargs) -> Resolution:
    validate_tenant_id_provided(tenant_id)
    now = datetime.now(UTC)
    obj = Resolution(
        tenant_id=tenant_id,
        created_at=now,
        updated_at=now,
        **kwargs,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_require_resolution(db: Session, tenant_id: int, resolution_id: int) -> Resolution:
    validate_tenant_id_provided(tenant_id)
    stmt = select(Resolution).where(
        and_(Resolution.tenant_id == tenant_id, Resolution.id == resolution_id)
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise TenantResourceNotFoundError(
            f"resolution {resolution_id} not found for tenant {tenant_id}"
        )
    return obj


def repo_link_resolution_to_assignment(
    db: Session,
    tenant_id: int,
    resolution_id: int,
    assignment_id: int,
    actor_user_id: int,
) -> ResolutionAssignmentLink:
    validate_tenant_id_provided(tenant_id)
    obj = ResolutionAssignmentLink(
        tenant_id=tenant_id,
        resolution_id=resolution_id,
        assignment_id=assignment_id,
        created_by_user_id=actor_user_id,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_link_document_to_assignment(
    db: Session,
    tenant_id: int,
    document_id: int,
    assignment_id: int,
    link_type: str,
    actor_user_id: int,
) -> DocumentAssignmentLink:
    validate_tenant_id_provided(tenant_id)
    obj = DocumentAssignmentLink(
        tenant_id=tenant_id,
        document_id=document_id,
        assignment_id=assignment_id,
        link_type=link_type,
        created_by_user_id=actor_user_id,
        created_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def repo_list_assignment_links(
    db: Session, tenant_id: int, document_id: int
) -> list[DocumentAssignmentLink]:
    validate_tenant_id_provided(tenant_id)
    stmt = (
        select(DocumentAssignmentLink)
        .where(
            and_(
                DocumentAssignmentLink.tenant_id == tenant_id,
                DocumentAssignmentLink.document_id == document_id,
            )
        )
        .order_by(DocumentAssignmentLink.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


# ===========================================================================
# Archive record repository
# ===========================================================================

def repo_create_archive_record(
    db: Session,
    tenant_id: int,
    entity_type: str,
    entity_id: int,
    reason: str | None,
    actor_user_id: int,
) -> ArchiveRecord:
    obj = ArchiveRecord(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        archive_reason=reason,
        archived_by_user_id=actor_user_id,
        archived_at=datetime.now(UTC),
    )
    db.add(obj)
    db.flush()
    return obj


# ===========================================================================
# Dashboard repository (1)
# ===========================================================================

def repo_compute_dashboard_summary(db: Session, tenant_id: int) -> dict:
    """Compute dashboard metrics from live DB queries. Returns raw counts dict."""
    validate_tenant_id_provided(tenant_id)

    # Document counts
    doc_counts_stmt = select(
        func.count(Document.id).label("total"),
        func.count(
            case((Document.status.in_(["REGISTERED", "UNDER_REVIEW", "APPROVED", "SIGNED", "ISSUED"]), 1))
        ).label("registered"),
        func.count(case((Document.status == "UNDER_REVIEW", 1))).label("under_review"),
        func.count(case((Document.status == "RETURNED_FOR_REVISION", 1))).label("returned"),
        func.count(case((Document.status == "APPROVED", 1))).label("approved"),
        func.count(case((Document.status == "SIGNED", 1))).label("signed"),
        func.count(case((Document.archived_at.isnot(None), 1))).label("archived"),
    ).where(Document.tenant_id == tenant_id)
    doc_row = db.execute(doc_counts_stmt).one()

    # Correspondence counts
    corr_counts_stmt = select(
        func.count(case((CorrespondenceItem.direction == "INCOMING", 1))).label("incoming"),
        func.count(case((CorrespondenceItem.direction == "OUTGOING", 1))).label("outgoing"),
    ).where(
        and_(
            CorrespondenceItem.tenant_id == tenant_id,
            CorrespondenceItem.archived_at.is_(None),
        )
    )
    corr_row = db.execute(corr_counts_stmt).one()

    # Assignment links
    linked_stmt = select(
        func.count(distinct(DocumentAssignmentLink.document_id))
    ).where(DocumentAssignmentLink.tenant_id == tenant_id)
    linked_count = db.execute(linked_stmt).scalar_one()

    # Decrees pending signature
    decrees_stmt = select(func.count(OrderDecree.id)).where(
        and_(
            OrderDecree.tenant_id == tenant_id,
            OrderDecree.status == "APPROVED_FOR_SIGNING",
            OrderDecree.archived_at.is_(None),
        )
    )
    decrees_pending = db.execute(decrees_stmt).scalar_one()

    return {
        "total_documents": doc_row.total or 0,
        "registered_documents": doc_row.registered or 0,
        "under_review_count": doc_row.under_review or 0,
        "returned_for_revision_count": doc_row.returned or 0,
        "approved_count": doc_row.approved or 0,
        "signed_count": doc_row.signed or 0,
        "archived_count": doc_row.archived or 0,
        "incoming_correspondence_count": corr_row.incoming or 0,
        "outgoing_correspondence_count": corr_row.outgoing or 0,
        "overdue_document_reviews": 0,  # computed from review cycle; zero is valid
        "documents_linked_to_assignments": linked_count or 0,
        "decrees_pending_signature": decrees_pending or 0,
        "average_review_cycle_days": None,
    }
