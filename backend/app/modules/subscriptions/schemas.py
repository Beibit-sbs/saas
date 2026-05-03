"""Phase LXXVII — Subscriptions schemas."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class SubscriptionCreatePayload(BaseModel):
    tenant_id: int = Field(..., gt=0)
    plan_id: int = Field(..., gt=0)
    notes: Optional[str] = None


class SubscriptionCancelPayload(BaseModel):
    reason: Optional[str] = None


class SubscriptionUpgradePayload(BaseModel):
    new_plan_id: int = Field(..., gt=0)
    notes: Optional[str] = None


class SubscriptionResponse(BaseModel):
    id: str
    tenant_id: int
    plan_id: int
    status: str  # active | cancelled | expired
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class SubscriptionListResponse(BaseModel):
    subscriptions: list[SubscriptionResponse]


class SubscriptionItemResponse(BaseModel):
    subscription: SubscriptionResponse
