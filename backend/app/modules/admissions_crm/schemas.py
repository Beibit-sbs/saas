"""Admissions CRM Batch 1 request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


LeadStatus = Literal["lead_created", "lead_qualified", "applicant_created", "archived"]
ApplicationStatus = Literal["application_started", "application_submitted", "archived"]


class AcrmBaseResponse(BaseModel):
    tenant_id: int
    module: str = "admissions_crm"
    contract_version: str = "A-045.2.RUNTIME.BATCH1"
    runtime_mode: str = "HUMAN_REVIEW_DECISION_SUPPORT_ONLY"
    fake_metrics: bool = False
    provider_live_enabled: bool = False
    autonomous_decision_enabled: bool = False
    hidden_score_present: bool = False
    human_review_required: bool = True


class LeadCreateRequest(BaseModel):
    lead_ref: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    source_channel: str = Field(default="direct", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadQualifyRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class LeadConvertRequest(BaseModel):
    applicant_ref: str = Field(min_length=1, max_length=64)


class ApplicantCreateRequest(BaseModel):
    lead_id: int
    applicant_ref: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApplicationCreateRequest(BaseModel):
    applicant_id: int
    application_ref: str = Field(min_length=1, max_length=64)
    program_code: str = Field(min_length=1, max_length=64)
    intake_term: str = Field(min_length=1, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApplicationSubmitRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class LeadRecord(BaseModel):
    id: int
    tenant_id: int
    lead_ref: str
    status: str
    full_name: str
    email: str
    phone: str | None = None
    source_channel: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApplicantRecord(BaseModel):
    id: int
    tenant_id: int
    lead_id: int
    applicant_ref: str
    status: str
    full_name: str
    email: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApplicationRecord(BaseModel):
    id: int
    tenant_id: int
    applicant_id: int
    application_ref: str
    status: str
    program_code: str
    intake_term: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowEventRecord(BaseModel):
    id: int
    tenant_id: int
    entity_type: str
    entity_id: int
    event_type: str
    from_status: str | None = None
    to_status: str | None = None
    created_at: datetime | None = None


class LeadItemResponse(AcrmBaseResponse):
    item: LeadRecord


class LeadListResponse(AcrmBaseResponse):
    items: list[LeadRecord] = Field(default_factory=list)


class ApplicantItemResponse(AcrmBaseResponse):
    item: ApplicantRecord


class ApplicantListResponse(AcrmBaseResponse):
    items: list[ApplicantRecord] = Field(default_factory=list)


class ApplicationItemResponse(AcrmBaseResponse):
    item: ApplicationRecord


class ApplicationListResponse(AcrmBaseResponse):
    items: list[ApplicationRecord] = Field(default_factory=list)
