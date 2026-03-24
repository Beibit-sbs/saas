"""Automation Templates - data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AutomationTemplateModel:
    """A global automation template that serves as a preset for creating rules."""

    id: str  # UUID
    template_key: str  # unique identifier (e.g., "academic-risk-detection")
    title: str  # display title
    description: str  # markdown description
    category: str  # category for grouping (e.g., "Academic", "Administrative")
    event_type: str  # the event this template reacts to
    condition_json: dict[str, Any]  # condition template (can be empty {})
    actions_json: list[dict[str, Any]]  # actions template
    is_system_template: bool  # whether this is a built-in template
    created_at: str  # ISO 8601
    updated_at: str  # ISO 8601
    version: int = 1
