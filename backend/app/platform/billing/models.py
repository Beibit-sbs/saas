from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlanRecord:
    id: int
    code: str
    name: str
    price_cents: int
    features: dict[str, bool] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)
    active: bool = True
    created_at: str = ""


@dataclass(slots=True)
class SubscriptionRecord:
    tenant_id: int
    plan_id: int
    plan_code: str
    status: str = "active"
    started_at: str = ""
