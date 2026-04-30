from __future__ import annotations

from pydantic import BaseModel, Field


class BillingSubscriptionReadSchema(BaseModel):
    tenant_id: int
    plan_id: int
    plan_code: str
    status: str
    started_at: str
    trial_ends_at: str | None = None
    current_period_start: str
    current_period_end: str
    next_plan_id: int | None = None
    next_plan_code: str | None = None
    updated_at: str


class BillingStateReadSchema(BaseModel):
    tenant_id: int
    plan_code: str
    plan_id: int
    next_plan_code: str | None = None
    subscription_status: str
    billing_state: str
    period_start: str | None = None
    period_end: str | None = None
    limits: dict[str, int]
    usage: dict[str, int]
    subscription: BillingSubscriptionReadSchema


class BillingTransitionRequestSchema(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class BillingPlanChangeRequestSchema(BaseModel):
    plan_code: str = Field(min_length=1, max_length=64)
    effective: str = Field(default="auto", min_length=1, max_length=32)


class BillingPlanChangeResponseSchema(BaseModel):
    subscription: BillingSubscriptionReadSchema
    effective: str
    old_plan: str
    new_plan: str


class BillingPlanCreateRequestSchema(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    price_cents: int = Field(ge=0, default=0)
    features: dict[str, bool] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)


class BillingPlanUpdateRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    active: bool | None = None


class BillingPlanReadSchema(BaseModel):
    id: int
    code: str
    name: str
    price_cents: int
    features: dict[str, bool]
    limits: dict[str, int]
    active: bool
    created_at: str


class BillingPlanMutationReadSchema(BillingPlanReadSchema):
    plan: BillingPlanReadSchema
    idempotent_replay: bool


class BillingSubscriptionAssignRequestSchema(BaseModel):
    plan_code: str = Field(min_length=2, max_length=64)


class BillingSubscriptionMutationReadSchema(BillingSubscriptionReadSchema):
    subscription: BillingSubscriptionReadSchema
    idempotent_replay: bool


class BillingUsageIncrementRequestSchema(BaseModel):
    value: int = Field(default=1, ge=1)


class BillingUsageReadSchema(BaseModel):
    tenant_id: int
    usage: dict[str, int]


class BillingUsageCounterReadSchema(BaseModel):
    tenant_id: int
    metric: str
    period_key: str
    value: int
    updated_at: str


class BillingDunningPolicySchema(BaseModel):
    grace_period_days: int = Field(default=7, ge=1, le=365)
    overdue_period_days: int = Field(default=30, ge=1, le=365)
    suspension_period_days: int = Field(default=30, ge=1, le=365)
    auto_cancel_after_days: int = Field(default=90, ge=1, le=730)
    reminder_schedule: list[int] = Field(default_factory=lambda: [1, 3, 7, 14, 30])
    require_approval_for_reactivation: bool = True


class BillingCollectionEventReadSchema(BaseModel):
    event_type: str
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: str


class BillingDelinquencyRecordReadSchema(BaseModel):
    id: int
    tenant_id: int
    invoice_id: str
    status: str
    opened_at: str
    last_reminder_at: str | None = None
    reminder_count: int = 0
    escalated_at: str | None = None
    resolved_at: str | None = None
    resolution: str | None = None
    notes: str | None = None
    amount_cents: int = 0
    events: list[BillingCollectionEventReadSchema] = Field(default_factory=list)


class BillingDelinquencyListResponseSchema(BaseModel):
    items: list[BillingDelinquencyRecordReadSchema]
    total: int


class BillingDelinquencyEscalateRequestSchema(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class BillingDelinquencyResolveRequestSchema(BaseModel):
    resolution: str = Field(min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)


class BillingDelinquencyReminderRequestSchema(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class BillingDelinquencyDashboardSchema(BaseModel):
    total: int
    open_total: int
    total_overdue_cents: int
    by_status: dict[str, int]
