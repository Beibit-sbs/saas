from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, INTERNAL_HEADERS, client


def test_platform_core_v1_end_to_end_flow() -> None:
    suffix = uuid4().hex[:8]
    slug = f"tenant-{suffix}"
    name = f"Tenant {suffix}"

    created = client.post(
        "/api/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": slug, "name": name},
    )
    assert created.status_code == 201, created.text
    tenant = created.json()
    tenant_id = int(tenant["tenant_id"])

    settings = client.patch(
        f"/api/v1/admin/tenants/{tenant_id}/settings",
        headers=ADMIN_HEADERS,
        json={"settings": {"locale": "en", "timezone": "UTC"}},
    )
    assert settings.status_code == 200, settings.text
    assert settings.json()["settings"]["locale"] == "en"

    quotas = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/quotas",
        headers=ADMIN_HEADERS,
        json={"values": {"admissions_per_month": 2500}},
    )
    assert quotas.status_code == 200, quotas.text
    assert quotas.json()["quotas"]["admissions_per_month"] == 2500

    limits = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/limits",
        headers=ADMIN_HEADERS,
        json={"values": {"max_users": 120}},
    )
    assert limits.status_code == 200, limits.text
    assert limits.json()["limits"]["max_users"] == 120

    platform_feature = client.put(
        "/api/v1/admin/features/scheduling/conflict_detection",
        headers=ADMIN_HEADERS,
        json={"enabled": True},
    )
    assert platform_feature.status_code == 200, platform_feature.text
    assert platform_feature.json()["enabled"] is True

    tenant_feature = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/features/admissions/advanced_review",
        headers=ADMIN_HEADERS,
        json={"enabled": True},
    )
    assert tenant_feature.status_code == 200, tenant_feature.text
    assert tenant_feature.json()["enabled"] is True

    plan_code = f"growth-{suffix}"
    create_plan = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json={
            "code": plan_code,
            "name": "Growth",
            "price_cents": 9900,
            "features": {"scheduling": True},
            "limits": {"max_users": 500},
        },
    )
    assert create_plan.status_code == 201, create_plan.text
    assert create_plan.json()["code"] == plan_code

    assign_subscription = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/billing/subscription",
        headers=ADMIN_HEADERS,
        json={"plan_code": plan_code},
    )
    assert assign_subscription.status_code == 200, assign_subscription.text
    assert assign_subscription.json()["plan_code"] == plan_code

    usage = client.post(
        f"/api/v1/admin/tenants/{tenant_id}/billing/usage/workflow.executions",
        headers=ADMIN_HEADERS,
        json={"value": 3},
    )
    assert usage.status_code == 200, usage.text
    assert usage.json()["value"] >= 3

    enqueue = client.post(
        "/api/v1/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"tenant_id": tenant_id, "job_type": "usage_rollup", "payload": {"window": "hour"}, "max_retries": 5},
    )
    assert enqueue.status_code == 201, enqueue.text
    job_id = int(enqueue.json()["id"])

    run = client.post(
        f"/api/v1/internal/jobs/{job_id}/run",
        headers=INTERNAL_HEADERS,
        json={"succeed": True, "result": {"rolled_up": True}},
    )
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "succeeded"

    notify = client.post(
        "/api/v1/admin/notifications",
        headers=ADMIN_HEADERS,
        json={
            "tenant_id": tenant_id,
            "channel": "email",
            "target": "ops@example.com",
            "subject": "Platform Event",
            "payload": {"event": "tenant.created"},
        },
    )
    assert notify.status_code == 201, notify.text

    notifications = client.get(f"/api/v1/internal/tenants/{tenant_id}/notifications", headers=INTERNAL_HEADERS)
    assert notifications.status_code == 200, notifications.text
    assert len(notifications.json()) >= 1

    public_tenant = client.get(f"/api/v1/public/tenants/{tenant_id}")
    assert public_tenant.status_code == 404, public_tenant.text

    public_features = client.get(f"/api/v1/public/tenants/{tenant_id}/features")
    assert public_features.status_code == 404, public_features.text

    public_subscription = client.get(f"/api/v1/public/tenants/{tenant_id}/subscription")
    assert public_subscription.status_code == 404, public_subscription.text


def test_platform_core_v1_admin_requires_auth() -> None:
    response = client.post("/api/v1/admin/tenants", json={"slug": "x1", "name": "X1"})
    assert response.status_code == 401


def test_platform_core_v1_internal_requires_token() -> None:
    response = client.post(
        "/api/v1/internal/worker/run-once",
    )
    assert response.status_code == 401
