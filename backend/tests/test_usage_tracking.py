from app.modules.tenants.service import create_tenant
from app.modules.usage.service import get_usage_sum, list_usage_events, record_usage_event


def test_usage_events_are_tenant_scoped_and_append_only() -> None:
    tenant_a = create_tenant({"slug": "usage-a", "name": "Usage A", "status": "active"})
    tenant_b = create_tenant({"slug": "usage-b", "name": "Usage B", "status": "active"})

    record_usage_event(int(tenant_a["id"]), "ai_requests", 1)
    record_usage_event(int(tenant_a["id"]), "ai_requests", 2)
    record_usage_event(int(tenant_b["id"]), "ai_requests", 5)

    events_a = list_usage_events(int(tenant_a["id"]), metric="ai_requests")
    events_b = list_usage_events(int(tenant_b["id"]), metric="ai_requests")

    assert len(events_a) == 2
    assert len(events_b) == 1
    assert get_usage_sum(int(tenant_a["id"]), "ai_requests") == 3
    assert get_usage_sum(int(tenant_b["id"]), "ai_requests") == 5
