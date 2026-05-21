"""Document Workflow OS — Pydantic Schemas.

35 schemas: 20 request + 15 response.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ===========================================================================
# Request schemas (20)
# ===========================================================================

# ---------------------------------------------------------------------------
# Document request schemas (8)
# ---------------------------------------------------------------------------

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    document_type: str = Field(..., min_length=1, max_length=32)
    source_department_id: int | None = None
    owner_user_id: int | None = None
    linked_assignment_id: int | None = None


class DocumentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    document_type: str | None = None
    owner_user_id: int | None = None
    version: int = Field(..., ge=1)


class DocumentRegisterRequest(BaseModel):
    registry_number: str = Field(..., min_length=1, max_length=64)
    registry_date: datetime | None = None
    version: int = Field(..., ge=1)


class DocumentSubmitReviewRequest(BaseModel):
    reviewer_user_id: int | None = None
    note: str | None = None
    version: int = Field(..., ge=1)


class DocumentReturnRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)


class DocumentApproveRequest(BaseModel):
    comment: str | None = None
    version: int = Field(..., ge=1)


class DocumentSignedMetadataRequest(BaseModel):
    signed_by_user_id: int
    signed_at: datetime | None = None
    note: str | None = None
    version: int = Field(..., ge=1)


class DocumentArchiveRequest(BaseModel):
    reason: str | None = None
    version: int = Field(..., ge=1)


class DocumentVersionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body_text: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class DocumentReviewCreateRequest(BaseModel):
    reviewer_user_id: int
    decision: str = Field(..., min_length=1, max_length=32)
    comment: str | None = None


# ---------------------------------------------------------------------------
# Decree request schemas (5)
# ---------------------------------------------------------------------------

class OrderDecreeCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    decree_type: str = Field(..., min_length=1, max_length=32)
    effective_date: date | None = None
    linked_document_id: int | None = None


class OrderDecreeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    effective_date: date | None = None
    version: int = Field(..., ge=1)


class OrderDecreeLegalReviewRequest(BaseModel):
    note: str | None = None
    version: int = Field(..., ge=1)


class OrderDecreeApproveSigningRequest(BaseModel):
    comment: str | None = None
    version: int = Field(..., ge=1)


class OrderDecreeSignedMetadataRequest(BaseModel):
    signed_by_user_id: int
    signed_at: datetime | None = None
    version: int = Field(..., ge=1)


class OrderDecreeRegisterRequest(BaseModel):
    registry_number: str = Field(..., min_length=1, max_length=64)
    registry_date: datetime | None = None
    version: int = Field(..., ge=1)


class OrderDecreeArchiveRequest(BaseModel):
    reason: str | None = None
    version: int = Field(..., ge=1)


# ---------------------------------------------------------------------------
# Correspondence request schemas (4)
# ---------------------------------------------------------------------------

class IncomingCorrespondenceCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    correspondence_type: str = Field(default="LETTER", max_length=32)
    sender_name: str | None = None
    sender_organization: str | None = None
    received_at: datetime | None = None
    linked_document_id: int | None = None


class OutgoingCorrespondenceCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    correspondence_type: str = Field(default="LETTER", max_length=32)
    recipient_name: str | None = None
    recipient_organization: str | None = None
    linked_document_id: int | None = None


class CorrespondenceRouteRequest(BaseModel):
    to_user_id: int | None = None
    to_role: str | None = None
    route_comment: str | None = None


class CorrespondenceRegisterRequest(BaseModel):
    registry_number: str = Field(..., min_length=1, max_length=64)
    registry_date: datetime | None = None


class CorrespondenceArchiveRequest(BaseModel):
    reason: str | None = None


# ---------------------------------------------------------------------------
# Resolution / integration request schemas (2)
# ---------------------------------------------------------------------------

class ResolutionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    text: str = Field(..., min_length=1)
    assigned_to_user_id: int | None = None
    linked_document_id: int | None = None
    linked_decree_id: int | None = None


class LinkAssignmentRequest(BaseModel):
    link_type: str = Field(default="SOURCE_DOCUMENT", max_length=32)

    @field_validator("link_type")
    @classmethod
    def validate_link_type(cls, v: str) -> str:
        allowed = {"SOURCE_DOCUMENT", "EXECUTION_DOCUMENT", "EVIDENCE"}
        if v not in allowed:
            raise ValueError(f"link_type must be one of {allowed}")
        return v


# ===========================================================================
# Response schemas (15)
# ===========================================================================

class DocumentVersionResponse(BaseModel):
    id: int
    document_id: int
    version_number: int
    title: str
    body_text: str | None
    metadata_json: dict[str, Any]
    created_by_user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusHistoryResponse(BaseModel):
    id: int
    document_id: int
    from_status: str | None
    to_status: str
    actor_user_id: int
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentAuditEventResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    event_type: str
    actor_user_id: int
    actor_role: str | None
    action: str
    payload_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentReviewResponse(BaseModel):
    id: int
    document_id: int
    reviewer_user_id: int
    decision: str
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentAssignmentLinkResponse(BaseModel):
    id: int
    document_id: int
    assignment_id: int
    link_type: str
    created_by_user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    document_type: str
    status: str
    registry_number: str | None
    registry_date: datetime | None
    source_department_id: int | None
    owner_user_id: int | None
    created_by_user_id: int
    linked_assignment_id: int | None
    linked_decree_id: int | None
    version: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    versions: list[DocumentVersionResponse] = Field(default_factory=list)
    reviews: list[DocumentReviewResponse] = Field(default_factory=list)
    assignment_links: list[DocumentAssignmentLinkResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class OrderDecreeResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    decree_type: str
    status: str
    registry_number: str | None
    registry_date: datetime | None
    effective_date: date | None
    signed_by_user_id: int | None
    signed_at: datetime | None
    linked_document_id: int | None
    linked_assignment_id: int | None
    created_by_user_id: int
    version: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class OrderDecreeListResponse(BaseModel):
    items: list[OrderDecreeResponse]
    total: int
    page: int
    page_size: int


class CorrespondenceItemResponse(BaseModel):
    id: int
    tenant_id: int
    direction: str
    subject: str
    correspondence_type: str
    sender_name: str | None
    sender_organization: str | None
    recipient_name: str | None
    recipient_organization: str | None
    status: str
    registry_number: str | None
    registry_date: datetime | None
    received_at: datetime | None
    sent_at: datetime | None
    linked_document_id: int | None
    linked_assignment_id: int | None
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class CorrespondenceListResponse(BaseModel):
    items: list[CorrespondenceItemResponse]
    total: int
    page: int
    page_size: int


class CorrespondenceRouteResponse(BaseModel):
    id: int
    correspondence_id: int
    from_user_id: int | None
    to_user_id: int | None
    to_role: str | None
    route_comment: str | None
    created_by_user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ResolutionResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    text: str
    status: str
    created_by_user_id: int
    assigned_to_user_id: int | None
    linked_document_id: int | None
    linked_decree_id: int | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class ResolutionAssignmentLinkResponse(BaseModel):
    id: int
    resolution_id: int
    assignment_id: int
    created_by_user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummaryResponse(BaseModel):
    tenant_id: int
    total_documents: int
    registered_documents: int
    under_review_count: int
    returned_for_revision_count: int
    approved_count: int
    signed_count: int
    archived_count: int
    incoming_correspondence_count: int
    outgoing_correspondence_count: int
    overdue_document_reviews: int
    documents_linked_to_assignments: int
    decrees_pending_signature: int
    average_review_cycle_days: float | None
    data_source: str = "computed_from_documents"
    fake_metrics: bool = False
    generated_at: datetime
    incomplete_data: bool = False
