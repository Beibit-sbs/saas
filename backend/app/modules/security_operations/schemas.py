"""Phase VI-VI1: Security operations schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SecurityIncidentCreatePayload(BaseModel):
    incident_code: str = Field(min_length=1, max_length=64)
    facility_code: str = Field(min_length=1, max_length=64)
    category: str = Field(default="general", min_length=1, max_length=64)
    severity: str = Field(default="medium", min_length=1, max_length=32)
    status: str = Field(default="open", min_length=1, max_length=32)
    response_team: str | None = Field(default=None, max_length=128)
    reported_at: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    visitor_id: str | None = Field(default=None, max_length=64)
    access_control_event_id: str | None = Field(default=None, max_length=64)
    integration_source: str | None = Field(default=None, max_length=64)


class SecurityIncidentResponse(SecurityIncidentCreatePayload):
    id: int
    tenant_id: int


class SecurityIncidentItemResponse(BaseModel):
    record: SecurityIncidentResponse


class SecurityIncidentListResponse(BaseModel):
    records: list[SecurityIncidentResponse]


class SecurityVisitorCreatePayload(BaseModel):
    visitor_name: str = Field(min_length=1, max_length=128)
    host_faculty_id: str | None = Field(default=None, max_length=64)
    visit_purpose: str = Field(default="general", min_length=1, max_length=256)
    status: str = Field(default="expected", min_length=1, max_length=32)
    access_status: str = Field(default="pending", min_length=1, max_length=32)
    badge_id: str | None = Field(default=None, max_length=64)
    check_in_at: str | None = Field(default=None, max_length=64)
    check_out_at: str | None = Field(default=None, max_length=64)
    access_control_event_id: str | None = Field(default=None, max_length=64)


class SecurityVisitorResponse(SecurityVisitorCreatePayload):
    id: int
    tenant_id: int


class SecurityVisitorItemResponse(BaseModel):
    record: SecurityVisitorResponse


class SecurityVisitorListResponse(BaseModel):
    records: list[SecurityVisitorResponse]


class SecurityOperationsBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    total_visitors: int
    active_visitors: int
    denied_access_events: int
    risk_level: str
