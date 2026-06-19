"""Schemas for innovation / commercialization extension runtime shell."""

from __future__ import annotations

from pydantic import BaseModel


class InnovationOpportunity(BaseModel):
    opportunity_id: str
    title: str
    stage: str
    readiness: str
    source_module: str
    notes: str


class InnovationCommercializationShellResponse(BaseModel):
    tenant_id: int
    owner_module: str
    extension_boundary: str
    runtime_mode: str
    canonical_base_vertical: str
    integration_policy: str
    bridge_modules: list[str]


class InnovationOpportunityListResponse(BaseModel):
    tenant_id: int
    items: list[InnovationOpportunity]
