from __future__ import annotations

from tests.conftest import ADMIN_HEADERS, client


def test_ai_routing_policy_crud_contract() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    create_resp = client.post(
        "/api/admin/ai/routing/policies",
        headers=ADMIN_HEADERS,
        json={
            "name": "chat-priority-policy",
            "strategy": "priority",
            "enabled": True,
            "rules": [
                {
                    "task_type": "chat",
                    "target_model": "gemini.default.chat",
                    "priority": 10,
                }
            ],
            "fallback_chain": ["openai.default.chat"],
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    policy_id = int(created["id"])
    assert created["name"] == "chat-priority-policy"
    assert created["rules"][0]["target_model"] == "gemini.default.chat"

    list_resp = client.get("/api/admin/ai/routing/policies", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json()
    assert any(int(item["id"]) == policy_id for item in items)

    update_resp = client.put(
        f"/api/admin/ai/routing/policies/{policy_id}",
        headers=ADMIN_HEADERS,
        json={
            "name": "chat-priority-policy-v2",
            "strategy": "priority",
            "enabled": False,
            "rules": [
                {
                    "task_type": "chat",
                    "target_model": "openai.default.chat",
                    "priority": 1,
                }
            ],
            "fallback_chain": ["gemini.default.chat"],
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["enabled"] is False
    assert updated["rules"][0]["target_model"] == "openai.default.chat"

    delete_resp = client.delete(f"/api/admin/ai/routing/policies/{policy_id}", headers=ADMIN_HEADERS)
    assert delete_resp.status_code == 204, delete_resp.text

    list_after_delete = client.get("/api/admin/ai/routing/policies", headers=ADMIN_HEADERS)
    assert list_after_delete.status_code == 200, list_after_delete.text
    assert all(int(item["id"]) != policy_id for item in list_after_delete.json())


def test_execute_chat_auto_model_uses_policy_rule(monkeypatch) -> None:
    from app.modules.ai_gateway import service as ai_service
    from app.modules.billing import service as billing_service

    ai_service.clear_ai_gateway_state()

    monkeypatch.setattr(billing_service, "assert_billing_write_allowed", lambda tenant_id, action: None)
    monkeypatch.setattr(
        billing_service,
        "assert_quota_with_increment",
        lambda tenant_id, quota_key, increment=1: {
            "tenant_id": tenant_id,
            "quota_key": quota_key,
            "within_limit": True,
        },
    )
    monkeypatch.setattr(ai_service, "enforce_rate_limit", lambda provider, actor, roles: None)
    monkeypatch.setattr(ai_service, "_provider_runtime_config", lambda provider, tenant_id=None: {})

    monkeypatch.setattr(
        ai_service,
        "list_models",
        lambda include_disabled=True, tenant_id=1: [
            {
                "model_key": "openai.default.chat",
                "provider": "openai",
                "enabled": True,
                "priority": 100,
            },
            {
                "model_key": "gemini.default.chat",
                "provider": "gemini",
                "enabled": True,
                "priority": 200,
            },
        ],
    )

    ai_service.create_routing_policy(
        {
            "name": "chat-policy",
            "strategy": "priority",
            "enabled": True,
            "rules": [{"task_type": "chat", "target_model": "gemini.default.chat", "priority": 1}],
            "fallback_chain": [],
        },
        tenant_id=1,
    )

    selected = {}

    def _resolve_model(model_key: str, *, tenant_id: int) -> dict[str, object]:
        selected["model_key"] = model_key
        if model_key == "gemini.default.chat":
            return {
                "provider": "gemini",
                "provider_model_id": "gemini-1.5-flash",
                "enabled": True,
            }
        return {
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "enabled": True,
        }

    monkeypatch.setattr(ai_service, "_resolve_model", _resolve_model)

    class _FakeAdapter:
        def execute_chat(self, **kwargs):
            class _Result:
                output_text = "ok"
                finish_reason = "stop"
                usage = {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7}

            return _Result()

    monkeypatch.setattr(ai_service, "_adapter_for_provider", lambda provider: _FakeAdapter())

    result = ai_service.execute_chat(
        {
            "model": "auto",
            "task_type": "chat",
            "messages": [{"role": "user", "content": "hello"}],
        },
        actor="owner@example.com",
        roles=["admin"],
        tenant_id=1,
    )

    assert selected["model_key"] == "gemini.default.chat"
    assert result["model"] == "gemini.default.chat"
    assert result["routing"]["selection"] == "policy_rule"
    assert int(result["routing"]["policy_id"]) >= 1


def test_execute_chat_auto_model_priority_default(monkeypatch) -> None:
    from app.modules.ai_gateway import service as ai_service
    from app.modules.billing import service as billing_service

    ai_service.clear_ai_gateway_state()

    monkeypatch.setattr(billing_service, "assert_billing_write_allowed", lambda tenant_id, action: None)
    monkeypatch.setattr(
        billing_service,
        "assert_quota_with_increment",
        lambda tenant_id, quota_key, increment=1: {
            "tenant_id": tenant_id,
            "quota_key": quota_key,
            "within_limit": True,
        },
    )
    monkeypatch.setattr(ai_service, "enforce_rate_limit", lambda provider, actor, roles: None)
    monkeypatch.setattr(ai_service, "_provider_runtime_config", lambda provider, tenant_id=None: {})

    monkeypatch.setattr(
        ai_service,
        "list_models",
        lambda include_disabled=True, tenant_id=1: [
            {
                "model_key": "openai.default.chat",
                "provider": "openai",
                "enabled": True,
                "priority": 100,
            }
        ],
    )

    monkeypatch.setattr(
        ai_service,
        "_resolve_model",
        lambda model_key, tenant_id=1: {
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "enabled": True,
        },
    )

    class _FakeAdapter:
        def execute_chat(self, **kwargs):
            class _Result:
                output_text = "ok"
                finish_reason = "stop"
                usage = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}

            return _Result()

    monkeypatch.setattr(ai_service, "_adapter_for_provider", lambda provider: _FakeAdapter())

    result = ai_service.execute_chat(
        {
            "model": "auto",
            "task_type": "classification",
            "messages": [{"role": "user", "content": "route me"}],
        },
        actor="owner@example.com",
        roles=["admin"],
        tenant_id=1,
    )

    assert result["model"] == "openai.default.chat"
    assert result["routing"]["selection"] == "priority_default"


def test_routing_selection_log_records_decisions(monkeypatch) -> None:
    from app.modules.ai_gateway import service as ai_service
    from app.modules.billing import service as billing_service

    ai_service.clear_ai_gateway_state()

    monkeypatch.setattr(billing_service, "assert_billing_write_allowed", lambda tenant_id, action: None)
    monkeypatch.setattr(
        billing_service,
        "assert_quota_with_increment",
        lambda tenant_id, quota_key, increment=1: {
            "tenant_id": tenant_id,
            "quota_key": quota_key,
            "within_limit": True,
        },
    )
    monkeypatch.setattr(ai_service, "enforce_rate_limit", lambda provider, actor, roles: None)
    monkeypatch.setattr(ai_service, "_provider_runtime_config", lambda provider, tenant_id=None: {})
    monkeypatch.setattr(
        ai_service,
        "list_models",
        lambda include_disabled=True, tenant_id=1: [
            {
                "model_key": "openai.default.chat",
                "provider": "openai",
                "enabled": True,
                "priority": 100,
            }
        ],
    )
    monkeypatch.setattr(
        ai_service,
        "_resolve_model",
        lambda model_key, tenant_id=1: {
            "provider": "openai",
            "provider_model_id": "gpt-4o-mini",
            "enabled": True,
        },
    )

    class _FakeAdapter:
        def execute_chat(self, **kwargs):
            class _R:
                output_text = "hello"
                finish_reason = "stop"
                usage = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
            return _R()

    monkeypatch.setattr(ai_service, "_adapter_for_provider", lambda provider: _FakeAdapter())

    ai_service.execute_chat(
        {"model": "auto", "task_type": "chat", "messages": [{"role": "user", "content": "hi"}]},
        actor="user@example.com",
        roles=["admin"],
        tenant_id=1,
    )

    log_entries = ai_service.list_routing_selection_log(tenant_id=1)
    assert len(log_entries) >= 1
    entry = log_entries[0]
    assert entry["tenant_id"] == 1
    assert str(entry["model_key"]) == "openai.default.chat"
    assert str(entry["selection"]) == "priority_default"
    assert "timestamp" in entry


def test_routing_selection_emits_prometheus_metric(monkeypatch) -> None:
    from app.modules.ai_gateway import service as ai_service
    from app.modules.observability import metrics as obs

    ai_service.clear_ai_gateway_state()
    obs.clear_metrics_state()

    ai_service._record_routing_selection(
        "openai.default.chat",
        {"mode": "auto", "selection": "policy_rule", "policy_id": 1, "task_type": "chat"},
        tenant_id=42,
    )

    rendered = obs.render_metrics()
    assert "ai_routing_selection_total" in rendered
    assert 'selection="policy_rule"' in rendered


def test_routing_selection_log_api_endpoint() -> None:
    from app.modules.ai_gateway import service as ai_service

    ai_service.clear_ai_gateway_state()

    ai_service._record_routing_selection(
        "gemini.default.chat",
        {"mode": "auto", "selection": "policy_rule", "policy_id": 2, "task_type": "summarize"},
        tenant_id=1,
    )

    resp = client.get("/api/admin/ai/routing/selection-log", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert isinstance(items, list)
    assert any(item.get("model_key") == "gemini.default.chat" for item in items)
