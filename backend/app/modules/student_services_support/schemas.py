"""Student Services / Welfare / Support Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RequestType = Literal[
    "general_support",
    "welfare",
    "hardship",
    "accessibility",
    "complaint",
    "advising_referral",
    "financial_aid_referral",
]
RequestStatus = Literal[
    "draft",
    "submitted",
    "triaged",
    "assigned",
    "in_progress",
    "waiting_student_response",
    "escalated",
    "resolved",
    "closed",
    "archived",
]
CaseType = Literal["support_case", "welfare_case", "hardship_case", "accommodation_case", "complaint_case"]
CaseStatus = Literal[
    "open",
    "under_review",
    "action_plan_draft",
    "action_plan_review",
    "follow_up",
    "escalated",
    "resolved",
    "closed",
    "archived",
]
SupportPriority = Literal["low", "medium", "high", "critical"]
ReadinessStatus = Literal[
    "insufficient_evidence",
    "ready_for_human_review",
    "needs_follow_up",
    "blocked_missing_required_evidence",
]
ComplaintStatus = Literal["submitted", "triaged", "routed", "under_review", "response_prepared", "closed", "archived"]
EscalationStatus = Literal["pending", "acknowledged", "under_review", "resolved", "closed"]


class SssBaseResponse(BaseModel):
    tenant_id: int
    module: str = "student_services_support"
    contract_version: str = "A-042.2.RUNTIME"
    runtime_mode: str = "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY"
    fake_metrics: bool = False
    provider_live_enabled: bool = False
    autonomous_decision_enabled: bool = False
    hidden_score_present: bool = False
    human_review_required: bool = True


class ServiceRequestCreateRequest(BaseModel):
    request_type: RequestType
    student_id: str = Field(min_length=1, max_length=128)
    support_priority: SupportPriority = "medium"
    subject: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=3000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServiceRequestAssignRequest(BaseModel):
    assigned_to_user_id: str = Field(min_length=1, max_length=255)


class ServiceRequestStatusUpdateRequest(BaseModel):
    status: RequestStatus
    reason: str | None = Field(default=None, max_length=500)


class SupportCaseCreateRequest(BaseModel):
    case_type: CaseType
    request_id: int | None = None
    title: str | None = Field(default=None, max_length=255)
    assigned_to_user_id: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupportCaseNoteCreateRequest(BaseModel):
    note: str = Field(min_length=1, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupportEvidenceCreateRequest(BaseModel):
    evidence_type: str = Field(min_length=1, max_length=128)
    evidence_ref: str | None = Field(default=None, max_length=255)
    source_available: bool = False
    limitations: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HardshipSupportCreateRequest(BaseModel):
    request_id: int | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DisabilityAccommodationCreateRequest(BaseModel):
    request_id: int | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StudentComplaintCreateRequest(BaseModel):
    request_id: int | None = None
    complaint_summary: str = Field(min_length=1, max_length=4000)
    route_to: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupportEscalationCreateRequest(BaseModel):
    case_id: int
    reason: str = Field(min_length=1, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServiceRequestRecord(BaseModel):
    id: int
    tenant_id: int
    request_type: str
    status: str
    support_priority: str
    student_id: str
    assigned_to_user_id: str | None = None
    subject: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SupportCaseRecord(BaseModel):
    id: int
    tenant_id: int
    case_type: str
    status: str
    request_id: int | None = None
    assigned_to_user_id: str | None = None
    title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SupportCaseNoteRecord(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    note: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class SupportEvidenceRecord(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    evidence_type: str
    evidence_ref: str | None = None
    source_available: bool = False
    limitations: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ComplaintRecord(BaseModel):
    id: int
    tenant_id: int
    status: ComplaintStatus
    request_id: int | None = None
    routed_to: str | None = None
    complaint_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EscalationRecord(BaseModel):
    id: int
    tenant_id: int
    case_id: int
    escalation_status: EscalationStatus
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReadinessRecord(BaseModel):
    id: int
    tenant_id: int
    request_id: int | None = None
    status: str
    readiness_status: ReadinessStatus
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_next_step: str | None = None


class ServiceRequestListResponse(SssBaseResponse):
    items: list[ServiceRequestRecord] = Field(default_factory=list)


class ServiceRequestItemResponse(SssBaseResponse):
    item: ServiceRequestRecord


class SupportCaseListResponse(SssBaseResponse):
    items: list[SupportCaseRecord] = Field(default_factory=list)


class SupportCaseItemResponse(SssBaseResponse):
    item: SupportCaseRecord


class SupportCaseNoteItemResponse(SssBaseResponse):
    item: SupportCaseNoteRecord


class SupportEvidenceItemResponse(SssBaseResponse):
    item: SupportEvidenceRecord


class HardshipReadinessItemResponse(SssBaseResponse):
    item: ReadinessRecord


class AccommodationReadinessItemResponse(SssBaseResponse):
    item: ReadinessRecord


class ComplaintItemResponse(SssBaseResponse):
    item: ComplaintRecord


class EscalationItemResponse(SssBaseResponse):
    item: EscalationRecord


class DashboardSummaryResponse(SssBaseResponse):
    data_source: str = "computed_from_student_services_support_records"
    incomplete_data: bool
    open_requests: int
    open_support_cases: int
    escalated_cases: int
    hardship_readiness_counts: dict[str, int] = Field(default_factory=dict)
    accommodation_readiness_counts: dict[str, int] = Field(default_factory=dict)
    complaint_counts: dict[str, int] = Field(default_factory=dict)
