"""Platform event type constants for the event ingestion layer."""
from __future__ import annotations

# Fired when analytics event projection data is read (GET /api/analytics/kpis)
ANALYTICS_EVENT_READ: str = "analytics.event.read"

# Fired when KPI data is read (GET /api/analytics/kpis/trends|insights|recommendations)
ANALYTICS_KPI_READ: str = "analytics.kpi.read"

# Fired when billing usage is incremented (billing.increment_usage)
BILLING_USAGE_RECORDED: str = "billing.usage.recorded"

# Fired when tenant KPI refresh is executed (POST /api/analytics/kpis/refresh)
KPI_REFRESH_EXECUTED: str = "analytics.kpi.refresh.executed"

VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {
        ANALYTICS_EVENT_READ,
        ANALYTICS_KPI_READ,
        BILLING_USAGE_RECORDED,
        KPI_REFRESH_EXECUTED,
    }
)
