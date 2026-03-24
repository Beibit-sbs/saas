from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.platform.ai.service import copilot_service
from app.platform.automation import service as automation_service
from app.platform.context import service as context_service
from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.handlers.context_projection_handler import ContextProjectionHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


def _tenant(prefix: str) -> int:
    row = tenant_service.create_tenant(f"{prefix}-{uuid4().hex[:8]}", f"{prefix} Tenant")
    return int(row["tenant_id"])


def _event(*, tenant_id: int, event_type: str, payload: dict, event_id: int) -> OutboxEventRead:
    return OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id=str(event_id),
        payload_json=payload,
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_classification_rules() -> None:
    assert copilot_service.classify_question("How many students do we currently have?") == "kpi_overview"
    assert copilot_service.classify_question("Which automation rules are failing?") == "automation_health"
    assert copilot_service.classify_question("Show student context for student 42") == "student_context"
    assert copilot_service.classify_question("Show students at academic risk") == "academic_risk"
    assert copilot_service.classify_question("something completely unrelated") == "unsupported"


def test_kpi_answer_generation(reset_shared_state) -> None:
    tenant_id = _tenant("ai-kpi")

    with UnitOfWork() as uow:
        AnalyticsEventHandler().handle(
            _event(tenant_id=tenant_id, event_type="student.created", payload={"id": "s1"}, event_id=101),
            uow=uow,
        )
        AnalyticsEventHandler().handle(
            _event(tenant_id=tenant_id, event_type="student.created", payload={"id": "s2"}, event_id=102),
            uow=uow,
        )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="How many students do we currently have?",
    )

    assert "Current Students" in answer["summary"] or answer["insights"][0]["title"] == "Current Students"
    assert answer["sources"]
    assert answer["sources"][0]["source_type"] == "kpi"


def test_automation_health_answer_generation(reset_shared_state) -> None:
    tenant_id = _tenant("ai-auto")

    with UnitOfWork() as uow:
        rule = automation_service.create_rule(
            tenant_id=tenant_id,
            name="Broken Rule",
            description="",
            event_type="student.created",
            condition_json={},
            actions_json=[{"type": "unknown_action"}],
            is_active=True,
            uow=uow,
        )
        _ = rule
        automation_service.evaluate_event(
            _event(tenant_id=tenant_id, event_type="student.created", payload={"id": "s1"}, event_id=201),
            uow=uow,
        )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Which automation rules are failing?",
    )

    assert answer["summary"] == "Automation health checked."
    assert any(item["title"] == "Failed Automation Executions" for item in answer["insights"])
    assert any(item["source_type"] == "automation" for item in answer["sources"])


def test_student_context_answer_generation(reset_shared_state) -> None:
    tenant_id = _tenant("ai-ctx")
    handler = ContextProjectionHandler()

    with UnitOfWork() as uow:
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="student.created",
                payload={"id": "42", "name": "Alice", "program_id": "prog-1"},
                event_id=301,
            ),
            uow=uow,
        )
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="advisor.assigned",
                payload={"student_id": "42", "advisor_id": "adv-2"},
                event_id=302,
            ),
            uow=uow,
        )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Show student context for student 42",
    )

    assert answer["summary"].startswith("Student context loaded")
    assert any(item["title"] == "Program" for item in answer["insights"])
    assert any(item["source_type"] == "context" for item in answer["sources"])


def test_tenant_isolation_and_logging(reset_shared_state) -> None:
    tenant_a = _tenant("ai-a")
    tenant_b = _tenant("ai-b")

    copilot_service.answer_question(
        tenant_id=tenant_a,
        actor_id="pytest",
        question="How many students do we currently have?",
    )

    logs_a = copilot_service.list_logs(tenant_id=tenant_a)
    logs_b = copilot_service.list_logs(tenant_id=tenant_b)

    assert len(logs_a) == 1
    assert logs_a[0]["tenant_id"] == tenant_a
    assert logs_b == []


def test_unsupported_query_handling(reset_shared_state) -> None:
    tenant_id = _tenant("ai-unsup")
    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Can you rewrite enrollment policies automatically?",
    )

    assert answer["summary"] == "This question type is not supported yet."
    assert "unsupported_query_type" in answer["warnings"]


def test_admin_api_response_shape(reset_shared_state) -> None:
    tenant_id = _tenant("ai-api")

    ask = client.post(
        "/api/v1/admin/platform/ai/copilot/ask",
        headers=ADMIN_HEADERS,
        json={
            "tenant_id": tenant_id,
            "question": "Show me the latest KPI summary",
            "context": {},
        },
    )
    assert ask.status_code == 200, ask.text
    body = ask.json()
    assert set(body.keys()) == {"question", "summary", "insights", "sources", "warnings"}
    assert isinstance(body["insights"], list)
    assert isinstance(body["sources"], list)

    logs = client.get(
        "/api/v1/admin/platform/ai/copilot/logs",
        headers=ADMIN_HEADERS,
        params={"tenant_id": tenant_id},
    )
    assert logs.status_code == 200, logs.text
    payload = logs.json()
    assert isinstance(payload, list)
    assert payload
    assert payload[0]["tenant_id"] == tenant_id
    assert payload[0]["question"] == "Show me the latest KPI summary"
