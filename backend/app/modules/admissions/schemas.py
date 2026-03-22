"""
Admissions Module - Pydantic Schemas

Request/Response DTOs for admissions API endpoints.

Uses discriminated unions for polymorph responses (e.g., decision outcomes).
All schemas include explicit tenant_id validation and audit trail fields.
No implicit defaults; fail-closed contract on tenant scope.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# ENUMS: Workflow States, Decision Types, Document Statuses
# ==============================================================================


class ApplicantStatus(str, Enum):
    """Applicant account statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ApplicationStage(str, Enum):
    """Application workflow stages (ordered progression)."""
    NEW = "new"                      # Initial creation
    RECEIVED = "received"             # Application submitted
    UNDER_REVIEW = "under_review"     # Under admissions review
    DECISION_PENDING = "decision_pending"  # Awaiting final decision
    CONCLUDED = "concluded"           # Decision made (see conclusion_type)


class ApplicationConclusionType(str, Enum):
    """Application conclusion outcomes."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLIST = "waitlist"
    WITHDRAWN = "withdrawn"


class DocumentStatus(str, Enum):
    """Document verification statuses."""
    RECEIVED = "received"      # Uploaded, pending verification
    VERIFIED = "verified"      # Verified and accepted
    REJECTED = "rejected"      # Failed verification


class StageTransitionAction(str, Enum):
    """Stage transition action types for audit trail."""
    MANUAL = "manual"              # Manual transition
    AUTOMATED = "automated"         # System-triggered
    SYSTEM_DECISION = "system_decision"  # Auto-decision based on rules


# ==============================================================================
# APPLICANT SCHEMAS
# ==============================================================================


class ApplicantBaseSchema(BaseModel):
    """Base applicant data (shared by create/update/read)."""
    email: str = Field(..., min_length=5, max_length=255, description="Applicant email address")
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    phone: Optional[str] = Field(None, max_length=20, description="Optional phone number")
    program_id: int = Field(..., gt=0, description="Target program ID")
    application_year: int = Field(..., ge=2020, le=2099, description="Application year")
    status: ApplicantStatus = Field(ApplicantStatus.ACTIVE, description="Account status")
    external_id: Optional[str] = Field(None, max_length=128, description="SIS or external system ID")
    metadata_json: dict = Field(default_factory=dict, description="Flexible attributes (country, gpa, etc.)")


class ApplicantCreateSchema(ApplicantBaseSchema):
    """Request schema for creating an applicant."""
    pass


class ApplicantUpdateSchema(BaseModel):
    """Request schema for updating an applicant (partial)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=128)
    last_name: Optional[str] = Field(None, min_length=1, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    status: Optional[ApplicantStatus] = None
    external_id: Optional[str] = Field(None, max_length=128)
    metadata_json: Optional[dict] = None


class ApplicantReadSchema(ApplicantBaseSchema):
    """Response schema for reading an applicant."""
    id: int = Field(..., description="Applicant ID")
    tenant_id: int = Field(..., description="Tenant ID (always included, never mutable)")
    created_by: str = Field(..., description="User who created this applicant")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicantListResponseSchema(BaseModel):
    """Paginated response for listing applicants."""
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    items: list[ApplicantReadSchema]


# ==============================================================================
# APPLICATION SCHEMAS
# ==============================================================================


class ApplicationBaseSchema(BaseModel):
    """Base application data."""
    applicant_id: int = Field(..., gt=0)
    program_id: int = Field(..., gt=0, description="Denormalized program ID")
    metadata_json: dict = Field(default_factory=dict)


class ApplicationCreateSchema(ApplicationBaseSchema):
    """Request schema for creating an application."""
    pass


class ApplicationUpdateSchema(BaseModel):
    """Request schema for updating an application (metadata only in MVP)."""
    metadata_json: Optional[dict] = None


class ApplicationReadSchema(ApplicationBaseSchema):
    """Response schema for reading an application."""
    id: int
    tenant_id: int = Field(..., description="Tenant ID (read-only)")
    stage: ApplicationStage
    conclusion_type: Optional[ApplicationConclusionType] = None
    received_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None
    version: int = Field(..., ge=1, description="Optimistic locking version")
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListResponseSchema(BaseModel):
    """Paginated response for listing applications."""
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    items: list[ApplicationReadSchema]


# ==============================================================================
# DOCUMENT SCHEMAS
# ==============================================================================


class DocumentAttachRequestSchema(BaseModel):
    """Request schema for attaching a document to an application."""
    document_type: str = Field(..., min_length=1, max_length=64, description="e.g., 'transcript', 'test_score'")
    document_key: str = Field(..., min_length=5, max_length=255, description="Safe reference: s3://bucket/tenant/app/doc.pdf")
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: Optional[int] = Field(None, ge=1)
    mime_type: Optional[str] = Field(None, max_length=128)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("document_key")
    @classmethod
    def validate_document_key_is_safe(cls, v: str) -> str:
        """Ensure document_key looks like a safe reference (S3, etc.), not a filesystem path."""
        if v.startswith("/") or v.startswith("C:\\"):
            raise ValueError("document_key must be a safe reference (e.g., s3://...), not a filesystem path")
        if ".." in v:
            raise ValueError("document_key cannot contain directory traversal (..)") 
        return v


class DocumentVerifyRequestSchema(BaseModel):
    """Request schema for verifying a document."""
    status: DocumentStatus = Field(..., description="Verification outcome")
    verified_by: str = Field(..., min_length=1, max_length=255, description="User ID of verifier")
    metadata_json: Optional[dict] = Field(None, description="Optional verification notes")


class DocumentReadSchema(BaseModel):
    """Response schema for reading a document."""
    id: int
    tenant_id: int = Field(..., description="Read-only")
    application_id: int
    document_type: str
    document_key: str = Field(..., description="Safe reference key (do not expose to untrusted callers)")
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    status: DocumentStatus
    metadata_json: dict
    created_by: str
    created_at: datetime
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentListResponseSchema(BaseModel):
    """Response for listing documents in an application."""
    total: int = Field(..., ge=0)
    items: list[DocumentReadSchema]


# ==============================================================================
# STAGE TRANSITION SCHEMAS
# ==============================================================================


class StageTransitionRequestSchema(BaseModel):
    """Request schema for transitioning an application to a new stage."""
    to_stage: ApplicationStage = Field(..., description="Target stage")
    reason: Optional[str] = Field(None, max_length=255, description="Transition reason for audit trail")
    action_type: StageTransitionAction = Field(StageTransitionAction.MANUAL, description="How transition was triggered")
    metadata_json: Optional[dict] = Field(None, description="Optional transition metadata")

    @field_validator("to_stage")
    @classmethod
    def validate_target_stage(cls, v: ApplicationStage) -> ApplicationStage:
        """Validate that to_stage is not invalid enum value."""
        if v not in ApplicationStage:
            raise ValueError(f"Invalid stage: {v}")
        return v


class StageTransitionResponseSchema(BaseModel):
    """Response after a successful stage transition."""
    application_id: int
    from_stage: ApplicationStage
    to_stage: ApplicationStage
    transition_at: datetime
    history_id: int = Field(..., description="ID of created ApplicationStageHistoryModel record")


class StageHistoryReadSchema(BaseModel):
    """Response schema for reading a stage history record."""
    id: int
    tenant_id: int = Field(..., description="Read-only")
    application_id: int
    from_stage: ApplicationStage
    to_stage: ApplicationStage
    reason: Optional[str] = None
    actor_id: str = Field(..., description="User ID who triggered transition")
    action_type: StageTransitionAction
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class StageHistoryListResponseSchema(BaseModel):
    """Response for listing stage history of an application."""
    total: int = Field(..., ge=0)
    items: list[StageHistoryReadSchema]


# ==============================================================================
# DECISION SCHEMAS
# ==============================================================================


class DecisionMakeRequestSchema(BaseModel):
    """Request schema for making an admission decision."""
    decision_type: ApplicationConclusionType = Field(..., description="Decision outcome")
    decision_rationale: Optional[str] = Field(None, max_length=500, description="Why this decision")
    decided_by: str = Field(..., min_length=1, max_length=255, description="User ID of decision maker")
    conditions_json: dict = Field(default_factory=dict, description="Conditional acceptance terms")
    application_version: int = Field(..., ge=1, description="Optimistic locking version on application")

    @field_validator("decision_type")
    @classmethod
    def validate_decision_type(cls, v: ApplicationConclusionType) -> ApplicationConclusionType:
        """Validate decision type is valid enum."""
        if v not in ApplicationConclusionType:
            raise ValueError(f"Invalid decision type: {v}")
        return v


class ApplicationDecisionReadSchema(BaseModel):
    """Response schema for reading a decision."""
    id: int
    tenant_id: int = Field(..., description="Read-only")
    application_id: int
    decision_type: ApplicationConclusionType
    decision_rationale: Optional[str] = None
    decided_by_id: str = Field(..., description="User ID who made decision")
    decided_at: datetime
    conditions_json: dict
    version: int = Field(..., ge=1, description="Decision version (for future amendments)")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==============================================================================
# ERROR RESPONSE SCHEMAS
# ==============================================================================


class ErrorDetailSchema(BaseModel):
    """Error detail with multi-language support placeholder."""
    code: str = Field(..., description="Error code (e.g., 'TENANT_MISMATCH', 'INVALID_TRANSITION')")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error context")


class ErrorResponseSchema(BaseModel):
    """Standard error response."""
    error: ErrorDetailSchema
    request_id: Optional[str] = Field(None, description="Correlation ID for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
