from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    slug: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    status: str = Field(min_length=1, max_length=64, default="active")
    plan_id: int | None = Field(default=None, ge=1)


class TenantCreatePayload(TenantBase):
    pass


class TenantUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=64)
    plan_id: int | None = Field(default=None, ge=1)


class TenantResponse(BaseModel):
    id: int
    slug: str
    name: str
    status: str
    plan_id: int
    created_at: str
    updated_at: str


class TenantListResponse(BaseModel):
    tenants: list[TenantResponse]


class TenantItemResponse(BaseModel):
    tenant: TenantResponse


class TenantDeleteResponse(BaseModel):
    deleted: bool
    tenant: TenantResponse


class LoginDirectoryTenant(BaseModel):
    """Minimal tenant info for login UI (unauthenticated access)."""
    tenant_id: int = Field(description="Tenant ID for login form")
    slug: str = Field(description="URL-friendly tenant identifier")
    name: str = Field(description="Display name for UI dropdown")


class LoginDirectoryResponse(BaseModel):
    """Public login directory: list of active tenants available for tenant-bound users."""
    tenants: list[LoginDirectoryTenant]
