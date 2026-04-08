from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tests.conftest import INTERNAL_HEADERS, _auth_headers, client

from app.platform.events.handlers.webhook_handler import WebhookEventHandler
from app.platform.events.publisher import EventPublisher
from app.platform.events.schemas import OutboxEventRead
from app.platform.events.worker import OutboxEventWorker
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork
from app.platform.webhooks.signer import build_webhook_signature, canonical_json_bytes
from app.platform.webhooks.service import webhook_service


def test_create_webhook_subscription_and_list_via_admin_api() -> None:
    suffix = uuid4().hex[:8]
    tenant = tenant_service.create_tenant(f"wh-sub-{suffix}", f"Webhook {suffix}")
    tenant_id = int(tenant["tenant_id"])

    # Use a token scoped to the new tenant - no cross-tenant override needed
    tenant_admin_headers = _auth_headers("owner@example.com", ["admin"], tenant_id=tenant_id)

    created = client.post(
        "/api/v1/admin/webhooks/subscriptions",
        headers=tenant_admin_headers,
        json={
            "tenant_id": tenant_id,
            "event_type": "student.created",
            "target_url": "https://example.com/webhooks/students",
            "signing_secret": "secret-key-for-tenant-webhook",
        },
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["event_type"] == "student.created"
    assert payload["is_active"] is True

    listed = client.get(f"/api/v1/admin/tenants/{tenant_id}/webhooks/subscriptions", headers=tenant_admin_headers)
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert any(int(item["id"]) == int(payload["id"]) for item in rows)


def test_webhook_subscription_tenant_isolation() -> None:
    first = tenant_service.create_tenant(f"wh-a-{uuid4().hex[:8]}", "Webhook Tenant A")
    second = tenant_service.create_tenant(f"wh-b-{uuid4().hex[:8]}", "Webhook Tenant B")
    first_tenant_id = int(first["tenant_id"])
    second_tenant_id = int(second["tenant_id"])

    webhook_service.create_subscription(
        tenant_id=first_tenant_id,
        event_type="tenant.created",
        target_url="https://example.com/a",
        signing_secret="secret-tenant-a-123456",
    )
    webhook_service.create_subscription(
        tenant_id=second_tenant_id,
        event_type="tenant.created",
        target_url="https://example.com/b",
        signing_secret="secret-tenant-b-123456",
    )

    rows_a = webhook_service.list_subscriptions(tenant_id=first_tenant_id)
    rows_b = webhook_service.list_subscriptions(tenant_id=second_tenant_id)

    assert rows_a
    assert rows_b
    assert all(int(item["tenant_id"]) == first_tenant_id for item in rows_a)
    assert all(int(item["tenant_id"]) == second_tenant_id for item in rows_b)


def test_signed_payload_generation() -> None:
    payload = {"event_type": "tenant.created", "tenant_id": 1}
    payload_bytes = canonical_json_bytes(payload)
    headers = build_webhook_signature(payload_bytes, signing_secret="top-secret-signing-key", timestamp=1700000000)

    assert headers["X-Webhook-Timestamp"] == "1700000000"
    assert headers["X-Webhook-Signature"].startswith("t=1700000000,v1=")
    assert headers["Content-Type"] == "application/json"


def test_dispatch_matching_event_successful_delivery_and_logging(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_sender(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        captured["url"] = url
        captured["headers"] = dict(headers)
        captured["body"] = body.decode("utf-8")
        captured["timeout"] = timeout
        return 202, "accepted"

    monkeypatch.setattr(webhook_service, "_sender", fake_sender)

    tenant = tenant_service.create_tenant(f"wh-ok-{uuid4().hex[:8]}", "Webhook OK")
    tenant_id = int(tenant["tenant_id"])
    webhook_service.create_subscription(
        tenant_id=tenant_id,
        event_type="student.created",
        target_url="https://example.com/tenant/webhook",
        signing_secret="delivery-success-signing-key",
    )

    with UnitOfWork() as uow:
        published = EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="student.created",
            aggregate_type="student_profile",
            aggregate_id="1001",
            payload_json={"student_profile_id": 1001},
        )

    worker = OutboxEventWorker(handlers=[WebhookEventHandler()], retry_delay_seconds=0.0)
    result = worker.run_once()
    assert result["succeeded"] >= 1

    deliveries = webhook_service.list_deliveries(tenant_id=tenant_id)
    matching = [item for item in deliveries if int(item["outbox_event_id"]) == int(published["id"])]
    assert matching
    assert str(matching[0]["delivery_status"]) == "delivered"
    assert int(matching[0]["response_status_code"]) == 202
    assert str(matching[0]["response_body"]) == "accepted"

    payload_json = matching[0]["request_payload_json"]
    assert payload_json["payload"]["event_type"] == "student.created"
    assert "X-Webhook-Signature" in payload_json["headers"]
    assert captured["url"] == "https://example.com/tenant/webhook"


def test_failed_delivery_schedules_retry(monkeypatch) -> None:
    def failing_sender(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        _ = (url, headers, body, timeout)
        return 503, "upstream unavailable"

    monkeypatch.setattr(webhook_service, "_sender", failing_sender)

    tenant = tenant_service.create_tenant(f"wh-fail-{uuid4().hex[:8]}", "Webhook Fail")
    tenant_id = int(tenant["tenant_id"])
    webhook_service.create_subscription(
        tenant_id=tenant_id,
        event_type="enrollment.created",
        target_url="https://example.com/failing-endpoint",
        signing_secret="delivery-failure-signing-key",
    )

    with UnitOfWork() as uow:
        published = EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="enrollment.created",
            aggregate_type="enrollment",
            aggregate_id="4001",
            payload_json={"enrollment_id": 4001},
        )

    worker = OutboxEventWorker(handlers=[WebhookEventHandler()], retry_delay_seconds=0.0)
    result = worker.run_once()
    assert result["succeeded"] >= 1

    deliveries = webhook_service.list_deliveries(tenant_id=tenant_id)
    matching = [item for item in deliveries if int(item["outbox_event_id"]) == int(published["id"])]
    assert matching
    assert str(matching[0]["delivery_status"]) == "failed"
    assert int(matching[0]["response_status_code"]) == 503
    assert matching[0]["next_retry_at"] is not None


def test_retry_failed_delivery(monkeypatch) -> None:
    state = {"calls": 0}

    def flaky_sender(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        _ = (url, headers, body, timeout)
        state["calls"] += 1
        if state["calls"] == 1:
            return 500, "temporary"
        return 200, "ok"

    monkeypatch.setattr(webhook_service, "_sender", flaky_sender)

    tenant = tenant_service.create_tenant(f"wh-retry-{uuid4().hex[:8]}", "Webhook Retry")
    tenant_id = int(tenant["tenant_id"])
    webhook_service.create_subscription(
        tenant_id=tenant_id,
        event_type="grade.submitted",
        target_url="https://example.com/retry-endpoint",
        signing_secret="delivery-retry-signing-key",
    )

    with UnitOfWork() as uow:
        EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="grade.submitted",
            aggregate_type="grade_submission",
            aggregate_id="7001",
            payload_json={"submission_id": 7001},
        )

    worker = OutboxEventWorker(handlers=[WebhookEventHandler()], retry_delay_seconds=0.0)
    first = worker.run_once()
    assert first["succeeded"] >= 1

    monkeypatch.setattr(
        "app.platform.webhooks.service._utc_now",
        lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )

    retried = webhook_service.retry_failed_deliveries(limit=100, actor="pytest")
    assert retried["attempted"] >= 1
    assert retried["delivered"] >= 1

    deliveries = webhook_service.list_deliveries(tenant_id=tenant_id)
    assert any(str(item["delivery_status"]) == "failed" for item in deliveries)
    assert any(str(item["delivery_status"]) == "delivered" and int(item["retry_count"]) >= 1 for item in deliveries)


def test_no_dispatch_for_inactive_subscription(monkeypatch) -> None:
    calls = {"count": 0}

    def should_not_be_called(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        _ = (url, headers, body, timeout)
        calls["count"] += 1
        return 200, "ok"

    monkeypatch.setattr(webhook_service, "_sender", should_not_be_called)

    tenant = tenant_service.create_tenant(f"wh-inactive-{uuid4().hex[:8]}", "Webhook Inactive")
    tenant_id = int(tenant["tenant_id"])
    sub = webhook_service.create_subscription(
        tenant_id=tenant_id,
        event_type="tenant.created",
        target_url="https://example.com/inactive",
        signing_secret="inactive-signing-secret",
    )
    webhook_service.deactivate_subscription(subscription_id=int(sub["id"]))

    event = OutboxEventRead(
        id=999,
        tenant_id=tenant_id,
        event_type="tenant.created",
        aggregate_type="tenant",
        aggregate_id=str(tenant_id),
        payload_json={"tenant_id": tenant_id},
        status="pending",
        retry_count=0,
        available_at=datetime.now(timezone.utc).isoformat(),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    with UnitOfWork() as uow:
        result = webhook_service.dispatch_event_to_subscriptions(event=event, uow=uow)

    assert result["attempted"] == 0
    assert calls["count"] == 0


def test_no_tenant_leakage_for_deliveries(monkeypatch) -> None:
    def ok_sender(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        _ = (url, headers, body, timeout)
        return 200, "ok"

    monkeypatch.setattr(webhook_service, "_sender", ok_sender)

    first = tenant_service.create_tenant(f"wh-d-a-{uuid4().hex[:8]}", "Delivery A")
    second = tenant_service.create_tenant(f"wh-d-b-{uuid4().hex[:8]}", "Delivery B")
    first_tenant_id = int(first["tenant_id"])
    second_tenant_id = int(second["tenant_id"])

    webhook_service.create_subscription(
        tenant_id=first_tenant_id,
        event_type="tenant.created",
        target_url="https://example.com/del-a",
        signing_secret="delivery-a-signing-secret",
    )
    webhook_service.create_subscription(
        tenant_id=second_tenant_id,
        event_type="tenant.created",
        target_url="https://example.com/del-b",
        signing_secret="delivery-b-signing-secret",
    )

    with UnitOfWork() as uow:
        EventPublisher(uow=uow).publish_event(
            tenant_id=first_tenant_id,
            event_type="tenant.created",
            aggregate_type="tenant",
            aggregate_id=str(first_tenant_id),
            payload_json={"tenant_id": first_tenant_id},
        )
        EventPublisher(uow=uow).publish_event(
            tenant_id=second_tenant_id,
            event_type="tenant.created",
            aggregate_type="tenant",
            aggregate_id=str(second_tenant_id),
            payload_json={"tenant_id": second_tenant_id},
        )

    worker = OutboxEventWorker(handlers=[WebhookEventHandler()], retry_delay_seconds=0.0)
    worker.run_once()

    first_deliveries = webhook_service.list_deliveries(tenant_id=first_tenant_id)
    second_deliveries = webhook_service.list_deliveries(tenant_id=second_tenant_id)

    assert first_deliveries
    assert second_deliveries
    assert all(int(item["tenant_id"]) == first_tenant_id for item in first_deliveries)
    assert all(int(item["tenant_id"]) == second_tenant_id for item in second_deliveries)


def test_internal_retry_failed_webhooks_endpoint(monkeypatch) -> None:
    def fail_sender(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        _ = (url, headers, body, timeout)
        return 500, "failed"

    monkeypatch.setattr(webhook_service, "_sender", fail_sender)

    tenant = tenant_service.create_tenant(f"wh-int-{uuid4().hex[:8]}", "Webhook Internal")
    tenant_id = int(tenant["tenant_id"])
    webhook_service.create_subscription(
        tenant_id=tenant_id,
        event_type="tenant.created",
        target_url="https://example.com/internal-retry",
        signing_secret="internal-retry-signing-secret",
    )

    with UnitOfWork() as uow:
        EventPublisher(uow=uow).publish_event(
            tenant_id=tenant_id,
            event_type="tenant.created",
            aggregate_type="tenant",
            aggregate_id=str(tenant_id),
            payload_json={"tenant_id": tenant_id},
        )

    worker = OutboxEventWorker(handlers=[WebhookEventHandler()], retry_delay_seconds=0.0)
    worker.run_once()

    monkeypatch.setattr(
        "app.platform.webhooks.service._utc_now",
        lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )

    def ok_sender(url: str, headers: dict[str, str], body: bytes, timeout: float) -> tuple[int, str]:
        _ = (url, headers, body, timeout)
        return 200, "ok"

    monkeypatch.setattr(webhook_service, "_sender", ok_sender)
    retried = client.post("/api/v1/internal/webhooks/retry-failed", headers=INTERNAL_HEADERS)
    assert retried.status_code == 200, retried.text
    payload = retried.json()
    assert payload["attempted"] >= 1
    assert payload["delivered"] >= 1