"""Phase XII-XII4: Model Evaluation router tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/model-evaluation"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="me@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["model_evaluation.read", "model_evaluation.write"],
        )
    )
}

_RUN_ID: list[str] = []


def test_health_ok() -> None:
    response = client.get(f"{BASE}/health", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["module"] == "model_evaluation"


def test_create_eval_run() -> None:
    payload = {
        "model_name": "gpt-4o-mini",
        "eval_set_name": "academic-qa-v1",
        "metric_names": ["accuracy", "latency_ms"],
        "notes": "Baseline evaluation",
    }
    response = client.post(f"{BASE}/runs", headers=HEADERS, json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["model_name"] == "gpt-4o-mini"
    _RUN_ID.append(body["run_id"])


def test_list_runs() -> None:
    response = client.get(f"{BASE}/runs", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_submit_results_and_leaderboard() -> None:
    if not _RUN_ID:
        test_create_eval_run()
    run_id = _RUN_ID[0]

    # Submit results
    response = client.post(
        f"{BASE}/runs/{run_id}/results",
        headers=HEADERS,
        json={
            "run_id": run_id,
            "metrics": [
                {"metric_name": "accuracy", "value": 0.92, "unit": "ratio"},
                {"metric_name": "latency_ms", "value": 320.0, "unit": "ms"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["metrics"]) == 2

    # Check leaderboard
    lb = client.get(f"{BASE}/leaderboard", headers=HEADERS)
    assert lb.status_code == 200, lb.text
    entries = lb.json()
    assert isinstance(entries, list)
    assert any(e["model_name"] == "gpt-4o-mini" for e in entries)
    assert entries[0]["rank"] == 1
