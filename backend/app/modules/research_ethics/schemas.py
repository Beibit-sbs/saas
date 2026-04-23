"""Phase VII-VII1: Research ethics schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


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


class EthicsReviewResponse(EthicsReviewCreatePayload):
    id: int
    tenant_id: int


class EthicsReviewItemResponse(BaseModel):
    record: EthicsReviewResponse


class EthicsReviewListResponse(BaseModel):
    records: list[EthicsReviewResponse]


class ResearchEthicsBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_reviews: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
    high_risk_reviews: int
    compliance_status: str
