from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.jobs import service as jobs_service


def _tenant_headers(tenant_id: int, base_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(base_headers or ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={
            "slug": "tenant-b-jobs",
            "name": "Tenant B Jobs",
            "status": "active",
        },
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_tenant_b_cannot_see_tenant_a_jobs() -> None:
    jobs_service.clear_jobs_state()
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    created = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "report.generate", "payload": {"kind": "a"}, "max_retries": 1},
    )
    assert created.status_code == 200, created.text
    job_id = int(created.json()["job"]["id"])

    list_tenant_b = client.get(
        "/api/admin/jobs",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert list_tenant_b.status_code == 200, list_tenant_b.text
    assert all(int(item["tenant_id"]) == tenant_b_id for item in list_tenant_b.json()["jobs"])

    get_cross = client.get(
        f"/api/admin/jobs/{job_id}",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert get_cross.status_code == 404


def test_platform_admin_can_use_tenant_override() -> None:
    jobs_service.clear_jobs_state()
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    created = client.post(
        f"/api/admin/jobs?tenant_id={tenant_b_id}",
        headers=platform_headers,
        json={"job_type": "audit.export", "payload": {"format": "json"}, "max_retries": 2},
    )
    assert created.status_code == 200, created.text
    job_id = int(created.json()["job"]["id"])

    listed = client.get(f"/api/admin/jobs?tenant_id={tenant_b_id}", headers=platform_headers)
    assert listed.status_code == 200, listed.text
    assert any(int(item["id"]) == job_id for item in listed.json()["jobs"])


def test_tenant_admin_override_returns_404() -> None:
    tenant_b_id = _create_tenant_b()

    response = client.get(f"/api/admin/jobs?tenant_id={tenant_b_id}", headers=ADMIN_HEADERS)
    assert response.status_code == 404
