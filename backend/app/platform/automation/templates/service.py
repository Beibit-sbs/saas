"""Automation Templates Service - business logic for template operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.platform.automation import service as automation_service
from app.platform.automation.templates.models import AutomationTemplateModel

if TYPE_CHECKING:
    from app.core.uow import UnitOfWork


def list_templates(
    *,
    uow: UnitOfWork,
) -> list[AutomationTemplateModel]:
    """List all automation templates."""
    return uow.automation_template_repository.list_templates(conn=uow.conn)


def get_template(
    *,
    template_key: str,
    uow: UnitOfWork,
) -> AutomationTemplateModel | None:
    """Get a single template by key."""
    return uow.automation_template_repository.get_template(template_key, conn=uow.conn)


def create_template(
    *,
    template_key: str,
    title: str,
    description: str,
    category: str,
    event_type: str,
    condition_json: dict[str, Any],
    actions_json: list[dict[str, Any]],
    is_system_template: bool = False,
    uow: UnitOfWork,
) -> AutomationTemplateModel:
    """Create a new automation template."""
    return uow.automation_template_repository.create_template(
        template_key=template_key,
        title=title,
        description=description,
        category=category,
        event_type=event_type,
        condition_json=condition_json,
        actions_json=actions_json,
        is_system_template=is_system_template,
        conn=uow.conn,
    )


def instantiate_template(
    *,
    template_key: str,
    tenant_id: int,
    rule_name: str | None = None,
    rule_description: str | None = None,
    uow: UnitOfWork,
) -> Any:
    """
    Instantiate a template into an automation rule.
    
    Steps:
    1. Load template by template_key
    2. Generate new rule from template
    3. Save rule using existing AutomationRuleRepository
    4. Return created rule
    """
    # Load template
    template = get_template(template_key=template_key, uow=uow)
    if template is None:
        raise ValueError(f"Template not found: {template_key}")

    # Determine rule name and description
    final_name = rule_name if rule_name else template.title
    final_description = rule_description if rule_description else template.description

    # Create rule from template
    rule = automation_service.create_rule(
        tenant_id=tenant_id,
        name=final_name,
        description=final_description,
        event_type=template.event_type,
        condition_json=template.condition_json,  # Use template's condition
        actions_json=template.actions_json,  # Use template's actions
        is_active=True,
        uow=uow,
    )

    return rule
