"""Phase VI-VI3: Campus SLA schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CampusSlaRecordCreatePayload(BaseModel):
    service_type: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    target_sla_minutes: int = Field(ge=1)
    actual_minutes: int | None = Field(default=None, ge=0)
    status: str = Field(default="open", min_length=1, max_length=32)
    reported_at: str | None = Field(default=None, max_length=64)
    resolved_at: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    integration_source: str | None = Field(default=None, max_length=64)


class CampusSlaRecordResponse(CampusSlaRecordCreatePayload):
    id: int
    tenant_id: int
    breached: bool = False


class CampusSlaRecordItemResponse(BaseModel):
    record: CampusSlaRecordResponse


class CampusSlaRecordListResponse(BaseModel):
    records: list[CampusSlaRecordResponse]


class CampusSlaBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_records: int
    open_records: int
    resolved_records: int
    breached_records: int
    breach_rate: float
    compliance_level: str
