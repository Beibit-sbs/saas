import threading
import pytest

from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.audit import service as audit_service


def _tenant_headers(tenant_id: int, base_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(base_headers or ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={
            "slug": "tenant-b-audit",
            "name": "Tenant B Audit",
            "status": "active",
        },
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_tenant_b_events_are_not_visible_in_tenant_a_view() -> None:
    audit_service.clear_audit_events()
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    create_event = client.post(
        "/api/admin/audit-test",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert create_event.status_code == 200, create_event.text

    list_default = client.get("/api/admin/audit/events?action=audit_test", headers=ADMIN_HEADERS)
    assert list_default.status_code == 200, list_default.text
    assert all(int(item.get("tenant_id", 1)) == 1 for item in list_default.json()["events"])

    list_tenant_b = client.get(
        "/api/admin/audit/events?action=audit_test",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert list_tenant_b.status_code == 200, list_tenant_b.text
    assert len(list_tenant_b.json()["events"]) >= 1
    assert int(list_tenant_b.json()["events"][0]["tenant_id"]) == tenant_b_id


def test_platform_admin_can_query_target_tenant_events() -> None:
    audit_service.clear_audit_events()
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    create_event = client.post(
        "/api/admin/audit-test",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert create_event.status_code == 200, create_event.text

    list_tenant_b = client.get(
        f"/api/admin/audit/events?action=audit_test&tenant_id={tenant_b_id}",
        headers=platform_headers,
    )
    assert list_tenant_b.status_code == 200, list_tenant_b.text
    assert len(list_tenant_b.json()["events"]) >= 1
    assert int(list_tenant_b.json()["events"][0]["tenant_id"]) == tenant_b_id


def test_non_platform_admin_cannot_override_tenant_id() -> None:
    tenant_b_id = _create_tenant_b()

    response = client.get(
        f"/api/admin/audit/events?tenant_id={tenant_b_id}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404


def test_default_tenant_fallback_without_header() -> None:
    audit_service.clear_audit_events()

    create_event = client.post("/api/admin/audit-test", headers=ADMIN_HEADERS)
    assert create_event.status_code == 200, create_event.text

    list_default = client.get("/api/admin/audit/events?action=audit_test", headers=ADMIN_HEADERS)
    assert list_default.status_code == 200, list_default.text
    assert len(list_default.json()["events"]) >= 1
    assert int(list_default.json()["events"][0]["tenant_id"]) == 1


def test_audit_event_always_contains_tenant_id() -> None:
    audit_service.clear_audit_events()

    audit_service.log_admin_action(
        actor="tenant-check@example.com",
        action="tenant_id_presence_check",
        path="/test/tenant-id",
        client_ip="10.0.0.1",
        tenant_id=1,
    )

    events = audit_service.list_admin_actions(action="tenant_id_presence_check", tenant_id=1, limit=5)
    assert len(events) >= 1
    assert "tenant_id" in events[0]
    assert int(events[0]["tenant_id"]) == 1


def test_audit_event_without_tenant_context_fails_closed() -> None:
    audit_service.clear_audit_events()

    with pytest.raises(RuntimeError, match="tenant_id is required"):
        audit_service.log_admin_action(
            actor="tenant-check@example.com",
            action="background_default_tenant",
            path="/workers/background-default",
            client_ip="10.0.0.1",
        )


def test_list_admin_actions_without_tenant_context_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="tenant_id is required"):
        audit_service.list_admin_actions(action="background_default_tenant", limit=5)


def test_background_thread_audit_event_honors_explicit_tenant_id() -> None:
    audit_service.clear_audit_events()

    def producer() -> None:
        audit_service.log_admin_action(
            actor="bg-worker@example.com",
            action="background_explicit_tenant",
            path="/workers/background-explicit",
            client_ip="10.0.0.1",
            tenant_id=2,
        )

    worker = threading.Thread(target=producer)
    worker.start()
    worker.join()

    events = audit_service.list_admin_actions(action="background_explicit_tenant", tenant_id=2, limit=5)
    assert len(events) >= 1
    assert int(events[0]["tenant_id"]) == 2
