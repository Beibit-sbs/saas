"""Document / Decree / Correspondence Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DdcSafetyFlags(BaseModel):
    fake_documents: bool = False
    fake_decrees: bool = False
    fake_signatures: bool = False
    fake_delivery_confirmations: bool = False
    fake_archive_legal_record: bool = False
    official_legal_effect: bool = False
    external_submission_enabled: bool = False
    automatic_rector_decision_enabled: bool = False
    automatic_decree_approval_enabled: bool = False
    automatic_document_signing_enabled: bool = False
    hidden_score_present: bool = False
    human_review_required: bool = True
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)


class DdcBaseResponse(DdcSafetyFlags):
    tenant_id: int
    module: str
    contract_version: str
    runtime_mode: str
    data_source: str


class DdcMetadataRecord(BaseModel):
    id: int
    tenant_id: int
    status: str
    reference_key: str | None = None
    title: str | None = None
    source_module: str | None = None
    source_record_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DdcAuditEventRecord(BaseModel):
    id: int
    tenant_id: int
    status: str
    entity_type: str
    entity_id: int | None = None
    action: str
    actor_user_id: str | None = None
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class DdcEvidenceItemRecord(BaseModel):
    id: int
    tenant_id: int
    status: str
    evidence_type: str
    title: str
    reference_uri: str | None = None
    source_module: str | None = None
    source_record_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class DdcMetadataCollectionResponse(DdcBaseResponse):
    records: list[DdcMetadataRecord] = Field(default_factory=list)


class DdcAuditEventResponse(DdcBaseResponse):
    records: list[DdcAuditEventRecord] = Field(default_factory=list)


class DdcEvidenceItemResponse(DdcBaseResponse):
    records: list[DdcEvidenceItemRecord] = Field(default_factory=list)


class DdcOverviewResponse(DdcBaseResponse):
    target_level: str
    foundation_status: str
    selected_vertical: str
    canonical_modules: list[str] = Field(default_factory=list)
    table_count: int
    route_count: int
    permission_count: int


class DdcReadinessResponse(DdcBaseResponse):
    readiness_status: str
    readiness_score: int
    required_evidence: list[str] = Field(default_factory=list)
    present_evidence: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class DdcDashboardResponse(DdcBaseResponse):
    summary: dict[str, Any] = Field(default_factory=dict)


class DdcDocumentIntakeResponse(DdcMetadataCollectionResponse):
    pass


class DdcDocumentRegistrationResponse(DdcMetadataCollectionResponse):
    pass


class DdcDocumentRoutingResponse(DdcMetadataCollectionResponse):
    pass


class DdcRectorResolutionResponse(DdcMetadataCollectionResponse):
    pass


class DdcDecreeRegistryResponse(DdcMetadataCollectionResponse):
    pass


class DdcDecreeDraftResponse(DdcMetadataCollectionResponse):
    pass


class DdcIncomingCorrespondenceResponse(DdcMetadataCollectionResponse):
    pass


class DdcOutgoingCorrespondenceResponse(DdcMetadataCollectionResponse):
    pass


class DdcTemplateMetadataResponse(DdcMetadataCollectionResponse):
    pass


class DdcCommitteeDecisionBridgeResponse(DdcMetadataCollectionResponse):
    pass


class DdcAssignmentBridgeResponse(DdcMetadataCollectionResponse):
    pass


class DdcExecutionControlResponse(DdcMetadataCollectionResponse):
    pass


class DdcSlaDeadlineResponse(DdcMetadataCollectionResponse):
    pass


class DdcAttachmentMetadataResponse(DdcMetadataCollectionResponse):
    pass


class DdcArchiveReadinessResponse(DdcMetadataCollectionResponse):
    pass


class DdcRetentionMetadataResponse(DdcMetadataCollectionResponse):
    pass


class DdcSignatureReadinessResponse(DdcMetadataCollectionResponse):
    pass


class DdcDeliveryReadinessResponse(DdcMetadataCollectionResponse):
    pass


class DdcBridgeResponse(DdcMetadataCollectionResponse):
    pass


class DdcLimitationsResponse(DdcMetadataCollectionResponse):
    pass


class DdcMetadataContractResponse(DdcBaseResponse):
    route_count: int
    table_count: int
    permission_count: int
    route_paths: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    canonical_modules: list[str] = Field(default_factory=list)


class DdcMetadataCreateRequest(BaseModel):
    reference_key: str = Field(..., min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    source_module: str | None = Field(default=None, max_length=128)
    source_record_id: int | None = None
    status: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class DdcEvidenceItemCreateRequest(BaseModel):
    evidence_type: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=255)
    reference_uri: str | None = Field(default=None, max_length=255)
    source_module: str | None = Field(default=None, max_length=128)
    source_record_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class DdcAuditEventCreateRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=128)
    entity_id: int | None = None
    action: str = Field(..., min_length=1, max_length=128)
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
