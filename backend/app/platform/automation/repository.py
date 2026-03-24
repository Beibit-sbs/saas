from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any

from app.platform.automation.models import AutomationExecutionModel, AutomationRuleModel

try:
    import psycopg  # type: ignore[import]
except ModuleNotFoundError:
    psycopg = None  # type: ignore[assignment]

from app.platform.repository.db import db_available, transaction


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rule_row_to_model(row: tuple[Any, ...]) -> AutomationRuleModel:
    (id_, tenant_id, name, description, event_type,
     condition_json, actions_json, is_active, created_at, updated_at, version) = row
    return AutomationRuleModel(
        id=int(id_),
        tenant_id=int(tenant_id),
        name=str(name),
        description=str(description or ""),
        event_type=str(event_type),
        condition_json=dict(condition_json) if condition_json else {},
        actions_json=list(actions_json) if actions_json else [],
        is_active=bool(is_active),
        created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
        updated_at=updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
        version=int(version),
    )


def _exec_row_to_model(row: tuple[Any, ...]) -> AutomationExecutionModel:
    (id_, tenant_id, rule_id, event_id, status,
     result_json, error_message, executed_at, created_at) = row
    return AutomationExecutionModel(
        id=int(id_),
        tenant_id=int(tenant_id),
        rule_id=int(rule_id),
        event_id=int(event_id),
        status=str(status),
        result_json=dict(result_json) if result_json else {},
        error_message=str(error_message) if error_message else None,
        executed_at=executed_at.isoformat() if hasattr(executed_at, "isoformat") else str(executed_at),
        created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
    )


class AutomationRepository:
    """Dual-mode repository: in-memory (tests) + PostgreSQL (production)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rules: dict[int, AutomationRuleModel] = {}
        self._executions: dict[int, AutomationExecutionModel] = {}
        self._rule_seq: int = 0
        self._exec_seq: int = 0

    # ------------------------------------------------------------------ #
    #  In-memory helpers                                                   #
    # ------------------------------------------------------------------ #

    def _next_rule_id(self) -> int:
        self._rule_seq += 1
        return self._rule_seq

    def _next_exec_id(self) -> int:
        self._exec_seq += 1
        return self._exec_seq

    def _clear(self) -> None:
        with self._lock:
            self._rules.clear()
            self._executions.clear()
            self._rule_seq = 0
            self._exec_seq = 0

    # ------------------------------------------------------------------ #
    #  Rules                                                               #
    # ------------------------------------------------------------------ #

    def create_rule(
        self,
        *,
        tenant_id: int,
        name: str,
        description: str,
        event_type: str,
        condition_json: dict[str, Any],
        actions_json: list[dict[str, Any]],
        is_active: bool = True,
        conn: object | None = None,
    ) -> AutomationRuleModel:
        if conn is None:
            with transaction() as tx:
                return self.create_rule(
                    tenant_id=tenant_id,
                    name=name,
                    description=description,
                    event_type=event_type,
                    condition_json=condition_json,
                    actions_json=actions_json,
                    is_active=is_active,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_automation_rules
                        (tenant_id, name, description, event_type,
                         condition_json, actions_json, is_active)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    RETURNING id, tenant_id, name, description, event_type,
                              condition_json, actions_json, is_active,
                              created_at, updated_at, version
                    """,
                    (
                        tenant_id, name, description, event_type,
                        json.dumps(condition_json), json.dumps(actions_json), is_active,
                    ),
                )
                row = cur.fetchone()
                return _rule_row_to_model(row)

        # in-memory path
        now = _utc_now_iso()
        with self._lock:
            rule_id = self._next_rule_id()
            rule = AutomationRuleModel(
                id=rule_id,
                tenant_id=tenant_id,
                name=name,
                description=description,
                event_type=event_type,
                condition_json=dict(condition_json),
                actions_json=list(actions_json),
                is_active=is_active,
                created_at=now,
                updated_at=now,
                version=1,
            )
            self._rules[rule_id] = rule
            return rule

    def update_rule(
        self,
        rule_id: int,
        *,
        is_active: bool,
        conn: object | None = None,
    ) -> AutomationRuleModel | None:
        if conn is None:
            with transaction() as tx:
                return self.update_rule(rule_id, is_active=is_active, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_automation_rules
                       SET is_active = %s, updated_at = NOW(), version = version + 1
                     WHERE id = %s
                    RETURNING id, tenant_id, name, description, event_type,
                              condition_json, actions_json, is_active,
                              created_at, updated_at, version
                    """,
                    (is_active, rule_id),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return _rule_row_to_model(row)

        with self._lock:
            rule = self._rules.get(rule_id)
            if rule is None:
                return None
            updated = AutomationRuleModel(
                id=rule.id,
                tenant_id=rule.tenant_id,
                name=rule.name,
                description=rule.description,
                event_type=rule.event_type,
                condition_json=rule.condition_json,
                actions_json=rule.actions_json,
                is_active=is_active,
                created_at=rule.created_at,
                updated_at=_utc_now_iso(),
                version=rule.version + 1,
            )
            self._rules[rule_id] = updated
            return updated

    def list_rules_by_event_type(
        self,
        tenant_id: int,
        event_type: str,
        *,
        conn: object | None = None,
    ) -> list[AutomationRuleModel]:
        if conn is None:
            with transaction() as tx:
                return self.list_rules_by_event_type(tenant_id, event_type, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, name, description, event_type,
                           condition_json, actions_json, is_active,
                           created_at, updated_at, version
                      FROM app_platform_automation_rules
                     WHERE tenant_id = %s AND event_type = %s AND is_active = TRUE
                     ORDER BY id ASC
                    """,
                    (tenant_id, event_type),
                )
                return [_rule_row_to_model(r) for r in cur.fetchall()]

        with self._lock:
            return [
                r for r in self._rules.values()
                if r.tenant_id == tenant_id and r.event_type == event_type and r.is_active
            ]

    def list_rules(
        self,
        tenant_id: int,
        *,
        conn: object | None = None,
    ) -> list[AutomationRuleModel]:
        if conn is None:
            with transaction() as tx:
                return self.list_rules(tenant_id, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, name, description, event_type,
                           condition_json, actions_json, is_active,
                           created_at, updated_at, version
                      FROM app_platform_automation_rules
                     WHERE tenant_id = %s
                     ORDER BY id DESC
                    """,
                    (tenant_id,),
                )
                return [_rule_row_to_model(r) for r in cur.fetchall()]

        with self._lock:
            return [r for r in self._rules.values() if r.tenant_id == tenant_id]

    # ------------------------------------------------------------------ #
    #  Executions                                                          #
    # ------------------------------------------------------------------ #

    def create_execution(
        self,
        *,
        tenant_id: int,
        rule_id: int,
        event_id: int,
        status: str,
        result_json: dict[str, Any],
        error_message: str | None = None,
        conn: object | None = None,
    ) -> AutomationExecutionModel:
        if conn is None:
            with transaction() as tx:
                return self.create_execution(
                    tenant_id=tenant_id,
                    rule_id=rule_id,
                    event_id=event_id,
                    status=status,
                    result_json=result_json,
                    error_message=error_message,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_automation_executions
                        (tenant_id, rule_id, event_id, status, result_json, error_message)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                    RETURNING id, tenant_id, rule_id, event_id, status,
                              result_json, error_message, executed_at, created_at
                    """,
                    (
                        tenant_id, rule_id, event_id, status,
                        json.dumps(result_json), error_message,
                    ),
                )
                row = cur.fetchone()
                return _exec_row_to_model(row)

        now = _utc_now_iso()
        with self._lock:
            exec_id = self._next_exec_id()
            execution = AutomationExecutionModel(
                id=exec_id,
                tenant_id=tenant_id,
                rule_id=rule_id,
                event_id=event_id,
                status=status,
                result_json=dict(result_json),
                error_message=error_message,
                executed_at=now,
                created_at=now,
            )
            self._executions[exec_id] = execution
            return execution

    def update_execution_status(
        self,
        execution_id: int,
        *,
        status: str,
        result_json: dict[str, Any],
        error_message: str | None = None,
        conn: object | None = None,
    ) -> AutomationExecutionModel | None:
        if conn is None:
            with transaction() as tx:
                return self.update_execution_status(
                    execution_id,
                    status=status,
                    result_json=result_json,
                    error_message=error_message,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_automation_executions
                       SET status = %s, result_json = %s::jsonb, error_message = %s
                     WHERE id = %s
                    RETURNING id, tenant_id, rule_id, event_id, status,
                              result_json, error_message, executed_at, created_at
                    """,
                    (status, json.dumps(result_json), error_message, execution_id),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return _exec_row_to_model(row)

        with self._lock:
            execution = self._executions.get(execution_id)
            if execution is None:
                return None
            updated = AutomationExecutionModel(
                id=execution.id,
                tenant_id=execution.tenant_id,
                rule_id=execution.rule_id,
                event_id=execution.event_id,
                status=status,
                result_json=dict(result_json),
                error_message=error_message,
                executed_at=execution.executed_at,
                created_at=execution.created_at,
            )
            self._executions[execution_id] = updated
            return updated

    def list_executions(
        self,
        tenant_id: int,
        *,
        limit: int = 50,
        conn: object | None = None,
    ) -> list[AutomationExecutionModel]:
        if conn is None:
            with transaction() as tx:
                return self.list_executions(tenant_id, limit=limit, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, rule_id, event_id, status,
                           result_json, error_message, executed_at, created_at
                      FROM app_platform_automation_executions
                     WHERE tenant_id = %s
                     ORDER BY id DESC
                     LIMIT %s
                    """,
                    (tenant_id, limit),
                )
                return [_exec_row_to_model(r) for r in cur.fetchall()]

        with self._lock:
            rows = [e for e in self._executions.values() if e.tenant_id == tenant_id]
            rows.sort(key=lambda e: e.id, reverse=True)
            return rows[:limit]
