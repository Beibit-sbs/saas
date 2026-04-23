from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client


def test_usage_summary_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    resp = client.get("/api/admin/ai/usage/summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "requests_total" in data
    assert "estimated_cost_usd" in data
    assert "budget_limit_usd" in data
    assert "budget_utilization_pct" in data
    assert "anomaly_detected" in data
    assert "models" in data
    assert isinstance(data["models"], list)


def test_usage_budget_crud_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    # Set budget
    put_resp = client.put(
        "/api/admin/ai/usage/budget",
        headers=ADMIN_HEADERS,
        json={"budget_limit_usd": 500.0, "alert_threshold_pct": 75, "hard_cap": False},
    )
    assert put_resp.status_code == 200, put_resp.text
    updated = put_resp.json()
    assert updated["budget_limit_usd"] == 500.0
    assert updated["alert_threshold_pct"] == 75
    assert updated["hard_cap"] is False

    # Read budget
    get_resp = client.get("/api/admin/ai/usage/budget", headers=ADMIN_HEADERS)
    assert get_resp.status_code == 200, get_resp.text
    fetched = get_resp.json()
    assert fetched["budget_limit_usd"] == 500.0


def test_usage_budgets_scoped_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    # Create scoped budget for a department
    put_resp = client.put(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        json={
            "scope": "department",
            "scope_id": "engineering",
            "budget_limit_usd": 200.0,
            "alert_threshold_pct": 80,
            "hard_cap": True,
        },
    )
    assert put_resp.status_code == 200, put_resp.text
    created = put_resp.json()
    assert created["budget_limit_usd"] == 200.0
    assert created["scope"] == "department"
    assert created["scope_id"] == "engineering"

    # List scoped budgets
    list_resp = client.get("/api/admin/ai/usage/budgets", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json()
    assert isinstance(items, list)
    assert any(b["scope"] == "department" and b["scope_id"] == "engineering" for b in items)

    # Delete scoped budget
    del_resp = client.delete(
        "/api/admin/ai/usage/budgets",
        headers=ADMIN_HEADERS,
        params={"scope": "department", "scope_id": "engineering"},
    )
    assert del_resp.status_code == 200, del_resp.text

    # Confirm removed
    list_after = client.get("/api/admin/ai/usage/budgets", headers=ADMIN_HEADERS)
    assert all(
        not (b["scope"] == "department" and b["scope_id"] == "engineering")
        for b in list_after.json()
    )


def test_usage_budget_status_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    # Set a budget first so status has something to report
    client.put(
        "/api/admin/ai/usage/budget",
        headers=ADMIN_HEADERS,
        json={"budget_limit_usd": 1000.0, "alert_threshold_pct": 85, "hard_cap": False},
    )

    resp = client.get("/api/admin/ai/usage/budgets/status", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert isinstance(items, list)
    if items:
        item = items[0]
        assert "scope" in item
        assert "budget_limit_usd" in item
        assert "utilization_pct" in item
        assert "budget_alert" in item
        assert "hard_cap_exceeded" in item


def test_usage_projection_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    resp = client.get("/api/admin/ai/usage/projection", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "current_cost_usd" in data
    assert "projected_cost_usd" in data
    assert "projection_basis" in data


def test_usage_anomalies_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    resp = client.get("/api/admin/ai/usage/anomalies", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


def test_slo_policy_crud_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    model_key = "openai.default.chat"

    # Upsert SLO policy
    put_resp = client.put(
        f"/api/admin/ai/slo/{model_key}",
        headers=ADMIN_HEADERS,
        json={"p95_latency_ms": 2000, "max_error_rate_pct": 5.0},
    )
    assert put_resp.status_code == 200, put_resp.text
    slo = put_resp.json()
    assert slo["model_key"] == model_key
    assert slo["p95_latency_ms"] == 2000
    assert slo["max_error_rate_pct"] == 5.0

    # List SLO policies
    list_resp = client.get("/api/admin/ai/slo", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    policies = list_resp.json()
    assert isinstance(policies, list)
    assert any(p["model_key"] == model_key for p in policies)


def test_slo_compliance_and_violations_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    # Set an SLO policy so compliance endpoint has a target
    client.put(
        "/api/admin/ai/slo/openai.default.chat",
        headers=ADMIN_HEADERS,
        json={"p95_latency_ms": 3000, "max_error_rate_pct": 10.0},
    )

    compliance_resp = client.get("/api/admin/ai/slo/compliance", headers=ADMIN_HEADERS)
    assert compliance_resp.status_code == 200, compliance_resp.text
    compliance = compliance_resp.json()
    assert isinstance(compliance, list)
    if compliance:
        item = compliance[0]
        assert "model_key" in item
        assert "compliant" in item
        assert "latency_compliant" in item
        assert "error_rate_compliant" in item

    violations_resp = client.get("/api/admin/ai/slo/violations", headers=ADMIN_HEADERS)
    assert violations_resp.status_code == 200, violations_resp.text
    assert isinstance(violations_resp.json(), list)
