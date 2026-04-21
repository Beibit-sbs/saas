import os

from tests.conftest import ADMIN_HEADERS, client
from app.modules.backup import service as backup_service
from app.modules.integrations import service as integrations_service
from app.modules.jobs import service as jobs_service
from app.modules.jobs import worker as jobs_worker


def test_backup_settings_reject_path_outside_allowed_roots() -> None:
    payload = {
        "active_profile": "main",
        "profiles": [
            {
                "id": "main",
                "label": "Main",
                "path": "/etc",
            }
        ],
    }

    response = client.put("/api/admin/backups/settings", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 400


def test_backup_settings_and_run_success(monkeypatch, tmp_path) -> None:
    backup_service._backup_history.clear()
    jobs_service.clear_jobs_state()

    profile_path = tmp_path / "db-backups"
    payload = {
        "active_profile": "localtest",
        "retention_days": 0,
        "retention_min_files": 0,
        "profiles": [
            {
                "id": "localtest",
                "label": "Local Test",
                "path": str(profile_path),
            }
        ],
    }

    monkeypatch.setenv("BACKUP_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setattr(integrations_service, "_use_database", lambda: False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    def fake_pg_dump(db_url: str, output_path: str) -> None:
        assert db_url.startswith("postgresql://")
        with open(output_path, "wb") as fh:
            fh.write(b"fake-backup")

    def fake_pg_restore(db_url: str, input_path: str) -> None:
        assert db_url.startswith("postgresql://")
        assert input_path.endswith(".dump")

    monkeypatch.setattr(backup_service, "_run_pg_dump_command", fake_pg_dump)
    monkeypatch.setattr(backup_service, "_run_pg_restore_command", fake_pg_restore)

    save_response = client.put("/api/admin/backups/settings", json=payload, headers=ADMIN_HEADERS)
    assert save_response.status_code == 200
    assert save_response.json()["active_profile"] == "localtest"

    monkeypatch.setenv("DATABASE_URL", "postgresql://app:change_me@db:5432/app")

    run_response = client.post("/api/admin/backups/run", headers=ADMIN_HEADERS)
    assert run_response.status_code == 200
    assert run_response.json()["job"]["status"] == "queued"

    processed = jobs_worker.execute_next_queued_job()
    assert processed is not None
    assert processed["status"] == "succeeded"

    history_response = client.get("/api/admin/backups/history", headers=ADMIN_HEADERS)
    assert history_response.status_code == 200
    assert len(history_response.json()["jobs"]) >= 1

    candidates_response = client.get(
        "/api/admin/backups/restore-candidates?profile_id=localtest",
        headers=ADMIN_HEADERS,
    )
    assert candidates_response.status_code == 200
    candidates = candidates_response.json()["candidates"]
    assert len(candidates) >= 1

    dry_run_response = client.post(
        "/api/admin/backups/restore",
        headers=ADMIN_HEADERS,
        json={
            "profile_id": "localtest",
            "file_name": candidates[0]["file_name"],
            "dry_run": True,
        },
    )
    assert dry_run_response.status_code == 200
    assert dry_run_response.json()["job"]["status"] == "planned"

    run_restore_response = client.post(
        "/api/admin/backups/restore",
        headers=ADMIN_HEADERS,
        json={
            "profile_id": "localtest",
            "file_name": candidates[0]["file_name"],
            "dry_run": False,
            "confirm_text": "RESTORE",
        },
    )
    assert run_restore_response.status_code == 200
    assert run_restore_response.json()["job"]["status"] == "completed"

    old_dump = profile_path / "old.dump"
    old_dump.write_bytes(b"old-backup")
    os.utime(old_dump, (1, 1))

    retention_plan = client.post(
        "/api/admin/backups/retention/apply",
        headers=ADMIN_HEADERS,
        json={"profile_id": "localtest", "dry_run": True},
    )
    assert retention_plan.status_code == 200
    assert retention_plan.json()["job"]["job_type"] == "retention"
    assert retention_plan.json()["job"]["deleted_count"] >= 1

    retention_run = client.post(
        "/api/admin/backups/retention/apply",
        headers=ADMIN_HEADERS,
        json={"profile_id": "localtest", "dry_run": False},
    )
    assert retention_run.status_code == 200
    assert retention_run.json()["job"]["status"] == "completed"
    assert old_dump.exists() is False

    # Keep autouse reset in in-memory mode; otherwise teardown helpers can
    # attempt DB-backed cleanup against the compose-only test DSN above.
    monkeypatch.delenv("DATABASE_URL", raising=False)
