from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.interventions.effectiveness_models import InterventionCohortOutcomeType


class CohortFinalizeRequestSchema(BaseModel):
    playbook_id: int
    cohort_name: str = Field(min_length=1, max_length=255)
    analysis_window_start: date
    analysis_window_end: date


class CohortAnalyzeRequestSchema(BaseModel):
    segment_keys: list[str] = Field(default_factory=list)


class CohortReadSchema(BaseModel):
    id: int
    tenant_id: int
    playbook_id: int
    cohort_name: str
    analysis_window_start: date
    analysis_window_end: date
    student_count: int
    data_completeness_pct: Decimal | None = None
    created_by: str
    created_at: datetime


class CohortOutcomeReadSchema(BaseModel):
    id: int
    tenant_id: int
    cohort_id: int
    outcome_type: InterventionCohortOutcomeType
    segment_name: str | None = None
    outcome_value_treated: Decimal
    outcome_value_control: Decimal
    uplift_pp: Decimal
    uplift_confidence_p5: Decimal | None = None
    uplift_confidence_p95: Decimal | None = None
    measurement_completeness_pct: Decimal | None = None
    measured_at: datetime
    notes: str | None = None


class CohortOutcomeListResponseSchema(BaseModel):
    items: list[CohortOutcomeReadSchema]
    total: int


class CohortAnalyzeResponseSchema(BaseModel):
    cohort_id: int
    status: str
    detail: str
    requested_at: datetime
