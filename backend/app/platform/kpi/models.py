from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TenantMetricSnapshotModel:
    id: int
    tenant_id: int
    metric_key: str
    metric_value: int
    snapshot_date: str
    metadata_json: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    version: int = 1


@dataclass(slots=True)
class TenantDashboardSnapshotModel:
    id: int
    tenant_id: int
    snapshot_date: str
    snapshot_json: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
