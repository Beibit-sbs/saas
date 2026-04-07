from __future__ import annotations


def build_audit_action(module: str, entity: str, action: str) -> str:
    """Build a canonical audit action: <module>.<entity>.<action>."""
    module_value = module.strip().lower()
    entity_value = entity.strip().lower()
    action_value = action.strip().lower()

    if not module_value or not entity_value or not action_value:
        raise ValueError("module, entity, and action are required for audit action naming")

    return f"{module_value}.{entity_value}.{action_value}"
