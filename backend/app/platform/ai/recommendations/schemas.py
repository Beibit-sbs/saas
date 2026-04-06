from __future__ import annotations

from pydantic import BaseModel


class CopilotRecommendationActionSchema(BaseModel):
    action_type: str  # e.g. "navigate", "review", "alert"
    label: str
    target: str | None = None  # e.g. route path or resource reference


class CopilotRecommendationSchema(BaseModel):
    recommendation_type: str
    title: str
    priority: str  # "high" | "medium" | "low"
    reason: str
    suggested_actions: list[CopilotRecommendationActionSchema]
    created_intervention_case_id: int | None = None


class CopilotRecommendationResponseSchema(BaseModel):
    question: str
    summary: str
    recommendations: list[CopilotRecommendationSchema]
    sources: list[str]
    warnings: list[str]
