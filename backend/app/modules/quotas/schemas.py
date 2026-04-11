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


class PlanQuotaConsistencyIssueSchema(BaseModel):
    issue_type: str
    plan_id: int | None = None
    plan_code: str | None = None
    quota_key: str | None = None
    detail: str


class PlanQuotaConsistencyReportSchema(BaseModel):
    total_plan_count: int = Field(..., ge=0)
    configured_plan_quota_count: int = Field(..., ge=0)
    issue_count: int = Field(..., ge=0)
    issues: list[PlanQuotaConsistencyIssueSchema] = Field(default_factory=list)
