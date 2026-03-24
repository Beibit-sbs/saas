"""Automation Templates Repository - in-memory and postgres implementations."""

from __future__ import annotations

import json
import threading
import uuid
from typing import TYPE_CHECKING, Any

import psycopg
from psycopg import sql

from app.platform.repository.db import db_available, transaction
from app.platform.automation.templates.models import AutomationTemplateModel

if TYPE_CHECKING:
    pass


def _utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _template_row_to_model(row: tuple[Any, ...]) -> AutomationTemplateModel:
    """Convert database row to AutomationTemplateModel."""
    return AutomationTemplateModel(
        id=str(row[0]),
        template_key=row[1],
        title=row[2],
        description=row[3],
        category=row[4],
        event_type=row[5],
        condition_json=row[6] if isinstance(row[6], dict) else {},
        actions_json=row[7] if isinstance(row[7], list) else [],
        is_system_template=row[8],
        created_at=row[9].isoformat() if hasattr(row[9], 'isoformat') else str(row[9]),
        updated_at=row[10].isoformat() if hasattr(row[10], 'isoformat') else str(row[10]),
        version=row[11],
    )


class AutomationTemplateRepository:
    """Repository for automation templates (both in-memory and postgres)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._templates: dict[str, AutomationTemplateModel] = {}

    # ------------------------------------------------------------------ #
    #  Templates                                                           #
    # ------------------------------------------------------------------ #

    def list_templates(
        self,
        *,
        conn: object | None = None,
    ) -> list[AutomationTemplateModel]:
        """List all automation templates."""
        if conn is None:
            with transaction() as tx:
                return self.list_templates(conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, template_key, title, description, category,
                           event_type, condition_json, actions_json,
                           is_system_template, created_at, updated_at, version
                      FROM app_platform_automation_templates
                     ORDER BY title ASC
                    """
                )
                return [_template_row_to_model(r) for r in cur.fetchall()]

        # In-memory path
        with self._lock:
            return sorted(self._templates.values(), key=lambda t: t.title)

    def get_template(
        self,
        template_key: str,
        *,
        conn: object | None = None,
    ) -> AutomationTemplateModel | None:
        """Get a single template by template_key."""
        if conn is None:
            with transaction() as tx:
                return self.get_template(template_key, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, template_key, title, description, category,
                           event_type, condition_json, actions_json,
                           is_system_template, created_at, updated_at, version
                      FROM app_platform_automation_templates
                     WHERE template_key = %s
                    """,
                    (template_key,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return _template_row_to_model(row)

        # In-memory path
        with self._lock:
            return self._templates.get(template_key)

    def create_template(
        self,
        *,
        template_key: str,
        title: str,
        description: str,
        category: str,
        event_type: str,
        condition_json: dict[str, Any],
        actions_json: list[dict[str, Any]],
        is_system_template: bool = False,
        conn: object | None = None,
    ) -> AutomationTemplateModel:
        """Create a new automation template."""
        if conn is None:
            with transaction() as tx:
                return self.create_template(
                    template_key=template_key,
                    title=title,
                    description=description,
                    category=category,
                    event_type=event_type,
                    condition_json=condition_json,
                    actions_json=actions_json,
                    is_system_template=is_system_template,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                template_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO app_platform_automation_templates
                        (id, template_key, title, description, category,
                         event_type, condition_json, actions_json, is_system_template)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    RETURNING id, template_key, title, description, category,
                              event_type, condition_json, actions_json,
                              is_system_template, created_at, updated_at, version
                    """,
                    (
                        template_id, template_key, title, description, category,
                        event_type, json.dumps(condition_json), json.dumps(actions_json),
                        is_system_template,
                    ),
                )
                row = cur.fetchone()
                return _template_row_to_model(row)

        # In-memory path
        now = _utc_now_iso()
        template = AutomationTemplateModel(
            id=str(uuid.uuid4()),
            template_key=template_key,
            title=title,
            description=description,
            category=category,
            event_type=event_type,
            condition_json=dict(condition_json),
            actions_json=list(actions_json),
            is_system_template=is_system_template,
            created_at=now,
            updated_at=now,
            version=1,
        )
        with self._lock:
            self._templates[template_key] = template
        return template

    def update_template(
        self,
        template_key: str,
        *,
        title: str | None = None,
        description: str | None = None,
        condition_json: dict[str, Any] | None = None,
        actions_json: list[dict[str, Any]] | None = None,
        conn: object | None = None,
    ) -> AutomationTemplateModel | None:
        """Update an existing automation template."""
        if conn is None:
            with transaction() as tx:
                return self.update_template(
                    template_key,
                    title=title,
                    description=description,
                    condition_json=condition_json,
                    actions_json=actions_json,
                    conn=tx,
                )

        # Get existing template first
        existing = self.get_template(template_key, conn=conn)
        if existing is None:
            return None

        # Use provided values or keep existing
        new_title = title if title is not None else existing.title
        new_description = description if description is not None else existing.description
        new_condition_json = condition_json if condition_json is not None else existing.condition_json
        new_actions_json = actions_json if actions_json is not None else existing.actions_json

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE app_platform_automation_templates
                       SET title = %s, description = %s,
                           condition_json = %s::jsonb, actions_json = %s::jsonb,
                           updated_at = NOW(), version = version + 1
                     WHERE template_key = %s
                    RETURNING id, template_key, title, description, category,
                              event_type, condition_json, actions_json,
                              is_system_template, created_at, updated_at, version
                    """,
                    (
                        new_title, new_description,
                        json.dumps(new_condition_json), json.dumps(new_actions_json),
                        template_key,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return _template_row_to_model(row)

        # In-memory path
        now = _utc_now_iso()
        updated = AutomationTemplateModel(
            id=existing.id,
            template_key=existing.template_key,
            title=new_title,
            description=new_description,
            category=existing.category,
            event_type=existing.event_type,
            condition_json=new_condition_json,
            actions_json=new_actions_json,
            is_system_template=existing.is_system_template,
            created_at=existing.created_at,
            updated_at=now,
            version=existing.version + 1,
        )
        with self._lock:
            self._templates[template_key] = updated
        return updated

    def delete_template(
        self,
        template_key: str,
        *,
        conn: object | None = None,
    ) -> bool:
        """Delete a template by template_key. Returns True if deleted, False if not found."""
        if conn is None:
            with transaction() as tx:
                return self.delete_template(template_key, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM app_platform_automation_templates WHERE template_key = %s",
                    (template_key,),
                )
                return cur.rowcount > 0

        # In-memory path
        with self._lock:
            if template_key in self._templates:
                del self._templates[template_key]
                return True
            return False
