from pydantic import BaseModel


class UsageEventResponse(BaseModel):
    id: int
    tenant_id: int
    metric: str
    value: int
    created_at: str


class UsageEventListResponse(BaseModel):
    events: list[UsageEventResponse]
