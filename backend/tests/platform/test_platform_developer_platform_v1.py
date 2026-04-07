from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.modules.students import service as students_service
from app.platform.developer.repository import DeveloperRepository
from app.platform.developer import service as developer_service
from app.platform.developer.service import DeveloperPlatformService
from app.modules.observability.metrics import snapshot_developer_analytics_contract_metrics
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def _tenant(prefix: str = "dev-app") -> int:
    row = tenant_service.create_tenant(f"{prefix}-{uuid4().hex[:8]}", f"{prefix} tenant")
    return int(row["tenant_id"])


def _developer_headers(app_key: str, app_secret: str, tenant_id: int) -> dict[str, str]:
    del tenant_id
    return {
        "X-App-Key": app_key,
        "X-App-Secret": app_secret,
    }


def _tenant_admin_headers(tenant_id: int) -> dict[str, str]:
    return _auth_headers(
        f"tenant.admin.developer.{tenant_id}@example.com",
        ["admin"],
        tenant_id=tenant_id,
    )


def _emit_analytics_event(*, tenant_id: int, event_type: str, event_id: int) -> None:
    event = OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id=str(event_id),
        payload_json={"id": event_id},
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )
    with UnitOfWork() as uow:
        AnalyticsEventHandler().handle(event, uow=uow)


def _set_developer_analytics_entitlement(*, tenant_id: int, enabled: bool) -> None:
    response = client.put(
        f"/api/v1/admin/tenants/{int(tenant_id)}/features/analytics/developer_read",
        headers=_tenant_admin_headers(tenant_id),
        json={"enabled": bool(enabled)},
    )
    assert response.status_code == 200, response.text


def _installed_analytics_app(*, tenant_id: int) -> dict[str, object]:
    app = developer_service.developer_service.create_app(
        tenant_id=tenant_id,
        name=f"Analytics App {tenant_id}",
        description="tenant analytics read app",
        owner_email="owner@example.com",
        scopes=["analytics.read"],
    )
    developer_service.developer_service.install_app(
        app_id=int(app["id"]),
        tenant_id=tenant_id,
        installed_by="test-suite",
    )
    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=True)
    return app


class TestDeveloperPlatformService:
    def test_create_rotate_install_and_validate_credentials(self) -> None:
        tenant_id = _tenant("svc-dev")
        service = DeveloperPlatformService(repository=DeveloperRepository())

        app = service.create_app(
            tenant_id=tenant_id,
            name="Registrar Connector",
            description="syncs rosters",
            owner_email="owner@example.com",
            scopes=["students.read", "analytics.read"],
        )
        assert app["id"] >= 1
        assert app["app_key"].startswith("app_")
        assert app["app_secret"]
        assert app["scopes"] == ["analytics.read", "students.read"]

        installation = service.install_app(app_id=int(app["id"]), tenant_id=tenant_id, installed_by="owner@example.com")
        assert installation["tenant_id"] == tenant_id

        validated = service.validate_credentials(
            app_key=str(app["app_key"]),
            app_secret=str(app["app_secret"]),
            tenant_id=tenant_id,
            required_scope="students.read",
        )
        assert validated["tenant_id"] == tenant_id
        assert validated["app_id"] == int(app["id"])

        rotated = service.rotate_secret(int(app["id"]))
        assert rotated["app_secret"] != app["app_secret"]

        with pytest.raises(ValueError, match="invalid developer app secret"):
            service.validate_credentials(
                app_key=str(app["app_key"]),
                app_secret=str(app["app_secret"]),
                tenant_id=tenant_id,
                required_scope="students.read",
            )

        validated_after_rotation = service.validate_credentials(
            app_key=str(app["app_key"]),
            app_secret=str(rotated["app_secret"]),
            tenant_id=tenant_id,
            required_scope="analytics.read",
        )
        assert validated_after_rotation["installation_id"] == installation["id"]

    def test_scope_and_installation_enforcement(self) -> None:
        tenant_id = _tenant("svc-scope")
        other_tenant_id = _tenant("svc-other")
        service = DeveloperPlatformService(repository=DeveloperRepository())
        app = service.create_app(
            tenant_id=tenant_id,
            name="Analytics Client",
            description="analytics only",
            owner_email="owner@example.com",
            scopes=["analytics.read"],
        )
        service.install_app(app_id=int(app["id"]), tenant_id=tenant_id, installed_by="owner@example.com")

        with pytest.raises(ValueError, match="scope not granted"):
            service.validate_credentials(
                app_key=str(app["app_key"]),
                app_secret=str(app["app_secret"]),
                tenant_id=tenant_id,
                required_scope="students.read",
            )

        with pytest.raises(ValueError, match="not installed"):
            service.validate_credentials(
                app_key=str(app["app_key"]),
                app_secret=str(app["app_secret"]),
                tenant_id=other_tenant_id,
                required_scope="analytics.read",
            )


def test_admin_api_create_install_subscribe_and_list_logs(reset_shared_state) -> None:
    tenant_id = 1

    create_resp = client.post(
        "/api/v1/admin/platform/developer/apps",
        json={
            "name": "Registrar Sync",
            "description": "integration",
            "owner_email": "owner@example.com",
            "scopes": ["students.read", "analytics.read"],
        },
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["app_key"].startswith("app_")
    assert created["app_secret"]

    list_resp = client.get("/api/v1/admin/platform/developer/apps", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    assert any(item["id"] == created["id"] for item in list_resp.json())

    install_resp = client.post(
        f"/api/v1/admin/platform/developer/apps/{created['id']}/installations",
        json={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert install_resp.status_code == 201, install_resp.text
    assert install_resp.json()["tenant_id"] == tenant_id

    subscribe_resp = client.post(
        f"/api/v1/admin/platform/developer/apps/{created['id']}/subscriptions",
        json={"event_type": "student.created"},
        headers=ADMIN_HEADERS,
    )
    assert subscribe_resp.status_code == 201, subscribe_resp.text
    assert subscribe_resp.json()["event_type"] == "student.created"

    logs_resp = client.get(
        f"/api/v1/admin/platform/developer/apps/{created['id']}/logs",
        headers=ADMIN_HEADERS,
    )
    assert logs_resp.status_code == 200, logs_resp.text
    assert logs_resp.json() == []


def test_developer_students_endpoint_enforces_credentials_and_logs_usage(reset_shared_state) -> None:
    tenant_id = 1
    create_resp = client.post(
        "/api/v1/admin/platform/developer/apps",
        json={
            "name": "Student Reader",
            "description": "reads students",
            "owner_email": "owner@example.com",
            "scopes": ["students.read"],
        },
        headers=ADMIN_HEADERS,
    )
    app = create_resp.json()

    install_resp = client.post(
        f"/api/v1/admin/platform/developer/apps/{app['id']}/installations",
        json={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert install_resp.status_code == 201, install_resp.text

    students_service.create_student(
        {
            "student_id": f"ST-{uuid4().hex[:6].upper()}",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada.lovelace@example.edu",
            "status": "active",
        },
        tenant_id,
    )

    unauthorized_resp = client.get("/api/dev/students")
    assert unauthorized_resp.status_code == 401, unauthorized_resp.text

    authorized_resp = client.get(
        "/api/dev/students",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_id),
    )
    assert authorized_resp.status_code == 200, authorized_resp.text
    body = authorized_resp.json()
    assert len(body) >= 1
    assert any(item["email"] == "ada.lovelace@example.edu" for item in body)

    logs_resp = client.get(
        f"/api/v1/admin/platform/developer/apps/{app['id']}/logs",
        headers=ADMIN_HEADERS,
    )
    assert logs_resp.status_code == 200, logs_resp.text
    logs = logs_resp.json()
    assert len(logs) >= 1
    assert any(item["endpoint"] == "/api/dev/students" and item["status_code"] == 200 for item in logs)


def test_developer_api_scope_and_tenant_isolation(reset_shared_state) -> None:
    tenant_id = 1
    before_contract = snapshot_developer_analytics_contract_metrics()

    create_resp = client.post(
        "/api/v1/admin/platform/developer/apps",
        json={
            "name": "Analytics Only",
            "description": "reads analytics",
            "owner_email": "owner@example.com",
            "scopes": ["analytics.read"],
        },
        headers=ADMIN_HEADERS,
    )
    app = create_resp.json()

    install_resp = client.post(
        f"/api/v1/admin/platform/developer/apps/{app['id']}/installations",
        json={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert install_resp.status_code == 201, install_resp.text

    forbidden_resp = client.get(
        "/api/dev/students",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_id),
    )
    assert forbidden_resp.status_code == 403, forbidden_resp.text

    _set_developer_analytics_entitlement(tenant_id=tenant_id, enabled=True)

    ok_resp = client.get(
        "/api/dev/analytics/kpi",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_id),
    )
    assert ok_resp.status_code == 200, ok_resp.text
    assert ok_resp.json()["tenant_id"] == tenant_id

    after_contract = snapshot_developer_analytics_contract_metrics()
    key = ("analytics.kpi", "success", "ok")
    assert int(after_contract.get(key, 0)) >= int(before_contract.get(key, 0)) + 1


def test_developer_analytics_events_endpoint_returns_empty_state(reset_shared_state) -> None:
    tenant_id = _tenant("dev-events-empty")
    app = _installed_analytics_app(tenant_id=tenant_id)

    response = client.get(
        "/api/dev/analytics/events",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_id),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["total"] == 0
    assert body["limit"] == 50
    assert body["ordering"] == "created_at_desc"
    assert body["next_cursor"] is None
    assert body["applied_filters"] == {
        "event_type": None,
        "date_from": None,
        "date_to": None,
    }
    assert body["items"] == []
    assert body["data_as_of"] is None
    assert body["freshness_status"] == "empty"
    assert isinstance(body["served_at"], str)
    assert body["served_at"]


def test_developer_analytics_latest_kpi_snapshot_empty_state_404(reset_shared_state) -> None:
    tenant_id = _tenant("dev-kpi-empty")
    app = _installed_analytics_app(tenant_id=tenant_id)
    before_contract = snapshot_developer_analytics_contract_metrics()

    response = client.get(
        "/api/dev/analytics/kpis/latest",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_id),
    )
    assert response.status_code == 404, response.text

    after_contract = snapshot_developer_analytics_contract_metrics()
    key = ("analytics.kpis.latest", "denied", "not_found")
    assert int(after_contract.get(key, 0)) >= int(before_contract.get(key, 0)) + 1


def test_developer_analytics_events_endpoint_is_tenant_scoped(reset_shared_state) -> None:
    tenant_a = _tenant("dev-events-a")
    tenant_b = _tenant("dev-events-b")
    app = _installed_analytics_app(tenant_id=tenant_a)

    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=8101)
    _emit_analytics_event(tenant_id=tenant_b, event_type="grade.submitted", event_id=8102)

    response = client.get(
        "/api/dev/analytics/events",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_a),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_id"] == tenant_a
    assert body["total"] == 1
    assert body["items"][0]["tenant_id"] == tenant_a
    assert body["items"][0]["event_type"] == "student.created"


def test_developer_analytics_events_tenant_scoped_under_filters_and_pagination(reset_shared_state) -> None:
    tenant_a = _tenant("dev-events-filter-page-a")
    tenant_b = _tenant("dev-events-filter-page-b")
    app = _installed_analytics_app(tenant_id=tenant_a)

    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=8201)
    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=8202)
    _emit_analytics_event(tenant_id=tenant_b, event_type="student.created", event_id=8203)

    first = client.get(
        "/api/dev/analytics/events?event_type=student.created&limit=1",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_a),
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["tenant_id"] == tenant_a
    assert first_body["total"] == 1
    assert first_body["applied_filters"]["event_type"] == "student.created"
    assert first_body["items"][0]["tenant_id"] == tenant_a
    assert first_body["next_cursor"] is not None

    second = client.get(
        f"/api/dev/analytics/events?event_type=student.created&limit=1&cursor={first_body['next_cursor']}",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_a),
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["tenant_id"] == tenant_a
    assert second_body["total"] == 1
    assert second_body["items"][0]["tenant_id"] == tenant_a


def test_developer_analytics_cursor_cannot_be_reused_across_tenants(reset_shared_state) -> None:
    tenant_a = _tenant("dev-events-cursor-a")
    tenant_b = _tenant("dev-events-cursor-b")
    app_a = _installed_analytics_app(tenant_id=tenant_a)
    app_b = _installed_analytics_app(tenant_id=tenant_b)

    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=8301)
    _emit_analytics_event(tenant_id=tenant_a, event_type="student.created", event_id=8302)
    _emit_analytics_event(tenant_id=tenant_b, event_type="student.created", event_id=8303)

    first = client.get(
        "/api/dev/analytics/events?event_type=student.created&limit=1",
        headers=_developer_headers(app_a["app_key"], app_a["app_secret"], tenant_a),
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["next_cursor"] is not None

    cross_tenant = client.get(
        f"/api/dev/analytics/events?event_type=student.created&limit=1&cursor={first_body['next_cursor']}",
        headers=_developer_headers(app_b["app_key"], app_b["app_secret"], tenant_b),
    )
    assert cross_tenant.status_code == 400, cross_tenant.text