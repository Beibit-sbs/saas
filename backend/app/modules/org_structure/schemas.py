from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.org_structure.models import OrgUnitType


class OrgUnitCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    unit_type: OrgUnitType
    parent_unit_id: Optional[int] = None
    head_person_id: Optional[int] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    location: Optional[str] = Field(None, max_length=500)


class OrgUnitUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    unit_type: Optional[OrgUnitType] = None
    parent_unit_id: Optional[int] = None
    active: Optional[bool] = None
    head_person_id: Optional[int] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    location: Optional[str] = Field(None, max_length=500)


class OrgUnitReadSchema(BaseModel):
    id: int
    tenant_id: int
    name: str
    code: str
    unit_type: OrgUnitType
    parent_unit_id: Optional[int]
    active: bool
    head_person_id: Optional[int]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrgUnitTreeNodeSchema(BaseModel):
    id: int
    name: str
    code: str
    unit_type: OrgUnitType
    active: bool
    children: list[OrgUnitTreeNodeSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}


OrgUnitTreeNodeSchema.model_rebuild()


class OrgUnitMutationResponse(BaseModel):
    unit: OrgUnitReadSchema
    idempotent_replay: bool = False


class OrgUnitConsistencyIssueSchema(BaseModel):
    issue_type: str
    unit_id: int | None = None
    parent_unit_id: int | None = None
    unit_type: OrgUnitType | None = None


class OrgUnitConsistencyReportSchema(BaseModel):
    unit_count: int = Field(ge=0)
    issue_count: int = Field(ge=0)
    issues: list[OrgUnitConsistencyIssueSchema] = Field(default_factory=list)
