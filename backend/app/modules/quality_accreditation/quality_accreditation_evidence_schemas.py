"""Schemas for Quality / Accreditation evidence runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AccreditationEvidenceItem(BaseModel):
    evidence_id: str
    evidence_name: str
    evidence_category: str
    accreditation_standard: str
    accreditation_section: str
    owner_unit: str
    evidence_status: str
    completeness_score: int = 0
    last_updated: datetime
    risk_level: str = "UNKNOWN"
    read_only: bool = True
    aggregator_only: bool = True


class EvidenceCategorySummary(BaseModel):
    evidence_category: str
    evidence_count: int = 0
    average_completeness_score: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class EvidenceReadinessSummary(BaseModel):
    readiness_band: str
    evidence_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class EvidenceCoverageSummary(BaseModel):
    coverage_scope: str
    evidence_count: int = 0
    covered_count: int = 0
    coverage_percent: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class EvidenceRiskSummary(BaseModel):
    risk_level: str
    evidence_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class AccreditationEvidenceRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "ACCREDITATION_EVIDENCE_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    evidence_inventory: list[AccreditationEvidenceItem] = Field(default_factory=list)
    evidence_categories: list[EvidenceCategorySummary] = Field(default_factory=list)
    evidence_readiness: list[EvidenceReadinessSummary] = Field(default_factory=list)
    evidence_coverage: list[EvidenceCoverageSummary] = Field(default_factory=list)
    evidence_risk: list[EvidenceRiskSummary] = Field(default_factory=list)
