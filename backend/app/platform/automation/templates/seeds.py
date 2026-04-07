"""Automation Templates - Seed Data.

This module provides the built-in automation templates that come with the system.
Templates are stored as presets that can be instantiated into actual automation rules.
"""

from typing import Any


SEED_TEMPLATES = [
    {
        "template_key": "academic-risk-detection",
        "title": "Academic Risk Detection",
        "description": "Automatically flag and notify when a student receives a low grade, create task for advisor review.",
        "category": "Academic",
        "event_type": "grade.submitted",
        "condition_json": {
            "field": "grade_points",
            "operator": "<",
            "value": 50,
        },
        "actions_json": [
            {
                "type": "send_notification",
                "channel": "in_app",
                "template": "low_grade_alert",
            },
            {
                "type": "create_task",
                "job_type": "advisor_review",
                "max_retries": 3,
            },
        ],
        "is_system_template": True,
    },
    {
        "template_key": "enrollment-welcome",
        "title": "Student Enrollment Welcome",
        "description": "Send a welcome notification when a new student enrolls.",
        "category": "Onboarding",
        "event_type": "enrollment.created",
        "condition_json": {},  # Always match
        "actions_json": [
            {
                "type": "send_notification",
                "channel": "email",
                "template": "enrollment_welcome",
            },
        ],
        "is_system_template": True,
    },
    {
        "template_key": "tenant-usage-alert",
        "title": "Tenant Usage Alert",
        "description": "Notify administrators when tenant usage exceeds 90% of quota.",
        "category": "Administration",
        "event_type": "tenant.usage_checked",
        "condition_json": {
            "field": "usage_percent",
            "operator": ">=",
            "value": 90,
        },
        "actions_json": [
            {
                "type": "send_notification",
                "channel": "in_app",
                "template": "usage_limit_warning",
            },
        ],
        "is_system_template": True,
    },
    {
        "template_key": "grade-change-approval",
        "title": "Grade Change Approval",
        "description": "Create a task for grade change approval whenever a grade is updated.",
        "category": "Academic",
        "event_type": "grade.updated",
        "condition_json": {},  # Always match
        "actions_json": [
            {
                "type": "create_task",
                "job_type": "grade_change_approval",
                "max_retries": 2,
            },
        ],
        "is_system_template": True,
    },
]


def get_seed_templates() -> list[dict[str, Any]]:
    """Get the list of built-in automation templates."""
    return SEED_TEMPLATES.copy()
