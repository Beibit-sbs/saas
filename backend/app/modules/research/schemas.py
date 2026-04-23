from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


ResearchGrantStatus = Literal["planned", "active", "submitted", "delayed", "closed"]
ResearchPublicationStatus = Literal["draft", "submitted", "published", "stalled"]
ResearchLabStatus = Literal["active", "inactive", "maintenance"]
ResearchIpAssetStatus = Literal["draft", "filed", "granted", "expired"]
ResearchExperimentStatus = Literal["planned", "running", "paused", "completed", "cancelled"]


class ResearchGrantCreateSchema(BaseModel):
    grant_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    pi_faculty_id: str = Field(min_length=1, max_length=64)
    deadline: date
    funding_amount: float = Field(default=0, ge=0)
    status: ResearchGrantStatus = "active"


class ResearchGrantSchema(ResearchGrantCreateSchema):
    id: int
    tenant_id: str | None = None


class ResearchPublicationCreateSchema(BaseModel):
    publication_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=300)
    lead_author_id: str = Field(min_length=1, max_length=64)
    target_venue: str = Field(min_length=1, max_length=120)
    last_activity_days: int = Field(default=0, ge=0)
    status: ResearchPublicationStatus = "draft"


class ResearchPublicationSchema(ResearchPublicationCreateSchema):
    id: int
    tenant_id: str | None = None


class ResearchLabCreateSchema(BaseModel):
    lab_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    status: ResearchLabStatus = "active"


class ResearchLabSchema(ResearchLabCreateSchema):
    id: int
    tenant_id: str | None = None


class ResearchIpAssetCreateSchema(BaseModel):
    asset_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    status: ResearchIpAssetStatus = "draft"


class ResearchIpAssetSchema(ResearchIpAssetCreateSchema):
    id: int
    tenant_id: str | None = None


class ResearchExperimentCreateSchema(BaseModel):
    experiment_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    lab_code: str = Field(min_length=1, max_length=64)
    principal_investigator_id: str = Field(min_length=1, max_length=64)
    status: ResearchExperimentStatus = "planned"


class ResearchExperimentSchema(ResearchExperimentCreateSchema):
    id: int
    tenant_id: str | None = None


class ResearchGrantListResponseSchema(BaseModel):
    items: list[ResearchGrantSchema]


class ResearchPublicationListResponseSchema(BaseModel):
    items: list[ResearchPublicationSchema]


class ResearchLabListResponseSchema(BaseModel):
    items: list[ResearchLabSchema]


class ResearchIpAssetListResponseSchema(BaseModel):
    items: list[ResearchIpAssetSchema]


class ResearchExperimentListResponseSchema(BaseModel):
    items: list[ResearchExperimentSchema]


class ResearchGrantItemResponseSchema(BaseModel):
    item: ResearchGrantSchema


class ResearchPublicationItemResponseSchema(BaseModel):
    item: ResearchPublicationSchema


class ResearchLabItemResponseSchema(BaseModel):
    item: ResearchLabSchema


class ResearchIpAssetItemResponseSchema(BaseModel):
    item: ResearchIpAssetSchema


class ResearchExperimentItemResponseSchema(BaseModel):
    item: ResearchExperimentSchema


class ResearchGrantStatusUpdateSchema(BaseModel):
    status: ResearchGrantStatus


class ResearchPublicationStatusUpdateSchema(BaseModel):
    status: ResearchPublicationStatus


class ResearchLabStatusUpdateSchema(BaseModel):
    status: ResearchLabStatus


class ResearchExperimentStatusUpdateSchema(BaseModel):
    status: ResearchExperimentStatus


class ResearchHealthSnapshotSchema(BaseModel):
    tenant_id: int = Field(..., ge=1)
    grants_total: int = Field(..., ge=0)
    grants_near_deadline: int = Field(..., ge=0)
    grant_pipeline_at_risk: int = Field(..., ge=0)
    publications_total: int = Field(..., ge=0)
    stalled_publications: int = Field(..., ge=0)
    publication_tracking_alerts: int = Field(..., ge=0)
    labs_total: int = Field(..., ge=0)
    labs_with_low_utilization: int = Field(..., ge=0)
    lab_utilization_rate: float = Field(..., ge=0, le=100)
    ip_assets_total: int = Field(..., ge=0)
    experiments_total: int = Field(..., ge=0)
    active_experiments: int = Field(..., ge=0)


class ResearchHealthResponseSchema(BaseModel):
    item: ResearchHealthSnapshotSchema
