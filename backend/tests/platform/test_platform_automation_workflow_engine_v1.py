"""Tests for Automation / Workflow Engine v1."""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.platform.automation import service as automation_service
from app.platform.automation.service import _evaluate_condition
from app.platform.events.handlers.automation_handler import AutomationEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.jobs import service as jobs_service
from app.platform.notifications import service as notifications_service
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _create_tenant(prefix: str = "automation") -> int:
    tenant = tenant_service.create_tenant(
        f"{prefix}-{uuid4().hex[:8]}",
        f"{prefix.title()} Tenant",
    )
    return int(tenant["tenant_id"])


def _make_event(
    *,
    tenant_id: int,
    event_type: str = "grade.submitted",
    event_id: int = 1,
    payload: dict | None = None,
) -> OutboxEventRead:
    return OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id=str(event_id),
        payload_json=payload or {"id": event_id},
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )


# ------------------------------------------------------------------ #
#  1. Rule creation                                                    #
# ------------------------------------------------------------------ #

def test_create_rule_stores_and_returns_model(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    with UnitOfWork() as uow:
        rule = automation_service.create_rule(
            tenant_id=tenant_id,
            name="Low Grade Alert",
            description="Fires when grade < 50",
            event_type="grade.submitted",
            condition_json={"field": "grade_points", "operator": "<", "value": 50},
            actions_json=[{"type": "send_notification", "channel": "in_app", "template": "student_risk"}],
            uow=uow,
        )

    assert rule.id > 0
    assert rule.tenant_id == tenant_id
    assert rule.name == "Low Grade Alert"
    assert rule.event_type == "grade.submitted"
    assert rule.is_active is True
    assert rule.condition_json["operator"] == "<"
    assert len(rule.actions_json) == 1


# ------------------------------------------------------------------ #
#  2. Condition evaluation                                             #
# ------------------------------------------------------------------ #

def test_condition_evaluation_all_operators(reset_shared_state) -> None:
    payload = {"grade_points": 45, "status": "fail"}

    # numeric comparisons
    assert _evaluate_condition({"field": "grade_points", "operator": "<", "value": 50}, payload) is True
    assert _evaluate_condition({"field": "grade_points", "operator": "<", "value": 40}, payload) is False
    assert _evaluate_condition({"field": "grade_points", "operator": ">", "value": 40}, payload) is True
    assert _evaluate_condition({"field": "grade_points", "operator": ">=", "value": 45}, payload) is True
    assert _evaluate_condition({"field": "grade_points", "operator": "<=", "value": 44}, payload) is False
    assert _evaluate_condition({"field": "grade_points", "operator": "==", "value": 45}, payload) is True
    assert _evaluate_condition({"field": "grade_points", "operator": "!=", "value": 45}, payload) is False

    # string equality
    assert _evaluate_condition({"field": "status", "operator": "==", "value": "fail"}, payload) is True
    assert _evaluate_condition({"field": "status", "operator": "!=", "value": "pass"}, payload) is True

    # empty condition → always match
    assert _evaluate_condition({}, payload) is True

    # missing field → no match
    assert _evaluate_condition({"field": "nonexistent", "operator": "==", "value": 1}, payload) is False


def test_condition_nested_dot_notation(reset_shared_state) -> None:
    payload = {"enrollment": {"grade_points": 38}}
    assert _evaluate_condition(
        {"field": "enrollment.grade_points", "operator": "<", "value": 50},
        payload,
    ) is True


# ------------------------------------------------------------------ #
#  3. Rule matching on event — matched vs skipped                     #
# ------------------------------------------------------------------ #

def test_evaluate_event_matches_and_executes_actions(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(
        tenant_id=tenant_id,
        event_type="grade.submitted",
        event_id=42,
        payload={"grade_points": 30},
    )

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Risk Alert",
            event_type="grade.submitted",
            condition_json={"field": "grade_points", "operator": "<", "value": 50},
            actions_json=[
                {"type": "send_notification", "channel": "in_app", "template": "student_risk"},
                {"type": "create_task", "job_type": "remediation_review", "max_retries": 2},
            ],
            uow=uow,
        )
        result = automation_service.evaluate_event(event, uow=uow)

    assert result["rules_matched"] == 1
    assert result["rules_skipped"] == 0
    assert len(result["executions"]) == 1
    exec_summary = result["executions"][0]
    assert exec_summary["status"] == "completed"
    assert exec_summary["actions_count"] == 2


def test_evaluate_event_skips_non_matching_condition(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(
        tenant_id=tenant_id,
        event_type="grade.submitted",
        event_id=43,
        payload={"grade_points": 90},  # 90 is NOT < 50
    )

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Risk Alert",
            event_type="grade.submitted",
            condition_json={"field": "grade_points", "operator": "<", "value": 50},
            actions_json=[{"type": "send_notification", "channel": "in_app", "template": "student_risk"}],
            uow=uow,
        )
        result = automation_service.evaluate_event(event, uow=uow)

    assert result["rules_matched"] == 0
    assert result["rules_skipped"] == 1


def test_evaluate_event_unconditional_rule_always_fires(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(tenant_id=tenant_id, event_type="student.created", event_id=99)

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Welcome Task",
            event_type="student.created",
            condition_json={},  # unconditional
            actions_json=[{"type": "create_task", "job_type": "send_welcome_kit"}],
            uow=uow,
        )
        result = automation_service.evaluate_event(event, uow=uow)

    assert result["rules_matched"] == 1
    assert result["executions"][0]["status"] == "completed"


# ------------------------------------------------------------------ #
#  4. Action execution — send_notification creates a notification      #
# ------------------------------------------------------------------ #

def test_action_send_notification(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(tenant_id=tenant_id, event_type="enrollment.created", event_id=77)

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Enrollment Notify",
            event_type="enrollment.created",
            condition_json={},
            actions_json=[{"type": "send_notification", "channel": "in_app", "template": "enrollment_welcome"}],
            uow=uow,
        )
        automation_service.evaluate_event(event, uow=uow)

    notifications = notifications_service.list_notifications(tenant_id, limit=100)
    assert any(n.get("subject") == "enrollment_welcome" for n in notifications)


def test_action_create_task_enqueues_job(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(tenant_id=tenant_id, event_type="grade.submitted", event_id=55, payload={"grade_points": 20})

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Remediation",
            event_type="grade.submitted",
            condition_json={"field": "grade_points", "operator": "<", "value": 50},
            actions_json=[{"type": "create_task", "job_type": "remediation_review", "max_retries": 3}],
            uow=uow,
        )
        automation_service.evaluate_event(event, uow=uow)

    jobs = jobs_service.list_tenant_jobs(tenant_id)
    remediation_jobs = [j for j in jobs if j.get("job_type") == "remediation_review"]
    assert len(remediation_jobs) >= 1


# ------------------------------------------------------------------ #
#  5. Tenant isolation                                                 #
# ------------------------------------------------------------------ #

def test_tenant_isolation_rules_not_visible_cross_tenant(reset_shared_state) -> None:
    tenant_a = _create_tenant("isolation-a")
    tenant_b = _create_tenant("isolation-b")

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_a,
            name="Tenant A Rule",
            event_type="grade.submitted",
            condition_json={},
            actions_json=[],
            uow=uow,
        )

    with UnitOfWork() as uow:
        rules_b = automation_service.list_rules(tenant_id=tenant_b, uow=uow)

    assert all(r.tenant_id == tenant_b for r in rules_b)
    assert len(rules_b) == 0


def test_tenant_isolation_event_only_triggers_own_rules(reset_shared_state) -> None:
    tenant_a = _create_tenant("iso-event-a")
    tenant_b = _create_tenant("iso-event-b")

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_a,
            name="A Alert",
            event_type="grade.submitted",
            condition_json={},
            actions_json=[{"type": "create_task", "job_type": "alert_task"}],
            uow=uow,
        )

    # Fire event for tenant_b — should NOT match tenant_a's rule
    event_b = _make_event(tenant_id=tenant_b, event_type="grade.submitted", event_id=200)
    with UnitOfWork() as uow:
        result = automation_service.evaluate_event(event_b, uow=uow)

    assert result["rules_matched"] == 0


# ------------------------------------------------------------------ #
#  6. Execution logging                                                #
# ------------------------------------------------------------------ #

def test_execution_record_saved_after_match(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(tenant_id=tenant_id, payload={"grade_points": 10})

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Record Test",
            event_type="grade.submitted",
            condition_json={"field": "grade_points", "operator": "<", "value": 50},
            actions_json=[{"type": "send_notification", "channel": "in_app", "template": "test"}],
            uow=uow,
        )
        automation_service.evaluate_event(event, uow=uow)
        executions = automation_service.list_executions(tenant_id=tenant_id, uow=uow)

    assert len(executions) == 1
    assert executions[0].status == "completed"
    assert executions[0].tenant_id == tenant_id
    assert executions[0].event_id == event.id


def test_execution_status_failed_on_bad_action(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(tenant_id=tenant_id)

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Bad Action Rule",
            event_type="grade.submitted",
            condition_json={},
            actions_json=[{"type": "nonexistent_action"}],
            uow=uow,
        )
        result = automation_service.evaluate_event(event, uow=uow)
        executions = automation_service.list_executions(tenant_id=tenant_id, uow=uow)

    assert result["executions"][0]["status"] == "failed"
    assert executions[0].status == "failed"
    assert "nonexistent_action" in (executions[0].error_message or "")


# ------------------------------------------------------------------ #
#  7. Admin API routes                                                 #
# ------------------------------------------------------------------ #

def test_admin_api_create_and_list_rules(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    payload = {
        "tenant_id": tenant_id,
        "name": "API Rule",
        "event_type": "grade.submitted",
        "condition_json": {"field": "grade_points", "operator": "<", "value": 60},
        "actions_json": [{"type": "send_notification", "channel": "email", "template": "risk_alert"}],
        "is_active": True,
    }
    create_resp = client.post(
        "/api/v1/admin/platform/automation/rules",
        json=payload,
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["name"] == "API Rule"
    assert data["id"] > 0

    list_resp = client.get(
        f"/api/v1/admin/platform/automation/rules?tenant_id={tenant_id}",
        headers=ADMIN_HEADERS,
    )
    assert list_resp.status_code == 200
    assert any(r["name"] == "API Rule" for r in list_resp.json())


def test_admin_api_list_executions(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    event = _make_event(tenant_id=tenant_id, event_id=301)

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Exec Listing Rule",
            event_type="grade.submitted",
            condition_json={},
            actions_json=[{"type": "create_task", "job_type": "review"}],
            uow=uow,
        )
        automation_service.evaluate_event(event, uow=uow)

    resp = client.get(
        f"/api/v1/admin/platform/automation/executions?tenant_id={tenant_id}",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    executions = resp.json()
    assert len(executions) >= 1
    assert executions[0]["tenant_id"] == tenant_id


# ------------------------------------------------------------------ #
#  8. Integration with event worker (AutomationEventHandler)          #
# ------------------------------------------------------------------ #

def test_automation_event_handler_integrates_with_worker(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    with UnitOfWork() as uow:
        automation_service.create_rule(
            tenant_id=tenant_id,
            name="Worker Integration Rule",
            event_type="student.created",
            condition_json={},
            actions_json=[{"type": "send_notification", "channel": "in_app", "template": "new_student"}],
            uow=uow,
        )

    event = _make_event(tenant_id=tenant_id, event_type="student.created", event_id=500)
    handler = AutomationEventHandler()

    with UnitOfWork() as uow:
        result = handler.handle(event, uow=uow)

    assert result["handler"] == "automation"
    assert result["rules_matched"] == 1
    assert result["executions"][0]["status"] == "completed"


def test_automation_handler_name_registered_in_worker(reset_shared_state) -> None:
    """Verify AutomationEventHandler is included in the default outbox worker pipeline."""
    from app.platform.events.worker import outbox_worker

    handler_names = [h.name for h in outbox_worker._handlers]
    assert "automation" in handler_names
