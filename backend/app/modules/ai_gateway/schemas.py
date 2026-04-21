from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AIModelUpsertPayload(BaseModel):
    provider: Literal["openai", "gemini", "anthropic", "custom"]
    provider_model_id: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10_000)
    metadata: dict[str, Any] | None = None


class AIModelEnabledPayload(BaseModel):
    enabled: bool


class AIChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=16_000)


class AIChatRequestPayload(BaseModel):
    model: str = Field(min_length=1, max_length=120)
    messages: list[AIChatMessage] = Field(min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=16_384)
    task_type: str | None = Field(default=None, min_length=1, max_length=64)


class AIRoutingRuleSchema(BaseModel):
    task_type: str = Field(min_length=1, max_length=64)
    target_model: str = Field(min_length=1, max_length=120)
    priority: int = Field(default=100, ge=0, le=10_000)


class AIRoutingPolicyPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    strategy: Literal["priority"] = "priority"
    enabled: bool = True
    rules: list[AIRoutingRuleSchema] = Field(default_factory=list, max_length=100)
    fallback_chain: list[str] = Field(default_factory=list, max_length=20)


class AIRoutingPolicyReadSchema(AIRoutingPolicyPayload):
    id: int
    tenant_id: int
    created_at: str
    updated_at: str


class AIUsageCostModelSummarySchema(BaseModel):
    model_key: str
    provider: str
    requests_total: int
    success_count: int
    degraded_count: int
    failed_count: int
    total_tokens: int
    avg_latency_ms: float
    estimated_cost_usd: float


class AIUsageCostSummarySchema(BaseModel):
    tenant_id: int
    requests_total: int
    success_count: int
    degraded_count: int
    failed_count: int
    total_tokens: int
    avg_latency_ms: float
    estimated_cost_usd: float
    budget_limit_usd: float
    budget_utilization_pct: float
    budget_alert: bool
    budget_hard_cap: bool
    anomaly_detected: bool
    anomaly_score_z: float
    anomaly_reason: str | None = None
    models: list[AIUsageCostModelSummarySchema]


class AIUsageCostByUserSchema(BaseModel):
    tenant_id: int
    actor: str
    requests_total: int
    success_count: int
    degraded_count: int
    failed_count: int
    total_tokens: int
    avg_latency_ms: float
    estimated_cost_usd: float


class AIUsageCostByDepartmentSchema(BaseModel):
    tenant_id: int
    department: str
    requests_total: int
    success_count: int
    degraded_count: int
    failed_count: int
    total_tokens: int
    avg_latency_ms: float
    estimated_cost_usd: float


class AIUsageCostTrendPointSchema(BaseModel):
    tenant_id: int
    date: str
    requests_total: int
    total_tokens: int
    estimated_cost_usd: float


class AIUsageCostDailyAggregateSchema(BaseModel):
    tenant_id: int
    date: str
    provider: str
    model_key: str
    requests_total: int
    total_tokens: int
    estimated_cost_usd: float
    updated_at: str


class AIUsageCostProjectionSchema(BaseModel):
    tenant_id: int
    period: Literal["daily"] = "daily"
    elapsed_requests: int
    current_cost_usd: float
    projected_cost_usd: float
    projection_basis: str


class AIUsageCostAnomalySchema(BaseModel):
    tenant_id: int
    timestamp: str
    model_key: str
    provider: str
    total_tokens: int
    estimated_cost_usd: float
    anomaly_score_z: float
    anomaly_reason: str


class AIUsageTokenPricePayload(BaseModel):
    input_price_per_1k: float = Field(ge=0.0, le=1000.0)
    output_price_per_1k: float = Field(ge=0.0, le=1000.0)


class AIUsageTokenPriceSchema(AIUsageTokenPricePayload):
    tenant_id: int
    provider: Literal["openai", "gemini", "anthropic", "custom"]
    model_key: str
    updated_at: str


class AISLOPolicyPayload(BaseModel):
    p95_latency_ms: int = Field(ge=1, le=300_000)
    max_error_rate_pct: float = Field(ge=0.0, le=100.0)


class AISLOPolicySchema(AISLOPolicyPayload):
    tenant_id: int
    model_key: str
    updated_at: str


class AISLOComplianceSchema(BaseModel):
    tenant_id: int
    model_key: str
    requests_total: int
    p95_latency_ms_observed: int
    error_rate_pct_observed: float
    p95_latency_ms_target: int
    max_error_rate_pct_target: float
    latency_compliant: bool
    error_rate_compliant: bool
    compliant: bool


class AISLOViolationSchema(BaseModel):
    tenant_id: int
    model_key: str
    requests_total: int
    p95_latency_ms_observed: int
    error_rate_pct_observed: float
    p95_latency_ms_target: int
    max_error_rate_pct_target: float
    latency_compliant: bool
    error_rate_compliant: bool
    compliant: bool
    violation_types: list[Literal["latency", "error_rate"]]


class AIUsageBudgetPayload(BaseModel):
    budget_limit_usd: float = Field(ge=0.0, le=1_000_000.0)
    alert_threshold_pct: int = Field(default=80, ge=1, le=100)
    hard_cap: bool = False


class AIUsageBudgetReadSchema(AIUsageBudgetPayload):
    tenant_id: int
    updated_at: str


class AIUsageBudgetScopedPayload(AIUsageBudgetPayload):
    scope: Literal["tenant", "department", "user"] = "tenant"
    scope_id: str | None = Field(default=None, max_length=200)


class AIUsageBudgetScopedReadSchema(AIUsageBudgetScopedPayload):
    tenant_id: int
    updated_at: str


class AIUsageBudgetStatusSchema(BaseModel):
    tenant_id: int
    scope: Literal["tenant", "department", "user"]
    scope_id: str | None = None
    budget_limit_usd: float
    current_cost_usd: float
    utilization_pct: float
    alert_threshold_pct: int
    budget_alert: bool
    hard_cap: bool
    hard_cap_exceeded: bool
    updated_at: str


class AISafetyPolicyPayload(BaseModel):
    injection_detection: bool = True
    content_moderation: bool = True
    pii_detection: bool = True
    audit_only: bool = False
    blocked_patterns: list[str] = Field(default_factory=list, max_length=200)


class AISafetyPolicySchema(AISafetyPolicyPayload):
    tenant_id: int
