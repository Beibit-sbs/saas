from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=128)
    name: str = Field(min_length=2, max_length=255)


class AcademicRiskThresholdsRead(BaseModel):
    risk_grade_threshold: int
    severe_risk_grade_threshold: int
    tenant_id: int


class AcademicRiskThresholdsPutRequest(BaseModel):
    risk_grade_threshold: int = Field(ge=1, le=100)
    severe_risk_grade_threshold: int = Field(ge=1, le=100)


class TenantSettingsPatchRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class TenantMapRequest(BaseModel):
    values: dict[str, int] = Field(default_factory=dict)


class TenantSuspendRequest(BaseModel):
    suspended: bool = True


class TenantPlatformRead(BaseModel):
    tenant_id: int
    slug: str
    name: str
    status: str
    suspended: bool
    settings: dict[str, Any]
    quotas: dict[str, int]
    limits: dict[str, int]
    updated_at: str


class FeatureFlagSetRequest(BaseModel):
    enabled: bool
    rollout_percentage: int = Field(default=100, ge=0, le=100)


class FeatureFlagRead(BaseModel):
    scope: Literal["platform", "tenant"]
    tenant_id: int | None = None
    module: str
    key: str
    enabled: bool
    rollout_percentage: int = 100
    updated_at: str


class AnalyticsEntitlementRolloutStateRead(BaseModel):
    tenant_id: int
    module: Literal["analytics"] = "analytics"
    marker_key: Literal["developer_read_required"] = "developer_read_required"
    marker_enabled: bool | None = None
    feature_key: Literal["developer_read"] = "developer_read"
    feature_enabled: bool | None = None
    effective_state: Literal[
        "legacy_compatible_allow",
        "strict_required_missing",
        "explicitly_enabled",
        "explicitly_disabled",
    ]
    is_entitled: bool


class AnalyticsEntitlementRolloutSummaryListRead(BaseModel):
    limit: int
    count: int
    items: list[AnalyticsEntitlementRolloutStateRead]


class PlanCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    price_cents: int = Field(ge=0, default=0)
    features: dict[str, bool] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)


class PlanRead(BaseModel):
    id: int
    code: str
    name: str
    price_cents: int
    features: dict[str, bool]
    limits: dict[str, int]
    active: bool
    created_at: str


class SubscriptionAssignRequest(BaseModel):
    plan_code: str = Field(min_length=2, max_length=64)


class SubscriptionRead(BaseModel):
    tenant_id: int
    plan_id: int
    plan_code: str
    status: str
    started_at: str


class UsageCounterIncrementRequest(BaseModel):
    value: int = Field(default=1, ge=1)


class UsageCounterRead(BaseModel):
    tenant_id: int
    metric: str
    period_key: str
    value: int
    updated_at: str


class JobEnqueueRequest(BaseModel):
    tenant_id: int = Field(gt=0)
    job_type: str = Field(min_length=2, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=20)


class JobRead(BaseModel):
    id: int
    tenant_id: int
    job_type: str
    status: str
    retry_count: int
    max_retries: int
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    updated_at: str


class JobRunRequest(BaseModel):
    succeed: bool = True
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class NotificationRequest(BaseModel):
    tenant_id: int = Field(gt=0)
    channel: Literal["email", "in_app", "webhook"]
    target: str = Field(min_length=3, max_length=512)
    subject: str | None = Field(default=None, max_length=255)
    payload: dict[str, Any] = Field(default_factory=dict)


class NotificationRead(BaseModel):
    id: int
    tenant_id: int
    channel: str
    target: str
    subject: str | None
    payload: dict[str, Any]
    status: str
    created_at: str


class HealthRead(BaseModel):
    status: str
    service: str
    at: datetime
