from pydantic import BaseModel, Field


class PlanQuotaPayload(BaseModel):
    quotas: dict[str, int] = Field(default_factory=dict)


class QuotaResponse(BaseModel):
    id: int
    plan_id: int
    key: str
    limit_value: int


class QuotaListResponse(BaseModel):
    quotas: list[QuotaResponse]


class TenantQuotaCheckResponse(BaseModel):
    tenant_id: int
    quota_key: str
    limit_value: int
    current_value: int
    within_limit: bool
    soft_warning: bool
    message: str
