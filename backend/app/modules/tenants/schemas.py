from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    slug: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    status: str = Field(min_length=1, max_length=64, default="active")


class TenantCreatePayload(TenantBase):
    pass


class TenantUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=64)


class TenantResponse(BaseModel):
    id: int
    slug: str
    name: str
    status: str
    created_at: str
    updated_at: str


class TenantListResponse(BaseModel):
    tenants: list[TenantResponse]


class TenantItemResponse(BaseModel):
    tenant: TenantResponse


class TenantDeleteResponse(BaseModel):
    deleted: bool
    tenant: TenantResponse
