from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SemanticEntitySchema(BaseModel):
    code: str
    version: str
    description: str
    grain: str
    allowed_dimensions: list[str]
    allowed_metrics: list[str]


class SemanticMetricSchema(BaseModel):
    code: str
    version: str
    description: str
    source: str
    aggregation: str
    time_grains: list[str]
    tenant_scope: str
    entity: str


class SemanticDimensionSchema(BaseModel):
    code: str
    version: str
    description: str
    allowed_entities: list[str]
    allowed_metrics: list[str]


class SemanticQueryRequestSchema(BaseModel):
    entity: str = Field(min_length=1)
    metrics: list[str] = Field(min_length=1)
    dimensions: list[str] = Field(default_factory=list)
    filters: dict[str, str] = Field(default_factory=dict)
    time_range: str = Field(default="last_12_months", min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)
    explain: bool = False
    version_preferences: dict[str, str] = Field(default_factory=dict)


class SemanticQueryMetadataSchema(BaseModel):
    entity: str
    metrics_returned: list[str]
    dimensions_applied: list[str]
    filters_applied: dict[str, str]
    tenant_id: int
    role_scope: str
    semantic_version: str
    lineage_ref: str
    data_as_of: str


class SemanticQueryResponseSchema(BaseModel):
    data: list[dict[str, Any]]
    metadata: SemanticQueryMetadataSchema
    lineage_ref: str
    data_as_of: str
    explanation: str | None = None


class SemanticInsightReadSchema(BaseModel):
    entity: str
    metric: str
    value: float
    explanation: str
    lineage_ref: str
    data_as_of: str
