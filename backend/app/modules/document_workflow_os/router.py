"""Document Workflow OS — FastAPI router."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import (
    integrity_error_to_http,
    permission_error_to_http,
    tenant_not_found_to_http,
    validation_error_to_http,
)
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantResourceNotFoundError,
)
from app.core.tenant import get_current_tenant
from app.modules.document_workflow_os import permissions, service
from app.modules.document_workflow_os.dependencies import get_doc_workflow_db
from app.modules.document_workflow_os.schemas import (
    CorrespondenceArchiveRequest,
    CorrespondenceItemResponse,
    CorrespondenceListResponse,
    CorrespondenceRegisterRequest,
    CorrespondenceRouteRequest,
    DashboardSummaryResponse,
    DocumentApproveRequest,
    DocumentArchiveRequest,
    DocumentAuditEventResponse,
    DocumentAssignmentLinkResponse,
    DocumentCreateRequest,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentRegisterRequest,
    DocumentResponse,
    DocumentReturnRequest,
    DocumentSignedMetadataRequest,
    DocumentStatusHistoryResponse,
    DocumentSubmitReviewRequest,
    DocumentUpdateRequest,
    OrderDecreeApproveSigningRequest,
    OrderDecreeArchiveRequest,
    OrderDecreeCreateRequest,
    OrderDecreeLegalReviewRequest,
    OrderDecreeListResponse,
    OrderDecreeRegisterRequest,
    OrderDecreeResponse,
    OrderDecreeSignedMetadataRequest,
    OrderDecreeUpdateRequest,
    ResolutionResponse,
    ResolutionCreateRequest,
    LinkAssignmentRequest,
    IncomingCorrespondenceCreateRequest,
    OutgoingCorrespondenceCreateRequest,
    ResolutionAssignmentLinkResponse,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/documents", tags=["documents"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_doc_workflow_db)]


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        raise integrity_error_to_http(exc)
    raise exc


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant: _Tenant,
    db: _DB,
) -> DashboardSummaryResponse:
    tenant_id = int(tenant["id"])
    try:
        return service.get_document_workflow_dashboard_summary(db, tenant_id, int(actor))
    except Exception as exc:
        _handle(exc)


@router.get("/decrees", response_model=OrderDecreeListResponse)
def list_decrees_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_READ))],
    tenant: _Tenant,
    db: _DB,
    status: str | None = Query(default=None),
    decree_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> OrderDecreeListResponse:
    tenant_id = int(tenant["id"])
    try:
        items, total = service.get_decrees(db, tenant_id, status=status, decree_type=decree_type, page=page, page_size=page_size)
        return OrderDecreeListResponse(
            items=[OrderDecreeResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        _handle(exc)


@router.post("/decrees", response_model=OrderDecreeResponse, status_code=201)
def create_decree_endpoint(
    body: OrderDecreeCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_CREATE))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.create_order_decree(
            db,
            tenant_id,
            int(actor),
            body.title,
            body.decree_type,
            effective_date=body.effective_date,
            linked_document_id=body.linked_document_id,
        )
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.get("/decrees/{decree_id}", response_model=OrderDecreeResponse)
def get_decree_endpoint(
    decree_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_READ))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        return OrderDecreeResponse.model_validate(service.get_decree_detail(db, tenant_id, decree_id))
    except Exception as exc:
        _handle(exc)


@router.patch("/decrees/{decree_id}", response_model=OrderDecreeResponse)
def update_decree_endpoint(
    decree_id: int,
    body: OrderDecreeUpdateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_UPDATE))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.update_order_decree(
            db,
            tenant_id,
            int(actor),
            decree_id,
            body.version,
            title=body.title,
            effective_date=body.effective_date,
        )
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.post("/decrees/{decree_id}/legal-review", response_model=OrderDecreeResponse)
def legal_review_decree_endpoint(
    decree_id: int,
    body: OrderDecreeLegalReviewRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_LEGAL_REVIEW))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.submit_decree_for_legal_review(db, tenant_id, int(actor), decree_id, body.version, body.note)
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.post("/decrees/{decree_id}/approve-signing", response_model=OrderDecreeResponse)
def approve_signing_decree_endpoint(
    decree_id: int,
    body: OrderDecreeApproveSigningRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_APPROVE_SIGNING))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.approve_decree_for_signing(db, tenant_id, int(actor), decree_id, body.version, body.comment)
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.post("/decrees/{decree_id}/signed-metadata", response_model=OrderDecreeResponse)
def signed_metadata_decree_endpoint(
    decree_id: int,
    body: OrderDecreeSignedMetadataRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_SIGNED_METADATA))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.record_decree_signed_metadata(
            db,
            tenant_id,
            int(actor),
            decree_id,
            body.signed_by_user_id,
            body.version,
            body.signed_at,
        )
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.post("/decrees/{decree_id}/register", response_model=OrderDecreeResponse)
def register_decree_endpoint(
    decree_id: int,
    body: OrderDecreeRegisterRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_REGISTER))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.register_decree(
            db,
            tenant_id,
            int(actor),
            decree_id,
            body.registry_number,
            body.version,
            body.registry_date,
        )
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.post("/decrees/{decree_id}/archive", response_model=OrderDecreeResponse)
def archive_decree_endpoint(
    decree_id: int,
    body: OrderDecreeArchiveRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DECREES_ARCHIVE))],
    tenant: _Tenant,
    db: _DB,
) -> OrderDecreeResponse:
    tenant_id = int(tenant["id"])
    try:
        decree = service.archive_decree(db, tenant_id, int(actor), decree_id, body.reason, body.version)
        return OrderDecreeResponse.model_validate(decree)
    except Exception as exc:
        _handle(exc)


@router.get("/correspondence", response_model=CorrespondenceListResponse)
def list_correspondence_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_READ))],
    tenant: _Tenant,
    db: _DB,
    direction: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CorrespondenceListResponse:
    tenant_id = int(tenant["id"])
    try:
        items, total = service.get_correspondence(db, tenant_id, direction=direction, status=status, page=page, page_size=page_size)
        return CorrespondenceListResponse(
            items=[CorrespondenceItemResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        _handle(exc)


@router.post("/correspondence/incoming", response_model=CorrespondenceItemResponse, status_code=201)
def create_incoming_correspondence_endpoint(
    body: IncomingCorrespondenceCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_CREATE))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        item = service.create_incoming_correspondence(
            db,
            tenant_id,
            int(actor),
            body.subject,
            body.correspondence_type,
            sender_name=body.sender_name,
            sender_organization=body.sender_organization,
            received_at=body.received_at,
            linked_document_id=body.linked_document_id,
        )
        return CorrespondenceItemResponse.model_validate(item)
    except Exception as exc:
        _handle(exc)


@router.post("/correspondence/outgoing", response_model=CorrespondenceItemResponse, status_code=201)
def create_outgoing_correspondence_endpoint(
    body: OutgoingCorrespondenceCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_CREATE))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        item = service.create_outgoing_correspondence(
            db,
            tenant_id,
            int(actor),
            body.subject,
            body.correspondence_type,
            recipient_name=body.recipient_name,
            recipient_organization=body.recipient_organization,
            linked_document_id=body.linked_document_id,
        )
        return CorrespondenceItemResponse.model_validate(item)
    except Exception as exc:
        _handle(exc)


@router.get("/correspondence/{correspondence_id}", response_model=CorrespondenceItemResponse)
def get_correspondence_endpoint(
    correspondence_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_READ))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        return CorrespondenceItemResponse.model_validate(service.get_correspondence_detail(db, tenant_id, correspondence_id))
    except Exception as exc:
        _handle(exc)


@router.post("/correspondence/{correspondence_id}/register", response_model=CorrespondenceItemResponse)
def register_correspondence_endpoint(
    correspondence_id: int,
    body: CorrespondenceRegisterRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_REGISTER))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        item = service.register_correspondence(db, tenant_id, int(actor), correspondence_id, body.registry_number, body.registry_date)
        return CorrespondenceItemResponse.model_validate(item)
    except Exception as exc:
        _handle(exc)


@router.post("/correspondence/{correspondence_id}/route", response_model=CorrespondenceItemResponse)
def route_correspondence_endpoint(
    correspondence_id: int,
    body: CorrespondenceRouteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_ROUTE))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        item = service.route_correspondence(
            db,
            tenant_id,
            int(actor),
            correspondence_id,
            to_user_id=body.to_user_id,
            to_role=body.to_role,
            comment=body.route_comment,
        )
        return CorrespondenceItemResponse.model_validate(item)
    except Exception as exc:
        _handle(exc)


@router.post("/correspondence/{correspondence_id}/sent-metadata", response_model=CorrespondenceItemResponse)
def sent_metadata_correspondence_endpoint(
    correspondence_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_SENT_METADATA))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        item = service.mark_outgoing_sent_metadata(db, tenant_id, int(actor), correspondence_id)
        return CorrespondenceItemResponse.model_validate(item)
    except Exception as exc:
        _handle(exc)


@router.post("/correspondence/{correspondence_id}/archive", response_model=CorrespondenceItemResponse)
def archive_correspondence_endpoint(
    correspondence_id: int,
    body: CorrespondenceArchiveRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CORRESPONDENCE_ARCHIVE))],
    tenant: _Tenant,
    db: _DB,
) -> CorrespondenceItemResponse:
    tenant_id = int(tenant["id"])
    try:
        item = service.archive_correspondence(db, tenant_id, int(actor), correspondence_id, body.reason)
        return CorrespondenceItemResponse.model_validate(item)
    except Exception as exc:
        _handle(exc)


@router.post("/resolutions", response_model=ResolutionResponse, status_code=201)
def create_resolution_endpoint(
    body: ResolutionCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.RESOLUTIONS_CREATE))],
    tenant: _Tenant,
    db: _DB,
) -> ResolutionResponse:
    tenant_id = int(tenant["id"])
    try:
        resolution = service.create_resolution(
            db,
            tenant_id,
            int(actor),
            body.title,
            body.text,
            assigned_to_user_id=body.assigned_to_user_id,
            linked_document_id=body.linked_document_id,
            linked_decree_id=body.linked_decree_id,
        )
        return ResolutionResponse.model_validate(resolution)
    except Exception as exc:
        _handle(exc)


@router.post("/resolutions/{resolution_id}/link-assignment/{assignment_id}", response_model=ResolutionAssignmentLinkResponse)
def link_resolution_assignment_endpoint(
    resolution_id: int,
    assignment_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.RESOLUTIONS_LINK_ASSIGNMENT))],
    tenant: _Tenant,
    db: _DB,
) -> ResolutionAssignmentLinkResponse:
    tenant_id = int(tenant["id"])
    try:
        link = service.link_resolution_to_assignment(db, tenant_id, int(actor), resolution_id, assignment_id)
        return ResolutionAssignmentLinkResponse.model_validate(link)
    except Exception as exc:
        _handle(exc)


@router.get("", response_model=DocumentListResponse)
def list_documents_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
    db: _DB,
    status: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DocumentListResponse:
    tenant_id = int(tenant["id"])
    try:
        items, total = service.get_documents(db, tenant_id, status=status, document_type=document_type, page=page, page_size=page_size)
        return DocumentListResponse(
            items=[DocumentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        _handle(exc)


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document_endpoint(
    body: DocumentCreateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.CREATE))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.create_document(
            db,
            tenant_id,
            int(actor),
            body.title,
            body.document_type,
            source_department_id=body.source_department_id,
            owner_user_id=body.owner_user_id,
            linked_assignment_id=body.linked_assignment_id,
        )
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_endpoint(
    document_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentDetailResponse:
    tenant_id = int(tenant["id"])
    try:
        return DocumentDetailResponse.model_validate(service.get_document_detail(db, tenant_id, document_id))
    except Exception as exc:
        _handle(exc)


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document_endpoint(
    document_id: int,
    body: DocumentUpdateRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.UPDATE))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.update_document(
            db,
            tenant_id,
            int(actor),
            document_id,
            body.version,
            title=body.title,
            document_type=body.document_type,
            owner_user_id=body.owner_user_id,
        )
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/register", response_model=DocumentResponse)
def register_document_endpoint(
    document_id: int,
    body: DocumentRegisterRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REGISTER))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.register_document(
            db,
            tenant_id,
            int(actor),
            document_id,
            body.registry_number,
            body.version,
            body.registry_date,
        )
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/submit-review", response_model=DocumentResponse)
def submit_review_document_endpoint(
    document_id: int,
    body: DocumentSubmitReviewRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REVIEW))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.submit_document_for_review(
            db,
            tenant_id,
            int(actor),
            document_id,
            body.version,
            reviewer_user_id=body.reviewer_user_id,
            note=body.note,
        )
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/return", response_model=DocumentResponse)
def return_document_endpoint(
    document_id: int,
    body: DocumentReturnRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REVIEW))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.return_document_for_revision(db, tenant_id, int(actor), document_id, body.version, body.reason)
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/approve", response_model=DocumentResponse)
def approve_document_endpoint(
    document_id: int,
    body: DocumentApproveRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.APPROVE))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.approve_document(db, tenant_id, int(actor), document_id, body.version, body.comment)
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/signed-metadata", response_model=DocumentResponse)
def signed_metadata_document_endpoint(
    document_id: int,
    body: DocumentSignedMetadataRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SIGNED_METADATA_RECORD))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.record_signed_metadata(
            db,
            tenant_id,
            int(actor),
            document_id,
            body.signed_by_user_id,
            body.version,
            body.signed_at,
            body.note,
        )
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/archive", response_model=DocumentResponse)
def archive_document_endpoint(
    document_id: int,
    body: DocumentArchiveRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ARCHIVE))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentResponse:
    tenant_id = int(tenant["id"])
    try:
        document = service.archive_document(db, tenant_id, int(actor), document_id, body.reason, body.version)
        return DocumentResponse.model_validate(document)
    except Exception as exc:
        _handle(exc)


@router.get("/{document_id}/audit", response_model=list[DocumentAuditEventResponse])
def get_document_audit_endpoint(
    document_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))],
    tenant: _Tenant,
    db: _DB,
) -> list[DocumentAuditEventResponse]:
    tenant_id = int(tenant["id"])
    try:
        return [DocumentAuditEventResponse.model_validate(item) for item in service.get_document_audit(db, tenant_id, document_id)]
    except Exception as exc:
        _handle(exc)


@router.get("/{document_id}/history", response_model=list[DocumentStatusHistoryResponse])
def get_document_history_endpoint(
    document_id: int,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))],
    tenant: _Tenant,
    db: _DB,
) -> list[DocumentStatusHistoryResponse]:
    tenant_id = int(tenant["id"])
    try:
        return [DocumentStatusHistoryResponse.model_validate(item) for item in service.get_document_history(db, tenant_id, document_id)]
    except Exception as exc:
        _handle(exc)


@router.post("/{document_id}/link-assignment/{assignment_id}", response_model=DocumentAssignmentLinkResponse)
def link_document_assignment_endpoint(
    document_id: int,
    assignment_id: int,
    body: LinkAssignmentRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DOCUMENTS_LINK_ASSIGNMENT))],
    tenant: _Tenant,
    db: _DB,
) -> DocumentAssignmentLinkResponse:
    tenant_id = int(tenant["id"])
    try:
        link = service.link_document_to_assignment(db, tenant_id, int(actor), document_id, assignment_id, body.link_type)
        return DocumentAssignmentLinkResponse.model_validate(link)
    except Exception as exc:
        _handle(exc)
