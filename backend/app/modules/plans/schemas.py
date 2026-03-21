from pydantic import BaseModel, Field


class PlanCreatePayload(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    active: bool = True


class PlanUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    active: bool | None = None


class PlanResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str
    active: bool


class PlanListResponse(BaseModel):
    plans: list[PlanResponse]


class PlanItemResponse(BaseModel):
    plan: PlanResponse
