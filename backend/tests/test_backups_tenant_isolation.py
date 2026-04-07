from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.integrations import service as integrations_service


def _tenant_headers(tenant_id: int, base_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(base_headers or ADMIN_HEADERS)
    headers["X-Tenant-ID"] = str(tenant_id)
    return headers


def _create_tenant_b() -> int:
    response = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b-backups", "name": "Tenant B Backups", "status": "active"},
    )
    assert response.status_code == 200, response.text
    return int(response.json()["tenant"]["id"])


def test_backup_settings_and_history_are_isolated_per_tenant(monkeypatch, tmp_path) -> None:
    tenant_b_id = _create_tenant_b()
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"], tenant_id=tenant_b_id)

    monkeypatch.setenv("BACKUP_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setattr(integrations_service, "_use_database", lambda: False)

    tenant_a_profile = tmp_path / "tenant-a"
    tenant_b_profile = tmp_path / "tenant-b"
    tenant_a_profile.mkdir(parents=True, exist_ok=True)
    tenant_b_profile.mkdir(parents=True, exist_ok=True)
    (tenant_b_profile / "tenant-b.dump").write_bytes(b"tenant-b")

    tenant_a_payload = {
        "active_profile": "tenanta",
        "retention_days": 14,
        "retention_min_files": 1,
        "profiles": [{"id": "tenanta", "label": "Tenant A", "path": str(tenant_a_profile)}],
    }
    tenant_b_payload = {
        "active_profile": "tenantb",
        "retention_days": 7,
        "retention_min_files": 0,
        "profiles": [{"id": "tenantb", "label": "Tenant B", "path": str(tenant_b_profile)}],
    }

    tenant_a_save = client.put("/api/admin/backups/settings", headers=ADMIN_HEADERS, json=tenant_a_payload)
    tenant_b_save = client.put(
        "/api/admin/backups/settings",
        headers=_tenant_headers(tenant_b_id, platform_headers),
        json=tenant_b_payload,
    )
    assert tenant_a_save.status_code == 200, tenant_a_save.text
    assert tenant_b_save.status_code == 200, tenant_b_save.text

    tenant_b_retention_plan = client.post(
        "/api/admin/backups/retention/apply",
        headers=_tenant_headers(tenant_b_id, platform_headers),
        json={
            "profile_id": "tenantb",
            "dry_run": True,
        },
    )
    assert tenant_b_retention_plan.status_code == 200, tenant_b_retention_plan.text

    tenant_a_settings = client.get("/api/admin/backups/settings", headers=ADMIN_HEADERS)
    tenant_b_settings = client.get(
        "/api/admin/backups/settings",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert tenant_a_settings.status_code == 200, tenant_a_settings.text
    assert tenant_b_settings.status_code == 200, tenant_b_settings.text
    assert tenant_a_settings.json()["active_profile"] == "tenanta"
    assert tenant_b_settings.json()["active_profile"] == "tenantb"

    tenant_a_history = client.get("/api/admin/backups/history", headers=ADMIN_HEADERS)
    tenant_b_history = client.get(
        "/api/admin/backups/history",
        headers=_tenant_headers(tenant_b_id, platform_headers),
    )
    assert tenant_a_history.status_code == 200, tenant_a_history.text
    assert tenant_b_history.status_code == 200, tenant_b_history.text
    assert tenant_a_history.json()["jobs"] == []
    assert len(tenant_b_history.json()["jobs"]) == 1