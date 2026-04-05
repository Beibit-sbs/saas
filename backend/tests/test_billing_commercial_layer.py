from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.modules.auth.local_users_service import local_user_store
from app.modules.billing.service import (
    assert_quota_with_increment,
    change_subscription_plan,
    ensure_tenant_subscription,
    get_tenant_subscription,
    get_tenant_billing_state,
    transition_subscription_status,
)
from app.modules.quotas.service import get_plan_quotas, update_plan_quotas
from app.modules.tenants.service import get_tenant_by_slug
from app.modules.usage.service import clear_usage_state
from app.modules.usage.service import get_usage_sum, record_usage_event
import pytest

from tests.conftest import ADMIN_HEADERS, client


def _idem(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


@pytest.fixture(autouse=True)
def _reset_client_cookies_for_billing() -> None:
    """Clear client cookies before each test to prevent CSRF due to cookie pollution from prior tests."""
    client.cookies.clear()


def test_self_service_provisioning_creates_tenant_admin_and_trial_subscription() -> None:
    response = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-commercial-layer"),
        json={
            "tenant_name": "Commercial Layer University",
            "admin_login": "billing.owner",
            "admin_password": "StrongPass123!",
            "admin_display_name": "Billing Owner",
            "admin_email": "owner@commercial.example",
            "plan_code": "free",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert int(body["tenant"]["id"]) > 1
    assert body["admin_user"]["login"] == "billing.owner"
    assert body["subscription"]["status"] == "trial"
    assert body["billing_state"]["billing_state"] == "read_write"


def test_self_service_disabled_by_default_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("PLATFORM_SELF_SERVICE_ENABLED", raising=False)

    response = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-prod-disabled"),
        json={
            "tenant_name": "Prod Disabled University",
            "admin_login": "prod.disabled.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "self-service tenant provisioning disabled"
    assert get_tenant_by_slug("prod-disabled-university") is None


def test_self_service_can_be_explicitly_enabled_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PLATFORM_SELF_SERVICE_ENABLED", "true")

    response = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-prod-enabled"),
        json={
            "tenant_name": "Prod Enabled University",
            "admin_login": "prod.enabled.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )

    assert response.status_code == 201, response.text
    assert int(response.json()["tenant"]["id"]) > 1


def test_subscription_suspended_switches_tenant_to_read_only() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-suspended"),
        json={
            "tenant_name": "Suspended Billing Tenant",
            "admin_login": "suspended.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    payload = transition_subscription_status(tenant_id, "suspended")
    assert payload["status"] == "suspended"
    assert get_tenant_billing_state(tenant_id)["billing_state"] == "read_only"

    with_http = None
    try:
        local_user_store.create_user(
            login="blocked.user",
            password="StrongPass123!",
            display_name="Blocked User",
            roles=["student"],
            default_language="ru",
            tenant_id=tenant_id,
        )
    except HTTPException as exc:
        with_http = exc

    assert with_http is not None
    assert with_http.status_code == 403
    assert "billing_required" in str(with_http.detail)

    update_http = None
    try:
        local_user_store.update_user(
            user_id=str(provision.json()["admin_user"]["user_id"]),
            tenant_id=tenant_id,
            display_name="Renamed Suspended Admin",
        )
    except HTTPException as exc:
        update_http = exc

    assert update_http is not None
    assert update_http.status_code == 403

    password_http = None
    try:
        local_user_store.set_password(
            user_id=str(provision.json()["admin_user"]["user_id"]),
            password="AnotherStrongPass123!",
            tenant_id=tenant_id,
        )
    except HTTPException as exc:
        password_http = exc

    assert password_http is not None
    assert password_http.status_code == 403

    delete_http = None
    try:
        local_user_store.delete_user(
            user_id=str(provision.json()["admin_user"]["user_id"]),
            tenant_id=tenant_id,
        )
    except HTTPException as exc:
        delete_http = exc

    assert delete_http is not None
    assert delete_http.status_code == 403


def test_users_limit_is_hard_enforced() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-users-limit"),
        json={
            "tenant_name": "Users Limit Tenant",
            "admin_login": "users-limit.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    ensure_tenant_subscription(tenant_id, plan_code="free", status="active")

    # Free plan allows 10 users; one admin user is already created by provisioning.
    for idx in range(2, 11):
        local_user_store.create_user(
            login=f"free.user.{idx}",
            password="StrongPass123!",
            display_name=f"Free User {idx}",
            roles=["student"],
            default_language="ru",
            tenant_id=tenant_id,
        )

    blocked = None
    try:
        local_user_store.create_user(
            login="free.user.11",
            password="StrongPass123!",
            display_name="Free User 11",
            roles=["student"],
            default_language="ru",
            tenant_id=tenant_id,
        )
    except HTTPException as exc:
        blocked = exc

    assert blocked is not None
    assert blocked.status_code == 403
    assert "quota exceeded" in str(blocked.detail)


def test_flow2_grades_usage_growth_limit_block_and_recovery() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-flow2-grades-billing"),
        json={
            "tenant_name": "Flow2 Grades Billing Tenant",
            "admin_login": "flow2.grades.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text

    tenant_id = int(provision.json()["tenant"]["id"])
    ensure_tenant_subscription(tenant_id, plan_code="free", status="active")

    subscription = get_tenant_subscription(tenant_id)
    plan_id = int(subscription["plan_id"])
    original_limit = int(get_plan_quotas(plan_id).get("grades_submitted", 0))

    try:
        update_plan_quotas(plan_id, {"grades_submitted": 1})

        before = get_usage_sum(tenant_id=tenant_id, metric="grades_submitted")
        allowed = assert_quota_with_increment(tenant_id, "grades_submitted", increment=1)
        assert allowed["within_limit"] is True

        record_usage_event(tenant_id=tenant_id, metric="grades_submitted", value=1)
        after = get_usage_sum(tenant_id=tenant_id, metric="grades_submitted")
        assert after == before + 1

        blocked = None
        try:
            assert_quota_with_increment(tenant_id, "grades_submitted", increment=1)
        except HTTPException as exc:
            blocked = exc

        assert blocked is not None
        assert blocked.status_code == 403
        assert "billing_required" in str(blocked.detail)

        update_plan_quotas(plan_id, {"grades_submitted": 2})
        recovered = assert_quota_with_increment(tenant_id, "grades_submitted", increment=1)
        assert recovered["within_limit"] is True
    finally:
        update_plan_quotas(plan_id, {"grades_submitted": original_limit})


def test_api_usage_counter_is_recorded_for_tenant_requests() -> None:
    before = get_usage_sum(tenant_id=1, metric="api_calls")

    response = client.get("/api/admin/tenants", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text

    after = get_usage_sum(tenant_id=1, metric="api_calls")
    assert after >= before + 1

    billing_state = get_tenant_billing_state(1)
    assert "limits" in billing_state
    assert "usage" in billing_state


def test_subscription_lifecycle_transitions_trial_to_active() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-lifecycle"),
        json={
            "tenant_name": "Lifecycle Tenant",
            "admin_login": "lifecycle.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "basic",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    first = transition_subscription_status(tenant_id, "active")
    assert first["status"] == "active"

    second = transition_subscription_status(tenant_id, "cancelled")
    assert second["status"] == "cancelled"


def test_ai_usage_is_counted_once_per_successful_request(monkeypatch) -> None:
    from app.modules.ai_gateway import service as ai_service

    clear_usage_state()

    class FakeResult:
        output_text = "ok"
        finish_reason = "stop"
        usage = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}

    class FakeAdapter:
        def execute_chat(self, **kwargs):
            return FakeResult()

    monkeypatch.setattr(
        ai_service,
        "_resolve_model",
        lambda model_key, tenant_id=None: {
            "provider": "openai",
            "provider_model_id": "gpt-test",
            "enabled": True,
        },
    )
    monkeypatch.setattr(ai_service, "_adapter_for_provider", lambda provider: FakeAdapter())
    monkeypatch.setattr(ai_service, "_provider_runtime_config", lambda provider, tenant_id=None: {})
    monkeypatch.setattr(ai_service, "enforce_rate_limit", lambda provider, actor, roles: None)

    before = get_usage_sum(tenant_id=1, metric="ai_requests")

    result = ai_service.execute_chat(
        {
            "model": "gpt-test",
            "messages": [{"role": "user", "content": "hi"}],
        },
        actor="owner@example.com",
        roles=["admin"],
        tenant_id=1,
    )

    assert result["output_text"] == "ok"
    after = get_usage_sum(tenant_id=1, metric="ai_requests")
    assert after == before + 1


def test_legacy_platform_job_enqueue_respects_billing_enforcement() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-legacy-job"),
        json={
            "tenant_name": "Legacy Job Billing Tenant",
            "admin_login": "legacy.job.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])
    transition_subscription_status(tenant_id, "suspended")

    response = client.post(
        "/api/v1/admin/jobs",
        headers=ADMIN_HEADERS,
        json={
            "tenant_id": tenant_id,
            "job_type": "backup.run",
            "payload": {"source": "legacy-admin"},
            "max_retries": 3,
        },
    )

    assert response.status_code == 403, response.text
    assert "billing_required" in response.json()["detail"]


def test_legacy_platform_job_enqueue_blocks_cancelled_subscription() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("self-service-legacy-job-cancelled"),
        json={
            "tenant_name": "Legacy Job Cancelled Tenant",
            "admin_login": "legacy.cancelled.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])
    transition_subscription_status(tenant_id, "active")
    transition_subscription_status(tenant_id, "cancelled")

    response = client.post(
        "/api/v1/admin/jobs",
        headers=ADMIN_HEADERS,
        json={
            "tenant_id": tenant_id,
            "job_type": "backup.run",
            "payload": {"source": "legacy-admin"},
            "max_retries": 3,
        },
    )

    assert response.status_code == 403, response.text
    assert "billing_required" in response.json()["detail"]


def test_self_service_idempotency_replays_same_result_for_same_key() -> None:
    payload = {
        "tenant_name": "Idempotent Replay University",
        "admin_login": "idempotent.replay",
        "admin_password": "StrongPass123!",
        "admin_email": "idempotent.replay@example.com",
        "plan_code": "free",
    }

    first = client.post("/api/platform/tenants", headers=_idem("replay-key"), json=payload)
    second = client.post("/api/platform/tenants", headers=_idem("replay-key"), json=payload)

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json() == first.json()


def test_self_service_retry_recovers_partial_create_without_duplicates(monkeypatch) -> None:
    import app.modules.platform.self_service_router as self_service_router

    original_sync = self_service_router.sync_user_roles_from_trusted_source
    original_delete = self_service_router.local_user_store.delete_user
    calls = {"count": 0}

    def fail_once(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated timeout")
        return original_sync(*args, **kwargs)

    monkeypatch.setattr(self_service_router, "sync_user_roles_from_trusted_source", fail_once)
    monkeypatch.setattr(self_service_router, "force_delete_tenant", lambda tenant_id: False)
    monkeypatch.setattr(self_service_router.local_user_store, "delete_user", lambda user_id, tenant_id: True)

    payload = {
        "tenant_name": "Retry Safe University",
        "admin_login": "retry.safe.admin",
        "admin_password": "StrongPass123!",
        "admin_email": "retry.safe@example.com",
        "plan_code": "free",
    }

    first = client.post("/api/platform/tenants", headers=_idem("retry-key"), json=payload)
    assert first.status_code == 400, first.text

    tenant = get_tenant_by_slug("retry-safe-university")
    assert tenant is not None

    monkeypatch.setattr(self_service_router.local_user_store, "delete_user", original_delete)

    second = client.post("/api/platform/tenants", headers=_idem("retry-key"), json=payload)
    assert second.status_code == 201, second.text

    body = second.json()
    tenant_id = int(body["tenant"]["id"])
    assert tenant_id == int(tenant["id"])
    users = local_user_store.list_users(tenant_id=tenant_id)
    assert len([item for item in users if item["login"] == "retry.safe.admin"]) == 1


def test_same_tenant_name_different_admin_is_deterministic_conflict() -> None:
    first = client.post(
        "/api/platform/tenants",
        headers=_idem("tenant-name-1"),
        json={
            "tenant_name": "Controlled Name University",
            "admin_login": "controlled.name.one",
            "admin_password": "StrongPass123!",
            "admin_email": "controlled.one@example.com",
            "plan_code": "free",
        },
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/api/platform/tenants",
        headers=_idem("tenant-name-2"),
        json={
            "tenant_name": "Controlled Name University",
            "admin_login": "controlled.name.two",
            "admin_password": "StrongPass123!",
            "admin_email": "controlled.two@example.com",
            "plan_code": "free",
        },
    )
    assert second.status_code == 409, second.text
    assert "tenant slug" in second.json()["detail"]


def test_same_admin_login_or_email_conflicts_without_orphan_tenant() -> None:
    first = client.post(
        "/api/platform/tenants",
        headers=_idem("admin-unique-1"),
        json={
            "tenant_name": "Admin Unique One",
            "admin_login": "unique.admin",
            "admin_password": "StrongPass123!",
            "admin_email": "unique.admin@example.com",
            "plan_code": "free",
        },
    )
    assert first.status_code == 201, first.text

    login_conflict = client.post(
        "/api/platform/tenants",
        headers=_idem("admin-unique-2"),
        json={
            "tenant_name": "Admin Unique Two",
            "admin_login": "unique.admin",
            "admin_password": "StrongPass123!",
            "admin_email": "another@example.com",
            "plan_code": "free",
        },
    )
    assert login_conflict.status_code == 409, login_conflict.text
    assert login_conflict.json()["detail"] == "login already exists"
    assert get_tenant_by_slug("admin-unique-two") is None

    email_conflict = client.post(
        "/api/platform/tenants",
        headers=_idem("admin-unique-3"),
        json={
            "tenant_name": "Admin Unique Three",
            "admin_login": "unique.admin.three",
            "admin_password": "StrongPass123!",
            "admin_email": "unique.admin@example.com",
            "plan_code": "free",
        },
    )
    assert email_conflict.status_code == 409, email_conflict.text
    assert email_conflict.json()["detail"] == "email already exists"
    assert get_tenant_by_slug("admin-unique-three") is None


def test_trial_expiry_transitions_to_suspended_by_default(monkeypatch) -> None:
    monkeypatch.delenv("BILLING_TRIAL_AUTO_ACTIVATE", raising=False)

    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("trial-expiry-suspended"),
        json={
            "tenant_name": "Trial Expiry Suspended",
            "admin_login": "trial.suspended.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    ensure_tenant_subscription(
        tenant_id,
        plan_code="free",
        status="trial",
        trial_ends_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )

    billing_state = get_tenant_billing_state(tenant_id)
    assert billing_state["subscription_status"] == "suspended"
    assert billing_state["billing_state"] == "read_only"


def test_trial_expiry_transitions_to_active_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("BILLING_TRIAL_AUTO_ACTIVATE", "true")

    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("trial-expiry-active"),
        json={
            "tenant_name": "Trial Expiry Active",
            "admin_login": "trial.active.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    ensure_tenant_subscription(
        tenant_id,
        plan_code="free",
        status="trial",
        trial_ends_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )

    billing_state = get_tenant_billing_state(tenant_id)
    assert billing_state["subscription_status"] == "active"
    assert billing_state["billing_state"] == "read_write"


def test_cancelled_is_terminal_for_status_transition() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("cancelled-terminal"),
        json={
            "tenant_name": "Cancelled Terminal",
            "admin_login": "cancelled.terminal.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "basic",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    transition_subscription_status(tenant_id, "active")
    transition_subscription_status(tenant_id, "cancelled")

    with_error = None
    try:
        transition_subscription_status(tenant_id, "active")
    except ValueError as exc:
        with_error = exc

    assert with_error is not None
    assert "invalid transition" in str(with_error)


def test_plan_change_supports_downgrade_next_period_and_rollover() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("plan-change-next-period"),
        json={
            "tenant_name": "Plan Change Tenant",
            "admin_login": "plan.change.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "pro",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    ensure_tenant_subscription(tenant_id, plan_code="pro", status="active")

    changed = change_subscription_plan(tenant_id, "basic", effective="next_period")
    assert changed["effective"] == "next_period"
    assert changed["subscription"]["plan_code"] == "pro"
    assert changed["subscription"]["next_plan_code"] == "basic"

    ensure_tenant_subscription(
        tenant_id,
        plan_code="pro",
        status="active",
        current_period_start=(datetime.now(timezone.utc) - timedelta(days=35)).isoformat(),
        current_period_end=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        next_plan_code="basic",
    )

    rolled = get_tenant_subscription(tenant_id)
    assert rolled is not None
    assert rolled["plan_code"] == "basic"
    assert rolled.get("next_plan_code") is None


def test_usage_snapshot_is_period_bound() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("period-bound-usage"),
        json={
            "tenant_name": "Period Usage Tenant",
            "admin_login": "period.usage.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "free",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    record_usage_event(tenant_id, "api_calls", 5)

    future_start = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    future_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    ensure_tenant_subscription(
        tenant_id,
        plan_code="free",
        status="active",
        current_period_start=future_start,
        current_period_end=future_end,
    )

    billing_state = get_tenant_billing_state(tenant_id)
    assert int(billing_state["usage"]["api_calls"]) == 0


def test_suspended_to_active_recovery_restores_write_mode() -> None:
    provision = client.post(
        "/api/platform/tenants",
        headers=_idem("suspended-recovery"),
        json={
            "tenant_name": "Suspended Recovery Tenant",
            "admin_login": "suspended.recovery.admin",
            "admin_password": "StrongPass123!",
            "plan_code": "basic",
        },
    )
    assert provision.status_code == 201, provision.text
    tenant_id = int(provision.json()["tenant"]["id"])

    transition_subscription_status(tenant_id, "active")
    transition_subscription_status(tenant_id, "suspended")
    assert get_tenant_billing_state(tenant_id)["billing_state"] == "read_only"

    transition_subscription_status(tenant_id, "active")
    assert get_tenant_billing_state(tenant_id)["billing_state"] == "read_write"
