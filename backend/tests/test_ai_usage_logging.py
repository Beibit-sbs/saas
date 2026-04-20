from tests.conftest import ADMIN_HEADERS, client

from app.modules.ai_gateway import service as ai_service
from app.modules.observability.metrics import clear_metrics_state, render_metrics


def test_ai_usage_log_records_success(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    upsert_response = client.put(
        "/api/admin/ai/models/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "OpenAI Default Chat",
            "enabled": True,
            "priority": 100,
        },
    )
    assert upsert_response.status_code == 200

    def fake_request_json(method: str, url: str, *, headers, params=None, payload=None):
        return {
            "id": "chatcmpl-1",
            "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

    monkeypatch.setattr(ai_service, "_request_json", fake_request_json)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 200

    logs = ai_service.list_usage_logs(limit=10, tenant_id=1)
    assert logs
    assert logs[0]["outcome"] == "success"
    assert logs[0]["actor"] == "owner@example.com"
    assert logs[0]["provider"] == "openai"
    assert logs[0]["model_key"] == "openai.default.chat"
    assert logs[0]["total_tokens"] == 5


def test_ai_usage_log_records_failure(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    upsert_response = client.put(
        "/api/admin/ai/models/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "OpenAI Default Chat",
            "enabled": True,
            "priority": 100,
        },
    )
    assert upsert_response.status_code == 200

    def fake_error(*args, **kwargs):
        raise ai_service.AIProviderExecutionError("provider failed")

    monkeypatch.setattr(ai_service._ADAPTERS["openai"], "execute_chat", fake_error)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 502

    logs = ai_service.list_usage_logs(limit=10, tenant_id=1)
    assert logs
    assert logs[0]["outcome"] == "failed"
    assert logs[0]["failure_reason"]


def test_ai_usage_summary_endpoint_aggregates_cost_and_latency(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "degraded",
                "latency_ms": 200,
                "total_tokens": 0,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "outcome": "failed",
                "latency_ms": 150,
                "total_tokens": 50,
            },
        ],
    )

    response = client.get("/api/admin/ai/usage/summary?limit=100", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["tenant_id"] == 1
    assert body["requests_total"] == 3
    assert body["success_count"] == 1
    assert body["degraded_count"] == 1
    assert body["failed_count"] == 1
    assert body["total_tokens"] == 150
    assert body["avg_latency_ms"] == 150.0
    assert body["estimated_cost_usd"] == 0.00012

    assert len(body["models"]) == 2
    openai_row = next(item for item in body["models"] if item["model_key"] == "openai.default.chat")
    assert openai_row["requests_total"] == 2
    assert openai_row["success_count"] == 1
    assert openai_row["degraded_count"] == 1
    assert openai_row["failed_count"] == 0


def test_ai_usage_budget_and_anomaly_contract(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()

    budget_put = client.put(
        "/api/admin/ai/usage/budget",
        headers=ADMIN_HEADERS,
        json={
            "budget_limit_usd": 0.001,
            "alert_threshold_pct": 80,
            "hard_cap": True,
        },
    )
    assert budget_put.status_code == 200, budget_put.text
    budget_body = budget_put.json()
    assert budget_body["budget_limit_usd"] == 0.001
    assert budget_body["hard_cap"] is True

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 120,
                "total_tokens": 5000,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
        ],
    )

    summary_resp = client.get("/api/admin/ai/usage/summary?limit=100", headers=ADMIN_HEADERS)
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()

    assert summary["budget_limit_usd"] == 0.001
    assert summary["budget_hard_cap"] is True
    assert summary["budget_alert"] is True
    assert summary["budget_utilization_pct"] >= 80.0
    assert summary["anomaly_detected"] is True
    assert summary["anomaly_reason"] in {"z_score_spike", "flat_baseline_spike"}


def test_ai_chat_hard_cap_budget_blocks_runtime_execution(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    upsert_response = client.put(
        "/api/admin/ai/models/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "display_name": "OpenAI Default Chat",
            "enabled": True,
            "priority": 100,
        },
    )
    assert upsert_response.status_code == 200

    budget_put = client.put(
        "/api/admin/ai/usage/budget",
        headers=ADMIN_HEADERS,
        json={
            "budget_limit_usd": 0.0001,
            "alert_threshold_pct": 80,
            "hard_cap": True,
        },
    )
    assert budget_put.status_code == 200, budget_put.text

    ai_service._record_usage_log(
        tenant_id=1,
        actor="owner@example.com",
        provider="openai",
        model_key="openai.default.chat",
        provider_model_id="gpt-4o-mini",
        outcome="success",
        latency_ms=100,
        input_tokens=200,
        output_tokens=200,
        total_tokens=400,
        failure_reason=None,
        correlation_id="seed-budget-usage",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("provider adapter must not be called when hard cap blocks")

    monkeypatch.setattr(ai_service._ADAPTERS["openai"], "execute_chat", fail_if_called)

    response = client.post(
        "/api/ai/chat",
        headers=ADMIN_HEADERS,
        json={
            "model": "openai.default.chat",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 1024,
        },
    )
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "ai_budget_hard_cap_exceeded"

    logs = ai_service.list_usage_logs(limit=20, tenant_id=1)
    assert logs
    assert logs[0]["outcome"] == "budget_blocked"


def test_ai_usage_budget_scopes_status_contract(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()

    tenant_budget = client.put(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        json={
            "scope": "tenant",
            "scope_id": None,
            "budget_limit_usd": 0.002,
            "alert_threshold_pct": 75,
            "hard_cap": False,
        },
    )
    assert tenant_budget.status_code == 200, tenant_budget.text
    assert tenant_budget.json()["scope"] == "tenant"

    department_budget = client.put(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        json={
            "scope": "department",
            "scope_id": "engineering",
            "budget_limit_usd": 0.001,
            "alert_threshold_pct": 60,
            "hard_cap": True,
        },
    )
    assert department_budget.status_code == 200, department_budget.text
    dep_row = department_budget.json()
    assert dep_row["scope"] == "department"
    assert dep_row["scope_id"] == "engineering"

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 1000,
            }
        ],
    )

    status_resp = client.get("/api/admin/ai/usage/budgets/status", headers=ADMIN_HEADERS)
    assert status_resp.status_code == 200, status_resp.text
    rows = status_resp.json()
    assert rows

    tenant_row = next(item for item in rows if item["scope"] == "tenant")
    assert tenant_row["budget_limit_usd"] == 0.002
    assert tenant_row["alert_threshold_pct"] == 75
    assert tenant_row["current_cost_usd"] > 0.0
    assert tenant_row["hard_cap"] is False

    dep_status_row = next(
        item for item in rows if item["scope"] == "department" and item["scope_id"] == "engineering"
    )
    assert dep_status_row["budget_limit_usd"] == 0.001
    assert dep_status_row["alert_threshold_pct"] == 60
    assert dep_status_row["hard_cap"] is True


def test_ai_usage_budget_status_is_scope_aware_for_user_and_department(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()

    user_budget = client.put(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        json={
            "scope": "user",
            "scope_id": "owner@example.com",
            "budget_limit_usd": 0.001,
            "alert_threshold_pct": 70,
            "hard_cap": False,
        },
    )
    assert user_budget.status_code == 200, user_budget.text

    department_budget = client.put(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        json={
            "scope": "department",
            "scope_id": "engineering",
            "budget_limit_usd": 0.001,
            "alert_threshold_pct": 70,
            "hard_cap": False,
        },
    )
    assert department_budget.status_code == 200, department_budget.text

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "actor": "owner@example.com",
                "department": "engineering",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 500,
            },
            {
                "tenant_id": tenant_id,
                "actor": "other@example.com",
                "department": "sales",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 500,
            },
        ],
    )

    status_resp = client.get("/api/admin/ai/usage/budgets/status", headers=ADMIN_HEADERS)
    assert status_resp.status_code == 200, status_resp.text
    rows = status_resp.json()

    user_row = next(item for item in rows if item["scope"] == "user" and item["scope_id"] == "owner@example.com")
    department_row = next(item for item in rows if item["scope"] == "department" and item["scope_id"] == "engineering")
    tenant_row = next(item for item in rows if item["scope"] == "tenant")

    assert user_row["current_cost_usd"] == 0.0004
    assert department_row["current_cost_usd"] == 0.0004
    assert tenant_row["current_cost_usd"] == 0.0008


def test_ai_usage_budget_scoped_list_and_delete_contract() -> None:
    ai_service.clear_ai_gateway_state()

    put_department = client.put(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        json={
            "scope": "department",
            "scope_id": "engineering",
            "budget_limit_usd": 0.003,
            "alert_threshold_pct": 70,
            "hard_cap": True,
        },
    )
    assert put_department.status_code == 200, put_department.text

    list_before = client.get("/api/admin/ai/usage/budgets", headers=ADMIN_HEADERS)
    assert list_before.status_code == 200, list_before.text
    rows_before = list_before.json()
    assert any(item["scope"] == "tenant" and item["scope_id"] is None for item in rows_before)
    assert any(item["scope"] == "department" and item["scope_id"] == "engineering" for item in rows_before)

    delete_response = client.delete(
        "/api/admin/ai/usage/budgets?scope=department&scope_id=engineering",
        headers=ADMIN_HEADERS,
    )
    assert delete_response.status_code == 200, delete_response.text
    deleted = delete_response.json()
    assert deleted["scope"] == "department"
    assert deleted["scope_id"] == "engineering"

    list_after = client.get("/api/admin/ai/usage/budgets", headers=ADMIN_HEADERS)
    assert list_after.status_code == 200, list_after.text
    rows_after = list_after.json()
    assert not any(item["scope"] == "department" and item["scope_id"] == "engineering" for item in rows_after)
    assert any(item["scope"] == "tenant" and item["scope_id"] is None for item in rows_after)


def test_ai_usage_cost_by_user_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "actor": "owner@example.com",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 120,
                "total_tokens": 300,
            },
            {
                "tenant_id": tenant_id,
                "actor": "owner@example.com",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "degraded",
                "latency_ms": 180,
                "total_tokens": 200,
            },
            {
                "tenant_id": tenant_id,
                "actor": "other@example.com",
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "outcome": "failed",
                "latency_ms": 90,
                "total_tokens": 100,
            },
        ],
    )

    response = client.get("/api/admin/ai/usage/by-user?limit=100", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 2

    owner_row = next(item for item in rows if item["actor"] == "owner@example.com")
    assert owner_row["requests_total"] == 2
    assert owner_row["success_count"] == 1
    assert owner_row["degraded_count"] == 1
    assert owner_row["failed_count"] == 0
    assert owner_row["total_tokens"] == 500
    assert owner_row["estimated_cost_usd"] == 0.0004


def test_ai_usage_cost_by_department_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "department": "engineering",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 400,
            },
            {
                "tenant_id": tenant_id,
                "department": "engineering",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "failed",
                "latency_ms": 110,
                "total_tokens": 0,
            },
            {
                "tenant_id": tenant_id,
                "department": "sales",
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "outcome": "success",
                "latency_ms": 130,
                "total_tokens": 100,
            },
        ],
    )

    response = client.get("/api/admin/ai/usage/by-department?limit=100", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 2

    engineering_row = next(item for item in rows if item["department"] == "engineering")
    assert engineering_row["requests_total"] == 2
    assert engineering_row["success_count"] == 1
    assert engineering_row["failed_count"] == 1
    assert engineering_row["total_tokens"] == 400
    assert engineering_row["estimated_cost_usd"] == 0.00032


def test_ai_usage_cost_trend_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T10:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 500,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T09:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 110,
                "total_tokens": 500,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-19T11:00:00+00:00",
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "outcome": "failed",
                "latency_ms": 90,
                "total_tokens": 250,
            },
        ],
    )

    response = client.get("/api/admin/ai/usage/trend?days=7", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 2

    day20 = next(item for item in rows if item["date"] == "2026-04-20")
    assert day20["requests_total"] == 2
    assert day20["total_tokens"] == 1000
    assert day20["estimated_cost_usd"] == 0.0008


def test_ai_usage_cost_daily_aggregation_contract(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T10:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 700,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T09:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 110,
                "total_tokens": 300,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T08:00:00+00:00",
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "outcome": "success",
                "latency_ms": 95,
                "total_tokens": 500,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-19T10:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "failed",
                "latency_ms": 90,
                "total_tokens": 250,
            },
        ],
    )

    refresh_response = client.post(
        "/api/admin/ai/usage/daily-aggregation/refresh?days=7&limit=100",
        headers=ADMIN_HEADERS,
    )
    assert refresh_response.status_code == 200, refresh_response.text
    rows = refresh_response.json()
    assert len(rows) == 3

    day20_openai = next(
        item
        for item in rows
        if item["date"] == "2026-04-20"
        and item["provider"] == "openai"
        and item["model_key"] == "openai.default.chat"
    )
    assert day20_openai["requests_total"] == 2
    assert day20_openai["total_tokens"] == 1000
    assert day20_openai["estimated_cost_usd"] == 0.0008

    list_response = client.get("/api/admin/ai/usage/daily-aggregation?days=7", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200, list_response.text
    listed_rows = list_response.json()
    assert len(listed_rows) == 3


def test_ai_usage_cost_projection_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T10:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 1000,
            }
        ],
    )

    response = client.get("/api/admin/ai/usage/projection", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["period"] == "daily"
    assert body["elapsed_requests"] == 1
    assert body["current_cost_usd"] == 0.0008
    assert body["projected_cost_usd"] == 0.0016
    assert body["projection_basis"] == "daily_linear_samplex2"


def test_ai_usage_cost_anomalies_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T10:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 5000,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T09:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T08:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T07:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T06:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "timestamp": "2026-04-20T05:00:00+00:00",
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
        ],
    )

    response = client.get("/api/admin/ai/usage/anomalies?limit=10", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert rows

    first = rows[0]
    assert first["model_key"] == "openai.default.chat"
    assert first["provider"] == "openai"
    assert first["total_tokens"] == 5000
    assert first["estimated_cost_usd"] == 0.004
    assert first["anomaly_reason"] in {"flat_baseline_spike", "z_score_spike"}


def test_ai_usage_token_price_catalog_contract() -> None:
    ai_service.clear_ai_gateway_state()

    put_response = client.put(
        "/api/admin/ai/prices/openai/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "input_price_per_1k": 0.001,
            "output_price_per_1k": 0.002,
        },
    )
    assert put_response.status_code == 200, put_response.text
    put_body = put_response.json()
    assert put_body["provider"] == "openai"
    assert put_body["model_key"] == "openai.default.chat"
    assert put_body["input_price_per_1k"] == 0.001
    assert put_body["output_price_per_1k"] == 0.002

    list_response = client.get("/api/admin/ai/prices", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200, list_response.text
    rows = list_response.json()
    assert rows
    row = rows[0]
    assert row["provider"] == "openai"
    assert row["model_key"] == "openai.default.chat"


def test_ai_slo_policy_and_compliance_contract(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()

    put_response = client.put(
        "/api/admin/ai/slo/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "p95_latency_ms": 200,
            "max_error_rate_pct": 20.0,
        },
    )
    assert put_response.status_code == 200, put_response.text
    put_body = put_response.json()
    assert put_body["model_key"] == "openai.default.chat"
    assert put_body["p95_latency_ms"] == 200

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 100,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "failed",
                "latency_ms": 180,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 220,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 150,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 190,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 140,
                "total_tokens": 100,
            },
        ],
    )

    compliance_response = client.get("/api/admin/ai/slo/compliance?limit=100", headers=ADMIN_HEADERS)
    assert compliance_response.status_code == 200, compliance_response.text
    rows = compliance_response.json()
    assert rows
    row = rows[0]
    assert row["model_key"] == "openai.default.chat"
    assert row["p95_latency_ms_target"] == 200
    assert row["max_error_rate_pct_target"] == 20.0
    assert row["error_rate_pct_observed"] == 16.67
    assert row["error_rate_compliant"] is True


def test_ai_slo_violations_contract(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()

    put_response = client.put(
        "/api/admin/ai/slo/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "p95_latency_ms": 100,
            "max_error_rate_pct": 10.0,
        },
    )
    assert put_response.status_code == 200, put_response.text

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 210,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "failed",
                "latency_ms": 205,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "outcome": "success",
                "latency_ms": 80,
                "total_tokens": 100,
            },
        ],
    )

    response = client.get("/api/admin/ai/slo/violations?limit=100", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 1

    row = rows[0]
    assert row["model_key"] == "openai.default.chat"
    assert row["compliant"] is False
    assert row["latency_compliant"] is False
    assert row["error_rate_compliant"] is False
    assert row["violation_types"] == ["latency", "error_rate"]


def test_ai_cost_governance_prometheus_metrics_contract(monkeypatch) -> None:
    ai_service.clear_ai_gateway_state()
    clear_metrics_state()

    budget_put = client.put(
        "/api/admin/ai/usage/budget",
        headers=ADMIN_HEADERS,
        json={
            "budget_limit_usd": 0.0001,
            "alert_threshold_pct": 80,
            "hard_cap": True,
        },
    )
    assert budget_put.status_code == 200, budget_put.text

    slo_put = client.put(
        "/api/admin/ai/slo/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={
            "p95_latency_ms": 100,
            "max_error_rate_pct": 10.0,
        },
    )
    assert slo_put.status_code == 200, slo_put.text

    monkeypatch.setattr(
        ai_service,
        "list_usage_logs",
        lambda limit, tenant_id: [
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 210,
                "total_tokens": 5000,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "failed",
                "latency_ms": 205,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 120,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 130,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 140,
                "total_tokens": 100,
            },
            {
                "tenant_id": tenant_id,
                "model_key": "openai.default.chat",
                "provider": "openai",
                "outcome": "success",
                "latency_ms": 150,
                "total_tokens": 100,
            },
        ],
    )

    summary_response = client.get("/api/admin/ai/usage/summary?limit=100", headers=ADMIN_HEADERS)
    assert summary_response.status_code == 200, summary_response.text

    budget_status_response = client.get("/api/admin/ai/usage/budgets/status", headers=ADMIN_HEADERS)
    assert budget_status_response.status_code == 200, budget_status_response.text

    slo_compliance_response = client.get("/api/admin/ai/slo/compliance?limit=100", headers=ADMIN_HEADERS)
    assert slo_compliance_response.status_code == 200, slo_compliance_response.text

    metrics = render_metrics()

    assert 'ai_cost_total_usd{tenant_id="1",provider="openai",model="openai.default.chat",period="daily"}' in metrics
    assert 'ai_budget_utilization_pct{tenant_id="1",scope="tenant",scope_id="-"}' in metrics
    assert 'ai_budget_exceeded_total{tenant_id="1",scope="tenant"} 1' in metrics
    assert 'ai_cost_anomaly_detected_total{tenant_id="1"} 1' in metrics
    assert 'ai_slo_compliance_pct{model="openai.default.chat",metric="p95_latency"} 0.00' in metrics
    assert 'ai_slo_compliance_pct{model="openai.default.chat",metric="error_rate"} 0.00' in metrics
    assert 'ai_slo_breach_total{model="openai.default.chat",metric="p95_latency"} 1' in metrics
    assert 'ai_slo_breach_total{model="openai.default.chat",metric="error_rate"} 1' in metrics
