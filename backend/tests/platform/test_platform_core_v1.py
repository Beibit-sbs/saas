from __future__ import annotations

from uuid import uuid4

from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, INTERNAL_HEADERS, _auth_headers, client


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

    # Use a token scoped to the new tenant - no cross-tenant override needed
    tenant_admin_headers = _auth_headers("owner@example.com", ["admin"], tenant_id=tenant_id)

    settings = client.patch(
        f"/api/v1/admin/tenants/{tenant_id}/settings",
        headers=tenant_admin_headers,
        json={"settings": {"locale": "en", "timezone": "UTC"}},
    )
    assert settings.status_code == 200, settings.text
    assert settings.json()["settings"]["locale"] == "en"

    quotas = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/quotas",
        headers=tenant_admin_headers,
        json={"values": {"admissions_per_month": 2500}},
    )
    assert quotas.status_code == 200, quotas.text
    assert quotas.json()["quotas"]["admissions_per_month"] == 2500

    limits = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/limits",
        headers=tenant_admin_headers,
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
        headers=tenant_admin_headers,
        json={"enabled": True},
    )
    assert tenant_feature.status_code == 200, tenant_feature.text
    assert tenant_feature.json()["enabled"] is True

    create_plan = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json={
            "code": f"growth-{suffix}",
            "name": "Growth",
            "price_cents": 9900,
            "features": {"scheduling": True},
            "limits": {"max_users": 500},
        },
    )
    assert create_plan.status_code == 201, create_plan.text
    created_plan = create_plan.json()
    assert created_plan["code"] == f"growth-{suffix}"
    assert created_plan["price_cents"] == 9900
    assert created_plan["features"]["scheduling"] is True
    assert created_plan["limits"]["max_users"] == 500

    listed_plans = client.get("/api/v1/admin/billing/plans", headers=ADMIN_HEADERS)
    assert listed_plans.status_code == 200, listed_plans.text
    matching = [item for item in listed_plans.json() if item["code"] == f"growth-{suffix}"]
    assert len(matching) == 1
    assert matching[0]["id"] == created_plan["id"]

    canonical_tenant_id = 1

    basic_plan = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json={"code": "basic", "name": "Basic", "price_cents": 0, "features": {}, "limits": {}},
    )
    assert basic_plan.status_code == 201, basic_plan.text

    assign_subscription = client.put(
        f"/api/v1/admin/tenants/{canonical_tenant_id}/billing/subscription",
        headers=ADMIN_HEADERS,
        json={"plan_code": "basic"},
    )
    assert assign_subscription.status_code == 200, assign_subscription.text
    assert assign_subscription.json()["plan_code"] == "basic"

    usage = client.post(
        f"/api/v1/admin/tenants/{canonical_tenant_id}/billing/usage/workflow.executions",
        headers=ADMIN_HEADERS,
        json={"value": 3},
    )
    assert usage.status_code == 200, usage.text
    assert usage.json()["value"] >= 3

    enqueue = client.post(
        "/api/v1/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"tenant_id": canonical_tenant_id, "job_type": "usage_rollup", "payload": {"window": "hour"}, "max_retries": 5},
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


def test_platform_core_v1_admin_forbids_non_admin_user() -> None:
    token = create_access_token(
        user_id="student.001",
        roles=["student"],
        auth_source="test",
        tenant_id=1,
        permissions=[],
    )
    response = client.post(
        "/api/v1/admin/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": "x2", "name": "X2"},
    )
    assert response.status_code == 403


def test_platform_core_v1_internal_requires_token() -> None:
    response = client.post(
        "/api/v1/internal/worker/run-once",
    )
    assert response.status_code == 401


def test_platform_core_v1_internal_rejects_wrong_token() -> None:
    response = client.post(
        "/api/v1/internal/worker/run-once",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 403


def test_platform_core_v1_internal_rejects_user_jwt() -> None:
    user_token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
    )
    response = client.post(
        "/api/v1/internal/worker/run-once",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


def test_platform_core_v1_internal_scope_is_explicit_and_denied_when_not_allowed(monkeypatch) -> None:
    monkeypatch.setenv("INTERNAL_API_ALLOWED_SCOPES", "worker.run_once")

    denied = client.get(
        "/api/v1/internal/tenants/1/notifications",
        headers=INTERNAL_HEADERS,
    )
    assert denied.status_code == 403
    assert "internal scope denied" in str(denied.json().get("detail", "")).lower()

    allowed = client.post(
        "/api/v1/internal/worker/run-once",
        headers=INTERNAL_HEADERS,
    )
    assert allowed.status_code == 200


def test_platform_core_v1_billing_plan_duplicate_create_is_rejected_and_state_stable() -> None:
    suffix = uuid4().hex[:8]
    plan_code = f"dup-{suffix}"
    payload = {
        "code": plan_code,
        "name": "Duplicate Stability",
        "price_cents": 1234,
        "features": {"analytics": True},
        "limits": {"api_calls": 1000},
    }

    first = client.post("/api/v1/admin/billing/plans", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/api/v1/admin/billing/plans", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 400, second.text

    listed = client.get("/api/v1/admin/billing/plans", headers=ADMIN_HEADERS)
    assert listed.status_code == 200, listed.text
    matches = [item for item in listed.json() if item["code"] == plan_code]
    assert len(matches) == 1
    assert matches[0]["name"] == "Duplicate Stability"


def test_platform_core_v1_billing_plan_create_rejects_cross_tenant_header_override() -> None:
    tenant_two_headers = {
        **_auth_headers("platform.owner.cross-tenant@example.com", ["admin"], tenant_id=1),
        "X-Tenant-ID": "2",
    }

    response = client.post(
        "/api/v1/admin/billing/plans",
        headers=tenant_two_headers,
        json={
            "code": f"cross-{uuid4().hex[:8]}",
            "name": "Cross Tenant",
            "price_cents": 100,
            "features": {},
            "limits": {},
        },
    )
    assert response.status_code == 403, response.text
    assert "cross-tenant override forbidden" in str(response.json().get("detail", "")).lower()


def test_platform_core_v1_jobs_enqueue_rejects_cross_tenant_header_override() -> None:
    tenant_two_headers = {
        **_auth_headers("platform.owner.jobs-cross-tenant@example.com", ["admin"], tenant_id=1),
        "X-Tenant-ID": "2",
    }

    response = client.post(
        "/api/v1/admin/jobs",
        headers=tenant_two_headers,
        json={
            "tenant_id": 1,
            "job_type": "billing.generate_invoice",
            "payload": {"tenant_id": 1, "period_key": "2026-03"},
            "max_retries": 0,
        },
    )
    assert response.status_code == 403, response.text
    assert "cross-tenant override forbidden" in str(response.json().get("detail", "")).lower()
