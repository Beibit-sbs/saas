from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FeatureFlagRecord:
    scope: str
    module: str
    key: str
    enabled: bool
    tenant_id: int | None = None
    updated_at: str = ""
