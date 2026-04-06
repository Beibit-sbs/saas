from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.interventions.models import (
    OutcomeTrackingStatus,
    RiskMetric,
    RiskSignalType,
    RiskThresholdCategory,
    RiskThresholdComparison,
    InterventionActionType,
    InterventionAssigneeType,
    InterventionCaseSeverity,
    InterventionCaseStatus,
    InterventionCaseType,
)


class InterventionCaseCreateSchema(BaseModel):
    case_type: InterventionCaseType = InterventionCaseType.ACADEMIC_RISK
    student_profile_id: int | None = Field(default=None, gt=0)
    severity: InterventionCaseSeverity = InterventionCaseSeverity.MEDIUM
    title: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    due_at: datetime | None = None
    assignee_type: InterventionAssigneeType | None = None
    assignee_ref: str | None = Field(default=None, min_length=2, max_length=255)
    risk_snapshot_json: dict = Field(default_factory=dict)
    metadata_json: dict = Field(default_factory=dict)


class InterventionCaseAssignSchema(BaseModel):
    expected_version: int = Field(ge=1)
    assignee_type: InterventionAssigneeType
    assignee_ref: str = Field(min_length=2, max_length=255)
    due_at: datetime | None = None


class InterventionCaseTakeSchema(BaseModel):
    expected_version: int = Field(ge=1)


class InterventionCaseStatusUpdateSchema(BaseModel):
    expected_version: int = Field(ge=1)
    status: InterventionCaseStatus
    reason: str | None = Field(default=None, max_length=2000)


class InterventionActionCreateSchema(BaseModel):
    expected_version: int = Field(ge=1)
    action_type: InterventionActionType
    description: str = Field(min_length=3, max_length=4000)
    outcome_note: str | None = Field(default=None, max_length=4000)
    mark_case_in_progress: bool = False
    mark_case_resolved: bool = False
    metadata_json: dict = Field(default_factory=dict)


class InterventionCaseReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    case_type: InterventionCaseType
    student_profile_id: int | None
    severity: InterventionCaseSeverity
    status: InterventionCaseStatus
    title: str
    description: str | None
    risk_snapshot_json: dict
    assignee_type: InterventionAssigneeType
    assignee_ref: str
    due_at: datetime
    opened_at: datetime
    resolved_at: datetime | None
    metadata_json: dict
    version: int
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class InterventionActionReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    case_id: int
    action_type: InterventionActionType
    description: str
    outcome_note: str | None
    performed_by: str
    performed_at: datetime
    metadata_json: dict


class InterventionCaseListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InterventionCaseReadSchema]


class InterventionActionListResponseSchema(BaseModel):
    total: int
    items: list[InterventionActionReadSchema]


class InterventionCaseActionResultSchema(BaseModel):
    case: InterventionCaseReadSchema
    action: InterventionActionReadSchema


class RiskThresholdCreateSchema(BaseModel):
    risk_category: RiskThresholdCategory
    rule_name: str = Field(min_length=3, max_length=128)
    metric: RiskMetric
    threshold_value: float = Field(ge=0)
    comparison: RiskThresholdComparison
    severity_level: InterventionCaseSeverity = InterventionCaseSeverity.MEDIUM
    signal_type: RiskSignalType
    enabled: bool = True
    auto_create_case: bool = True
    window_days: int = Field(default=30, ge=1, le=365)
    escalate_to_refs_json: list[str] = Field(default_factory=list)


class RiskThresholdUpdateSchema(BaseModel):
    enabled: bool | None = None
    threshold_value: float | None = Field(default=None, ge=0)
    comparison: RiskThresholdComparison | None = None
    severity_level: InterventionCaseSeverity | None = None
    auto_create_case: bool | None = None
    window_days: int | None = Field(default=None, ge=1, le=365)
    escalate_to_refs_json: list[str] | None = None


class RiskThresholdReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    risk_category: RiskThresholdCategory
    rule_name: str
    metric: RiskMetric
    threshold_value: float
    comparison: RiskThresholdComparison
    severity_level: InterventionCaseSeverity
    signal_type: RiskSignalType
    enabled: bool
    auto_create_case: bool
    window_days: int
    escalate_to_refs_json: list
    created_at: datetime
    updated_at: datetime


class RiskThresholdListResponseSchema(BaseModel):
    total: int
    items: list[RiskThresholdReadSchema]


class RiskSignalReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    threshold_id: int
    signal_type: RiskSignalType
    detected_at: datetime
    detected_on: date
    current_value: float
    threshold_value: float
    severity: InterventionCaseSeverity
    signal_data_json: dict
    associated_case_id: int | None


class RiskSignalListResponseSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RiskSignalReadSchema]


class OutcomeTrackingUpsertSchema(BaseModel):
    baseline_risk_score: float
    current_risk_score: float
    outcome: OutcomeTrackingStatus
    improvement_date: date | None = None
    measurement_notes: str | None = Field(default=None, max_length=2000)
    outcome_notes: str | None = Field(default=None, max_length=2000)


class OutcomeTrackingReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    case_id: int
    baseline_risk_score: float
    current_risk_score: float
    outcome: OutcomeTrackingStatus
    improvement_date: date | None
    measurement_notes: str | None
    outcome_notes: str | None
    created_at: datetime
    updated_at: datetime


class RiskDetectionRunResultSchema(BaseModel):
    tenant_id: int
    thresholds_evaluated: int
    signals_created: int
    cases_created: int


class InterventionRiskKpiSummarySchema(BaseModel):
    tenant_id: int
    open_cases_total: int
    signals_last_24h: int
    auto_created_cases_last_24h: int
    severity_breakdown: dict[str, int]
