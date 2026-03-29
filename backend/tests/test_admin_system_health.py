from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


def test_admin_system_health_requires_authentication() -> None:
    response = client.get("/api/admin/system/health")
    assert response.status_code == 401


def test_admin_system_health_requires_permission() -> None:
    response = client.get(
        "/api/admin/system/health",
        headers={
            "Authorization": f"Bearer {create_access_token('student.001', ['student'], 'test', tenant_id=1)}",
            "x-user-roles": "admin",
        },
    )
    assert response.status_code == 403


def test_admin_system_health_returns_expected_shape() -> None:
    response = client.get("/api/admin/system/health", headers=ADMIN_HEADERS)
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"

    assert isinstance(body.get("services"), dict)
    assert isinstance(body.get("metrics"), dict)
    assert isinstance(body.get("queues"), dict)
    assert isinstance(body.get("disk"), dict)

    services = body["services"]
    assert services.get("backend") == "ok"
    assert services.get("api") == "ok"

    metrics = body["metrics"]
    assert "generated_at" in metrics
    assert isinstance(metrics.get("local_users_count"), int)
    assert isinstance(metrics.get("roles_count"), int)
    assert isinstance(metrics.get("assignments_count"), int)
    assert isinstance(metrics.get("languages_count"), int)

    queues = body["queues"]
    assert isinstance(queues.get("backup_jobs_total"), int)
    assert isinstance(queues.get("backup_jobs_running"), int)
    assert isinstance(queues.get("audit_events_recent"), int)

    disk = body["disk"]
    assert disk.get("path") == "/"
    assert isinstance(disk.get("total_bytes"), int)
    assert isinstance(disk.get("used_bytes"), int)
    assert isinstance(disk.get("free_bytes"), int)
    assert isinstance(disk.get("usage_percent"), (int, float))
