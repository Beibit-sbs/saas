from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InstitutionCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    country: str = Field(min_length=1, max_length=128)
    type: str = "university"
    metadata: dict[str, Any] = {}


class InstitutionReadSchema(BaseModel):
    id: int
    name: str
    code: str
    country: str
    type: str
    status: str
    metadata_json: dict[str, Any]
    created_at: str
    updated_at: str


class FederationMemberReadSchema(BaseModel):
    id: int
    institution_id: int
    tenant_id: int
    role: str
    created_at: str


class LinkTenantSchema(BaseModel):
    tenant_id: int
    role: str = "institution_admin"


class InstitutionKpiCardSchema(BaseModel):
    metric_key: str
    title: str
    value: int


class InstitutionOverviewSchema(BaseModel):
    institution: InstitutionReadSchema
    tenant_count: int
    students_total: int
    enrollments_total: int
    automation_health: dict[str, Any]
    kpi_cards: list[InstitutionKpiCardSchema]
