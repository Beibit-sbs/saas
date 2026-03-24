from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TenantPlatformRecord:
    tenant_id: int
    slug: str
    name: str
    status: str = "active"
    suspended: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    quotas: dict[str, int] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)
    updated_at: str = ""
