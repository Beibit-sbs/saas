from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.students import service as students_service
from app.platform.developer.repository import DeveloperRepository
from app.platform.developer.service import DeveloperPlatformService
from app.platform.tenant import service as tenant_service
from tests.conftest import ADMIN_HEADERS, client


def _tenant(prefix: str = "dev-app") -> int:
    row = tenant_service.create_tenant(f"{prefix}-{uuid4().hex[:8]}", f"{prefix} tenant")
    return int(row["tenant_id"])


def _developer_headers(app_key: str, app_secret: str, tenant_id: int) -> dict[str, str]:
    del tenant_id
    return {
        "X-App-Key": app_key,
        "X-App-Secret": app_secret,
    }


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

    ok_resp = client.get(
        "/api/dev/analytics/kpi",
        headers=_developer_headers(app["app_key"], app["app_secret"], tenant_id),
    )
    assert ok_resp.status_code == 200, ok_resp.text
    assert ok_resp.json()["tenant_id"] == tenant_id