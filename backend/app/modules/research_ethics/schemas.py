"""Phase VII-VII1: Research ethics schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

# State machine: allowed status transitions for ethics reviews
RE_ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["under_review", "rejected"],
    "under_review": ["approved", "rejected", "revision_requested"],
    "revision_requested": ["under_review", "rejected"],
    "approved": [],
    "rejected": [],
}


class EthicsReviewCreatePayload(BaseModel):
    review_code: str = Field(min_length=1, max_length=64)
    project_title: str = Field(min_length=1, max_length=256)
    principal_investigator_id: str = Field(min_length=1, max_length=64)
    review_type: str = Field(default="irb", min_length=1, max_length=64)
    status: str = Field(default="pending", min_length=1, max_length=32)
    submission_date: str | None = Field(default=None, max_length=64)
    decision_date: str | None = Field(default=None, max_length=64)
    risk_level: str = Field(default="minimal", min_length=1, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    integration_source: str | None = Field(default=None, max_length=64)
    committee_name: str | None = Field(default=None, max_length=128)


class EthicsReviewResponse(EthicsReviewCreatePayload):
    id: int
    tenant_id: int


class EthicsReviewItemResponse(BaseModel):
    record: EthicsReviewResponse


class EthicsReviewListResponse(BaseModel):
    records: list[EthicsReviewResponse]


class EthicsReviewStatusUpdateSchema(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    notes: str | None = Field(default=None, max_length=500)


class ResearchEthicsBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_reviews: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
    high_risk_reviews: int
    compliance_status: str
