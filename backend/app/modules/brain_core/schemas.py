from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class BrainDecisionType(str, Enum):
    RISK = "risk"
    OPTIMIZATION = "optimization"
    PREVENTIVE = "preventive"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"


class BrainPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BrainDecisionStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BrainSignalEnvelopeSchema(BaseModel):
    signal_id: UUID
    tenant_id: int = Field(..., gt=0)
    correlation_id: UUID
    event_type: str = Field(..., min_length=3, max_length=255)
    signal_class: str = Field(..., min_length=3, max_length=128)
    source_module: str = Field(..., min_length=2, max_length=128)
    source_entity_type: str = Field(..., min_length=2, max_length=128)
    source_entity_id: str = Field(..., min_length=1, max_length=255)
    occurred_at: datetime
    subject: dict = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class BrainExplanationSchema(BaseModel):
    summary: str
    factors: list[str] = Field(default_factory=list)
    policy_notes: list[str] = Field(default_factory=list)
    expected_outcome: str | None = None


class BrainActionItemSchema(BaseModel):
    action_type: str = Field(..., min_length=2, max_length=128)
    target_module: str = Field(..., min_length=2, max_length=128)
    payload: dict = Field(default_factory=dict)
    requires_approval: bool = False
    deadline_at: datetime | None = None


class BrainActionPlanSchema(BaseModel):
    plan_id: UUID
    decision_id: UUID
    tenant_id: int = Field(..., gt=0)
    actions: list[BrainActionItemSchema] = Field(default_factory=list)


class BrainDecisionSchema(BaseModel):
    decision_id: UUID
    tenant_id: int = Field(..., gt=0)
    correlation_id: UUID
    decision_type: BrainDecisionType
    situation_type: str = Field(..., min_length=3, max_length=128)
    priority: BrainPriority
    status: BrainDecisionStatus
    confidence_score: float = Field(..., ge=0, le=1)
    severity_score: float = Field(..., ge=0, le=1)
    urgency_score: float = Field(..., ge=0, le=1)
    recommended_actions: list[str] = Field(default_factory=list)
    requires_approval: bool = True
    explanation: BrainExplanationSchema
    created_at: datetime
    created_by: str
    metadata: dict = Field(default_factory=dict)


class BrainDecisionListResponseSchema(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    items: list[BrainDecisionSchema]
