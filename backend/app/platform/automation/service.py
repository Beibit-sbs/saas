from __future__ import annotations

import logging
from typing import Any

from app.platform.automation.models import AutomationExecutionModel, AutomationRuleModel
from app.platform.automation.repository import AutomationRepository
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork

logger = logging.getLogger("app.platform.automation")

# ------------------------------------------------------------------ #
#  Shared singleton (used by UoW as default)                           #
# ------------------------------------------------------------------ #

_SHARED_AUTOMATION_REPOSITORY = AutomationRepository()

# ------------------------------------------------------------------ #
#  Condition evaluation                                                #
# ------------------------------------------------------------------ #

_SUPPORTED_OPERATORS = {"==", "!=", ">", "<", ">=", "<="}


def _evaluate_condition(condition_json: dict[str, Any], payload: dict[str, Any]) -> bool:
    """
    Evaluate a single condition against an event payload.

    Condition schema:
        {"field": "grade_value", "operator": "<", "value": 50}

    An empty condition_json is treated as "always match" (unconditional rule).

    Supports nested fields with dot notation: "enrollment.grade_points"
    """
    if not condition_json:
        return True  # unconditional rule

    field: str = condition_json.get("field", "")
    operator: str = condition_json.get("operator", "")
    expected_value: Any = condition_json.get("value")

    if not field or operator not in _SUPPORTED_OPERATORS:
        logger.warning(
            "automation_invalid_condition",
            extra={"condition": condition_json},
        )
        return False

    # Resolve field: support simple dot-notation for one level of nesting
    actual_value: Any = payload
    for part in field.split("."):
        if not isinstance(actual_value, dict):
            return False
        actual_value = actual_value.get(part)

    if actual_value is None:
        return False

    # Coerce types for numeric comparison
    try:
        if isinstance(expected_value, (int, float)):
            actual_value = type(expected_value)(actual_value)
    except (TypeError, ValueError):
        pass

    match operator:
        case "==":
            return actual_value == expected_value
        case "!=":
            return actual_value != expected_value
        case ">":
            return actual_value > expected_value  # type: ignore[operator]
        case "<":
            return actual_value < expected_value  # type: ignore[operator]
        case ">=":
            return actual_value >= expected_value  # type: ignore[operator]
        case "<=":
            return actual_value <= expected_value  # type: ignore[operator]
        case _:
            return False


# ------------------------------------------------------------------ #
#  Automation service                                                  #
# ------------------------------------------------------------------ #

def clear_automation_state() -> None:
    """Reset in-memory state. For tests only."""
    _SHARED_AUTOMATION_REPOSITORY._clear()


def create_rule(
    *,
    tenant_id: int,
    name: str,
    description: str = "",
    event_type: str,
    condition_json: dict[str, Any],
    actions_json: list[dict[str, Any]],
    is_active: bool = True,
    uow: UnitOfWork,
) -> AutomationRuleModel:
    return uow.automation_repository.create_rule(
        tenant_id=tenant_id,
        name=name,
        description=description,
        event_type=event_type,
        condition_json=condition_json,
        actions_json=actions_json,
        is_active=is_active,
        conn=uow.conn,
    )


def list_rules(*, tenant_id: int, uow: UnitOfWork) -> list[AutomationRuleModel]:
    return uow.automation_repository.list_rules(tenant_id, conn=uow.conn)


def list_executions(
    *,
    tenant_id: int,
    uow: UnitOfWork,
    limit: int = 50,
) -> list[AutomationExecutionModel]:
    return uow.automation_repository.list_executions(tenant_id, limit=limit, conn=uow.conn)


def evaluate_event(event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, Any]:
    """
    Core engine entry point.

    For every active rule matching event.event_type + tenant_id:
      1. Evaluate condition_json against event.payload_json
      2. If match: record AutomationExecution and execute all actions
      3. Update execution record with result / error

    Returns summary dict.
    """
    from app.platform.automation.actions import execute_action

    rules = uow.automation_repository.list_rules_by_event_type(
        event.tenant_id,
        event.event_type,
        conn=uow.conn,
    )

    matched = 0
    skipped = 0
    action_results: list[dict[str, Any]] = []

    for rule in rules:
        matched_condition = _evaluate_condition(rule.condition_json, event.payload_json)
        if not matched_condition:
            skipped += 1
            continue

        matched += 1
        # Record execution as pending
        execution = uow.automation_repository.create_execution(
            tenant_id=event.tenant_id,
            rule_id=rule.id,
            event_id=event.id,
            status="pending",
            result_json={},
            conn=uow.conn,
        )

        rule_results: list[dict[str, Any]] = []
        rule_error: str | None = None

        try:
            for action in rule.actions_json:
                result = execute_action(action, event, uow=uow)
                rule_results.append(result)
            final_status = "completed"
        except Exception as exc:
            rule_error = str(exc)
            final_status = "failed"
            logger.exception(
                "automation_execution_failed",
                extra={"rule_id": rule.id, "event_id": event.id, "error": rule_error},
            )

        uow.automation_repository.update_execution_status(
            execution.id,
            status=final_status,
            result_json={"actions": rule_results},
            error_message=rule_error,
            conn=uow.conn,
        )

        action_results.append({
            "rule_id": rule.id,
            "rule_name": rule.name,
            "execution_id": execution.id,
            "status": final_status,
            "actions_count": len(rule_results),
            "error": rule_error,
        })

        logger.info(
            "automation_rule_evaluated",
            extra={
                "rule_id": rule.id,
                "event_type": event.event_type,
                "tenant_id": event.tenant_id,
                "status": final_status,
            },
        )

    return {
        "event_type": event.event_type,
        "tenant_id": event.tenant_id,
        "rules_total": len(rules),
        "rules_matched": matched,
        "rules_skipped": skipped,
        "executions": action_results,
    }
