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

    def fake_backup_run(actor: str, tenant_id: int | None = None):
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


def test_jobs_queue_and_history_endpoints() -> None:
    jobs_service.clear_jobs_state()

    queued = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "queue.queued", "payload": {}, "max_retries": 2},
    )
    assert queued.status_code == 200, queued.text
    queued_id = int(queued.json()["job"]["id"])

    running = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "queue.running", "payload": {}, "max_retries": 2},
    )
    assert running.status_code == 200, running.text
    running_id = int(running.json()["job"]["id"])
    assert jobs_service.mark_job_running(running_id) is not None

    failed = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "queue.failed", "payload": {}, "max_retries": 2},
    )
    assert failed.status_code == 200, failed.text
    failed_id = int(failed.json()["job"]["id"])
    assert jobs_service.mark_job_running(failed_id) is not None
    assert jobs_service.mark_job_failed(failed_id, "boom") is not None

    queue_default = client.get("/api/admin/jobs/queue", headers=ADMIN_HEADERS)
    assert queue_default.status_code == 200, queue_default.text
    queue_ids = {int(item["id"]) for item in queue_default.json()["jobs"]}
    assert queued_id in queue_ids
    assert running_id in queue_ids
    assert failed_id not in queue_ids

    queue_failed = client.get("/api/admin/jobs/queue/failed", headers=ADMIN_HEADERS)
    assert queue_failed.status_code == 200, queue_failed.text
    failed_ids = {int(item["id"]) for item in queue_failed.json()["jobs"]}
    assert failed_id in failed_ids

    history = client.get("/api/admin/jobs/history", headers=ADMIN_HEADERS)
    assert history.status_code == 200, history.text
    history_statuses = {item["status"] for item in history.json()["jobs"]}
    assert "failed" in history_statuses
    assert "queued" not in history_statuses

    unsupported = client.get("/api/admin/jobs/queue/unknown-view", headers=ADMIN_HEADERS)
    assert unsupported.status_code == 404


def test_enqueue_job_deduplicates_active_same_payload() -> None:
    jobs_service.clear_jobs_state()

    first = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "backup.run", "payload": {"source": "dedup-test"}, "max_retries": 1},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "backup.run", "payload": {"source": "dedup-test"}, "max_retries": 1},
    )
    assert second.status_code == 200, second.text

    first_id = int(first.json()["job"]["id"])
    second_id = int(second.json()["job"]["id"])
    assert first_id == second_id

    listed = client.get("/api/admin/jobs/queue", headers=ADMIN_HEADERS)
    assert listed.status_code == 200, listed.text
    queue_ids = {int(item["id"]) for item in listed.json()["jobs"]}
    assert queue_ids == {first_id}


def test_enqueue_job_allows_same_payload_after_terminal_status() -> None:
    jobs_service.clear_jobs_state()

    first = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "report.generate", "payload": {"source": "dedup-terminal"}, "max_retries": 1},
    )
    assert first.status_code == 200, first.text
    first_id = int(first.json()["job"]["id"])

    processed = jobs_worker.execute_next_queued_job()
    assert processed is not None
    assert int(processed["id"]) == first_id
    assert processed["status"] == "succeeded"

    second = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "report.generate", "payload": {"source": "dedup-terminal"}, "max_retries": 1},
    )
    assert second.status_code == 200, second.text
    second_id = int(second.json()["job"]["id"])
    assert second_id != first_id


def test_create_job_rejects_de_scoped_job_types() -> None:
    jobs_service.clear_jobs_state()

    for job_type in ("sync", "ldap.sync", "ai.generate"):
        response = client.post(
            "/api/admin/jobs",
            headers=ADMIN_HEADERS,
            json={"job_type": job_type, "payload": {}, "max_retries": 1},
        )
        assert response.status_code == 400, response.text
        assert "de-scoped" in response.json()["detail"]
