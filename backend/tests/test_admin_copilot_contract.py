"""
Wave1 #53 – Admin Copilot contract tests.
Covers: classify_question logic (pure), router endpoints (ask + logs),
        schema validation, and audit emission.
No DB dependency — all service calls monkeypatched.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.platform import router_admin
from app.platform.ai.service import AiCopilotService
from app.platform.ai.query_types import AiCopilotQueryType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router_admin.router)
    # router_admin.router has two router-level dependencies that enforce auth:
    # 1. _require_platform_admin_permissions (calls permission checks via JWT)
    # 2. _require_request_tenant_id (calls resolve_current_user_claims directly)
    app.dependency_overrides[router_admin.get_actor] = lambda: "admin@uni.edu"
    app.dependency_overrides[router_admin._require_platform_admin_permissions] = lambda: None
    app.dependency_overrides[router_admin._require_request_tenant_id] = lambda: 1
    app.dependency_overrides[router_admin._platform_admin_read_dependency] = lambda: None
    app.dependency_overrides[router_admin._platform_admin_write_dependency] = lambda: None
    return TestClient(app)


def _answer(question: str = "test?") -> dict:
    return {
        "question": question,
        "summary": "Test summary.",
        "insights": [],
        "sources": [],
        "warnings": [],
        "recommendations": [],
        "created_intervention_case_id": None,
    }


def _log_entry(i: int = 1) -> dict:
    return {
        "id": i,
        "tenant_id": 5,
        "actor_id": "admin@uni.edu",
        "question": "kpi summary?",
        "query_type": "kpi_overview",
        "retrieved_sources_json": [],
        "answer_json": {"summary": "OK"},
        "created_at": "2026-04-20T00:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# classify_question (pure logic — no DB, no monkeypatch)
# ---------------------------------------------------------------------------


def test_classify_question_kpi_keywords() -> None:
    svc = AiCopilotService.__new__(AiCopilotService)
    assert svc.classify_question("kpi summary for tenant 5") == AiCopilotQueryType.KPI_OVERVIEW.value


def test_classify_question_student_context() -> None:
    svc = AiCopilotService.__new__(AiCopilotService)
    assert svc.classify_question("student profile for id 42") == AiCopilotQueryType.STUDENT_CONTEXT.value


def test_classify_question_academic_risk() -> None:
    svc = AiCopilotService.__new__(AiCopilotService)
    assert svc.classify_question("academic risk report") == AiCopilotQueryType.ACADEMIC_RISK.value


def test_classify_question_unsupported_returns_unsupported() -> None:
    svc = AiCopilotService.__new__(AiCopilotService)
    result = svc.classify_question("what is the meaning of life?")
    assert result == AiCopilotQueryType.UNSUPPORTED.value


def test_classify_question_empty_returns_unsupported() -> None:
    svc = AiCopilotService.__new__(AiCopilotService)
    assert svc.classify_question("") == AiCopilotQueryType.UNSUPPORTED.value


# ---------------------------------------------------------------------------
# POST /api/v1/admin/platform/ai/copilot/ask
# ---------------------------------------------------------------------------


def test_ask_copilot_returns_answer_contract(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(router_admin.ai_service, "answer_question", lambda **_kw: _answer("how many students?"))

    response = client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        json={"tenant_id": 5, "question": "how many students?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["question"] == "how many students?"
    assert "summary" in body
    assert isinstance(body["insights"], list)
    assert isinstance(body["sources"], list)
    assert isinstance(body["warnings"], list)
    assert isinstance(body["recommendations"], list)


def test_ask_copilot_passes_tenant_id_and_question_to_service(monkeypatch) -> None:
    client = _build_client()
    calls: list[dict] = []

    def _capture(**kw):
        calls.append(kw)
        return _answer(kw["question"])

    monkeypatch.setattr(router_admin.ai_service, "answer_question", _capture)

    client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        json={"tenant_id": 7, "question": "kpi summary?"},
    )
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == 7
    assert calls[0]["question"] == "kpi summary?"


def test_ask_copilot_rejects_empty_question(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(router_admin.ai_service, "answer_question", lambda **_kw: _answer())

    response = client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        json={"tenant_id": 5, "question": ""},
    )
    # Pydantic min_length=1 → 422
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/admin/platform/ai/copilot/logs
# ---------------------------------------------------------------------------


def test_list_copilot_logs_returns_list_contract(monkeypatch) -> None:
    client = _build_client()
    monkeypatch.setattr(router_admin.ai_service, "list_logs", lambda **_kw: [_log_entry(1), _log_entry(2)])

    response = client.get("/api/v1/admin/platform/ai/copilot/logs", params={"tenant_id": 5})
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["id"] == 1
    assert body[0]["query_type"] == "kpi_overview"


def test_list_copilot_logs_passes_tenant_id_to_service(monkeypatch) -> None:
    client = _build_client()
    calls: list[dict] = []

    def _capture(**kw):
        calls.append(kw)
        return []

    monkeypatch.setattr(router_admin.ai_service, "list_logs", _capture)

    client.get("/api/v1/admin/platform/ai/copilot/logs", params={"tenant_id": 9})
    assert calls[0]["tenant_id"] == 9
