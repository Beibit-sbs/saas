"""
Deterministic recommendation rule catalog for AI Copilot Phase 1.1.

Each factory function receives the retrieved context dict and returns a
CopilotRecommendationSchema if the rule fires, or None if it does not.
All rules are pure functions: no side effects, no I/O.
"""
from __future__ import annotations

from typing import Any

from app.platform.ai.recommendations.schemas import (
    CopilotRecommendationActionSchema,
    CopilotRecommendationSchema,
)


def _rule_academic_risk_followup(
    context: dict[str, Any],
) -> CopilotRecommendationSchema | None:
    """Fires when retrieved context contains at-risk students."""
    at_risk_count = int(context.get("at_risk_count") or 0)
    if at_risk_count <= 0:
        return None
    return CopilotRecommendationSchema(
        recommendation_type="academic_risk_followup",
        title="Follow up with at-risk students",
        priority="high" if at_risk_count >= 5 else "medium",
        reason=f"{at_risk_count} student(s) are flagged as academically at risk and may need immediate support.",
        suggested_actions=[
            CopilotRecommendationActionSchema(
                action_type="navigate",
                label="View Academic Risk Report",
                target="/console/analytics/academic-risk",
            ),
            CopilotRecommendationActionSchema(
                action_type="review",
                label="Review student engagement metrics",
                target="/console/analytics/engagement",
            ),
        ],
    )


def _rule_automation_rule_health_review(
    context: dict[str, Any],
) -> CopilotRecommendationSchema | None:
    """Fires when any automation rules have a failing or degraded status."""
    unhealthy_rules = int(context.get("unhealthy_rules") or 0)
    if unhealthy_rules <= 0:
        return None
    return CopilotRecommendationSchema(
        recommendation_type="automation_rule_health_review",
        title="Review failing automation rules",
        priority="high" if unhealthy_rules >= 3 else "medium",
        reason=f"{unhealthy_rules} automation rule(s) have a failing or degraded status.",
        suggested_actions=[
            CopilotRecommendationActionSchema(
                action_type="navigate",
                label="Open Automation Dashboard",
                target="/console/automation",
            ),
        ],
    )


def _rule_failed_jobs_attention(
    context: dict[str, Any],
) -> CopilotRecommendationSchema | None:
    """Fires when the platform has a significant number of failed background jobs."""
    failed_jobs = int(context.get("failed_jobs") or 0)
    if failed_jobs < 5:
        return None
    return CopilotRecommendationSchema(
        recommendation_type="failed_jobs_attention",
        title="Investigate failed background jobs",
        priority="high" if failed_jobs >= 20 else "medium",
        reason=f"{failed_jobs} background job(s) have failed and may require manual retry or investigation.",
        suggested_actions=[
            CopilotRecommendationActionSchema(
                action_type="navigate",
                label="View Job Queue",
                target="/console/platform/jobs",
            ),
        ],
    )


def _rule_failed_notifications_attention(
    context: dict[str, Any],
) -> CopilotRecommendationSchema | None:
    """Fires when too many notifications have failed delivery."""
    failed_notifications = int(context.get("failed_notifications") or 0)
    if failed_notifications < 10:
        return None
    return CopilotRecommendationSchema(
        recommendation_type="failed_notifications_attention",
        title="Investigate failed notifications",
        priority="medium",
        reason=f"{failed_notifications} notification(s) failed to deliver. Check provider configuration.",
        suggested_actions=[
            CopilotRecommendationActionSchema(
                action_type="navigate",
                label="View Notification Logs",
                target="/console/platform/notifications",
            ),
        ],
    )


def _rule_enrollment_drop_attention(
    context: dict[str, Any],
) -> CopilotRecommendationSchema | None:
    """Fires when total enrollments are significantly below the historical average."""
    total_enrollments = int(context.get("total_enrollments") or 0)
    avg_enrollments = int(context.get("avg_enrollments") or 0)
    if avg_enrollments <= 0:
        return None
    drop_rate = (avg_enrollments - total_enrollments) / avg_enrollments
    if drop_rate < 0.30:
        return None
    return CopilotRecommendationSchema(
        recommendation_type="enrollment_drop_attention",
        title="Enrollment numbers are below average",
        priority="medium",
        reason=(
            f"Current enrollments ({total_enrollments}) are {int(drop_rate * 100)}% below "
            f"the historical average ({avg_enrollments}). Consider reviewing course availability."
        ),
        suggested_actions=[
            CopilotRecommendationActionSchema(
                action_type="navigate",
                label="View Enrollment Analytics",
                target="/console/analytics/enrollments",
            ),
        ],
    )


def _rule_low_activity_attention(
    context: dict[str, Any],
) -> CopilotRecommendationSchema | None:
    """Fires when the platform activity score is critically low."""
    activity_score = float(context.get("activity_score") or 0.0)
    if activity_score > 0.20:
        return None
    return CopilotRecommendationSchema(
        recommendation_type="low_activity_attention",
        title="Platform activity is critically low",
        priority="high" if activity_score <= 0.05 else "medium",
        reason=(
            f"Platform activity score is {activity_score:.0%}, which is critically low. "
            "Consider re-engagement campaigns or check for technical issues."
        ),
        suggested_actions=[
            CopilotRecommendationActionSchema(
                action_type="navigate",
                label="View Activity Dashboard",
                target="/console/analytics",
            ),
        ],
    )


# Ordered catalog — rules are evaluated top-to-bottom, all matching rules fire.
RULE_CATALOG = [
    _rule_academic_risk_followup,
    _rule_automation_rule_health_review,
    _rule_failed_jobs_attention,
    _rule_failed_notifications_attention,
    _rule_enrollment_drop_attention,
    _rule_low_activity_attention,
]


def evaluate_rules(context: dict[str, Any]) -> list[CopilotRecommendationSchema]:
    """Evaluate all rules against the given context and return matching recommendations."""
    results: list[CopilotRecommendationSchema] = []
    for rule in RULE_CATALOG:
        rec = rule(context)
        if rec is not None:
            results.append(rec)
    return results
