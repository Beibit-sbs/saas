"""Schemas for Quality / Accreditation runtime shell (A-050.5-E1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class QualityAccreditationRuntimeSection(BaseModel):
    owner_module: str
    records: int = 0
    read_only: bool = True
    aggregator_only: bool = True
    source_modules: list[str] = Field(default_factory=list)


class QualityAccreditationRuntimeSafety(BaseModel):
    read_only: bool = True
    aggregator_only: bool = True
    human_review_required: bool = True
    provider_integration_enabled: bool = False
    official_accreditation_approval_enabled: bool = False
    official_ministry_submission_enabled: bool = False
    official_ranking_claim_enabled: bool = False
    hidden_score_present: bool = False
    limitations: list[str] = Field(default_factory=list)


class QualityAccreditationRuntimeShellResponse(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_shell: str = "QUALITY_ACCREDITATION_RUNTIME_SHELL"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    overview: QualityAccreditationRuntimeSection
    readiness: QualityAccreditationRuntimeSection
    evidence: QualityAccreditationRuntimeSection
    risk: QualityAccreditationRuntimeSection
    dashboard: QualityAccreditationRuntimeSection
    safety: QualityAccreditationRuntimeSafety
