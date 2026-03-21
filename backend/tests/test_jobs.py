from tests.conftest import ADMIN_HEADERS, client
from app.modules.jobs import service as jobs_service
from app.modules.jobs import worker as jobs_worker


def test_create_list_retry_cancel_jobs() -> None:
    jobs_service.clear_jobs_state()

    created = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "report.generate", "payload": {"scope": "daily"}, "max_retries": 2},
    )
    assert created.status_code == 200, created.text
    body = created.json()["job"]
    assert body["status"] == "queued"
    job_id = int(body["id"])

    listed = client.get("/api/admin/jobs", headers=ADMIN_HEADERS)
    assert listed.status_code == 200
    assert any(int(item["id"]) == job_id for item in listed.json()["jobs"])

    running = jobs_service.mark_job_running(job_id)
    assert running is not None
    failed = jobs_service.mark_job_failed(job_id, "boom")
    assert failed is not None
    assert failed["status"] == "failed"

    retried = client.post(f"/api/admin/jobs/{job_id}/retry", headers=ADMIN_HEADERS)
    assert retried.status_code == 200, retried.text
    assert retried.json()["job"]["status"] == "queued"
    assert retried.json()["job"]["retry_count"] == 1

    cancelled = client.post(f"/api/admin/jobs/{job_id}/cancel", headers=ADMIN_HEADERS)
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["job"]["status"] == "cancelled"


def test_worker_executes_backup_run_job_end_to_end(monkeypatch) -> None:
    jobs_service.clear_jobs_state()

    def fake_backup_run(actor: str):
        return {
            "job_id": "backup-001",
            "job_type": "backup",
            "status": "completed",
            "profile_id": "local",
            "file_path": "/tmp/app-backups/local/fake.dump",
            "size_bytes": 128,
            "started_at": "2026-01-01T00:00:00+00:00",
            "finished_at": "2026-01-01T00:00:01+00:00",
            "actor": actor,
        }

    monkeypatch.setattr(jobs_worker, "run_backup_now", fake_backup_run)

    created = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "backup.run", "payload": {}, "max_retries": 3},
    )
    assert created.status_code == 200, created.text
    job_id = int(created.json()["job"]["id"])

    processed = jobs_worker.execute_next_queued_job()
    assert processed is not None
    assert int(processed["id"]) == job_id
    assert processed["status"] == "succeeded"
    assert processed["result_json"]["job_type"] == "backup.run"

    details = client.get(f"/api/admin/jobs/{job_id}", headers=ADMIN_HEADERS)
    assert details.status_code == 200, details.text
    assert details.json()["job"]["status"] == "succeeded"
