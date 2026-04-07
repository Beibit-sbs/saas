from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


WebhookDeliveryStatus = Literal["pending", "delivered", "failed"]


class WebhookSubscriptionCreateSchema(BaseModel):
    tenant_id: int = Field(gt=0)
    event_type: str = Field(min_length=3, max_length=128)
    target_url: str = Field(min_length=10, max_length=2048)
    signing_secret: str = Field(min_length=16, max_length=255)


class WebhookSubscriptionReadSchema(BaseModel):
    id: int
    tenant_id: int
    event_type: str
    target_url: str
    is_active: bool
    created_at: str
    updated_at: str
    version: int


class WebhookDeliveryReadSchema(BaseModel):
    id: int
    tenant_id: int
    subscription_id: int
    outbox_event_id: int
    event_type: str
    target_url: str
    request_payload_json: dict[str, Any]
    response_status_code: int | None = None
    response_body: str | None = None
    delivery_status: WebhookDeliveryStatus
    retry_count: int
    next_retry_at: str | None = None
    last_error: str | None = None
    created_at: str
    delivered_at: str | None = None


class WebhookDeliveryListSchema(BaseModel):
    tenant_id: int
    total: int
    items: list[WebhookDeliveryReadSchema]


class WebhookRetryResponseSchema(BaseModel):
    attempted: int
    delivered: int
    failed: int