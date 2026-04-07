from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.platform.ai.service import copilot_service
from app.platform.automation import service as automation_service
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
    assert copilot_service.classify_question("Покажи профиль преподавателя advisor-2") == "faculty_context"
    assert copilot_service.classify_question("Сколько студентов у нас сейчас?") == "kpi_overview"
    assert copilot_service.classify_question("Show students at academic risk") == "academic_risk"
    assert copilot_service.classify_question("Студент на грани отчисления") == "academic_risk"
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


def test_faculty_context_answer_generation(reset_shared_state) -> None:
    tenant_id = _tenant("ai-fac")
    handler = ContextProjectionHandler()

    with UnitOfWork() as uow:
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="student.created",
                payload={"id": "s-100", "name": "Bob", "program_id": "prog-9", "department_id": "dep-7"},
                event_id=401,
            ),
            uow=uow,
        )
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="advisor.assigned",
                payload={"student_id": "s-100", "advisor_id": "advisor-2", "name": "Dr. Lane"},
                event_id=402,
            ),
            uow=uow,
        )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Покажи контекст преподавателя advisor-2",
    )

    assert answer["summary"].startswith("Faculty context loaded")
    assert any(item["title"] == "Advised Students" for item in answer["insights"])
    assert any(item["source_type"] == "context" for item in answer["sources"])


def test_faculty_context_requires_id(reset_shared_state) -> None:
    tenant_id = _tenant("ai-fac-missing")
    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Покажи контекст преподавателя",
    )

    assert answer["summary"] == "Faculty id is required for faculty context queries."
    assert "missing_faculty_id" in answer["warnings"]


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
    assert {"question", "summary", "insights", "sources", "warnings", "recommendations"}.issubset(body.keys())
    assert isinstance(body["insights"], list)
    assert isinstance(body["sources"], list)
    assert isinstance(body["recommendations"], list)

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


def test_academic_risk_answer_includes_counts_and_escalation_recommendation(reset_shared_state) -> None:
    tenant_id = _tenant("ai-risk")
    handler = ContextProjectionHandler()

    with UnitOfWork() as uow:
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="grade.submitted",
                payload={"id": "g1", "student_id": "s1", "grade_value": 55},
                event_id=501,
            ),
            uow=uow,
        )
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="grade.submitted",
                payload={"id": "g2", "student_id": "s2", "grade_value": 45},
                event_id=502,
            ),
            uow=uow,
        )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Кто на грани отчисления?",
    )

    assert answer["summary"].startswith("Identified 2 student(s) at academic risk")
    assert any(item["title"] == "At-Risk Students" and item["value"] == "2" for item in answer["insights"])
    assert any(item["title"] == "High Expulsion Risk Students" and item["value"] == "1" for item in answer["insights"])
    assert "expulsion_risk_detected" in answer["warnings"]
    assert any(rec["recommendation_type"] == "expulsion_risk_escalation" for rec in answer["recommendations"])


def test_per_tenant_risk_threshold_override(reset_shared_state) -> None:
    """Per-tenant risk threshold stored via save_setting is picked up by retrieve_academic_risk."""
    from app.modules.integrations.service import save_setting
    from app.platform.ai.retrieval import retrieve_academic_risk

    tenant_id = _tenant("threshold-override")
    handler = ContextProjectionHandler()

    # Grade of 70 — above the global default of 60, so NOT at risk by default.
    with UnitOfWork() as uow:
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="grade.submitted",
                payload={"id": "g100", "student_id": "s_threshold", "grade_value": 70},
                event_id=900,
            ),
            uow=uow,
        )

    # Confirm that with the default threshold (60) the student is NOT flagged.
    with UnitOfWork() as uow:
        result_default = retrieve_academic_risk(tenant_id=tenant_id, uow=uow)
    assert result_default["at_risk_count"] == 0

    # Override threshold to 80 for this tenant — 70 is now below 80 → at risk.
    save_setting("academic.risk_grade_threshold", "80", tenant_id=tenant_id)

    with UnitOfWork() as uow:
        result_overridden = retrieve_academic_risk(tenant_id=tenant_id, uow=uow)
    assert result_overridden["at_risk_count"] == 1, (
        "Student with grade 70 should be at risk when per-tenant threshold is 80"
    )


def test_academic_risk_triggers_intervention_auto_creation_hook(reset_shared_state, monkeypatch) -> None:
    tenant_id = _tenant("ai-risk-autocase")
    handler = ContextProjectionHandler()

    with UnitOfWork() as uow:
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="grade.submitted",
                payload={"id": "g-auto-1", "student_id": "s-auto-1", "grade_value": 45},
                event_id=1001,
            ),
            uow=uow,
        )

    auto_create_mock = MagicMock(return_value={"created": True, "case_id": 123})
    monkeypatch.setattr(
        "app.platform.ai.recommendations.service.maybe_create_academic_risk_intervention_case",
        auto_create_mock,
    )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Кто на грани отчисления?",
    )

    assert any(rec["recommendation_type"] == "expulsion_risk_escalation" for rec in answer["recommendations"])
    auto_create_mock.assert_called_once()
    kwargs = auto_create_mock.call_args.kwargs
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["retrieved_context"].get("severe_at_risk_count") == 1


def test_non_academic_query_does_not_trigger_intervention_auto_creation(reset_shared_state, monkeypatch) -> None:
    tenant_id = _tenant("ai-no-autocase")

    auto_create_mock = MagicMock(return_value={"created": True, "case_id": 123})
    monkeypatch.setattr(
        "app.platform.ai.recommendations.service.maybe_create_academic_risk_intervention_case",
        auto_create_mock,
    )

    _ = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="How many students do we currently have?",
    )

    auto_create_mock.assert_not_called()


def test_academic_risk_creates_bound_intervention_case_and_action(reset_shared_state, monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://app:app@db:5432/app"),
    )

    tenant_id = _tenant("ai-risk-db-bind")
    handler = ContextProjectionHandler()

    with UnitOfWork() as uow:
        if uow.conn is None:
            pytest.skip("DB-backed UnitOfWork connection is required for this integration test")
        with uow.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_profiles_people (
                    tenant_id,
                    email,
                    first_name,
                    last_name,
                    status,
                    metadata_json,
                    version,
                    created_by
                )
                VALUES (%s, %s, %s, %s, 'active', '{}'::jsonb, 1, 'pytest')
                RETURNING id
                """,
                (tenant_id, f"risk-bind-{tenant_id}@example.test", "Risk", "Bound"),
            )
            person_id = int(cur.fetchone()[0])

            cur.execute(
                """
                INSERT INTO app_students_profiles (
                    tenant_id,
                    person_id,
                    student_number,
                    cohort_year,
                    current_status,
                    admission_source,
                    metadata_json,
                    version,
                    created_by,
                    updated_by
                )
                VALUES (%s, %s, %s, %s, 'active', 'manual', '{}'::jsonb, 1, 'pytest', 'pytest')
                RETURNING id
                """,
                (tenant_id, person_id, "s-auto-bind-1", 2026),
            )
            student_profile_id = int(cur.fetchone()[0])

    with UnitOfWork() as uow:
        handler.handle(
            _event(
                tenant_id=tenant_id,
                event_type="grade.submitted",
                payload={"id": "g-bind-1", "student_id": "s-auto-bind-1", "grade_value": 45},
                event_id=1101,
            ),
            uow=uow,
        )

    answer = copilot_service.answer_question(
        tenant_id=tenant_id,
        actor_id="pytest",
        question="Show students at academic risk",
    )

    assert any(rec["recommendation_type"] == "expulsion_risk_escalation" for rec in answer["recommendations"])

    with UnitOfWork() as uow:
        if uow.conn is None:
            pytest.skip("DB-backed UnitOfWork connection is required for this integration test")
        with uow.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, student_profile_id, metadata_json
                FROM app_intervention_cases
                WHERE tenant_id = %s
                  AND case_type = 'academic_risk'
                  AND COALESCE(metadata_json ->> 'auto_source', '') = 'ai_academic_risk'
                ORDER BY id DESC
                LIMIT 1
                """,
                (tenant_id,),
            )
            case_row = cur.fetchone()

            assert case_row is not None
            case_id = int(case_row[0])
            linked_profile_id = int(case_row[1]) if case_row[1] is not None else None
            metadata_json = dict(case_row[2] or {})

            assert linked_profile_id == student_profile_id
            assert metadata_json.get("selected_student_identifier") == "s-auto-bind-1"
            assert int(metadata_json.get("linked_student_profile_id") or 0) == student_profile_id

            cur.execute(
                """
                SELECT COUNT(*)
                FROM app_intervention_actions
                WHERE tenant_id = %s
                  AND case_id = %s
                """,
                (tenant_id, case_id),
            )
            action_count = int(cur.fetchone()[0])
            assert action_count >= 1
