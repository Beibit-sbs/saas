from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CopilotSourceReferenceSchema(BaseModel):
    source_type: str
    reference: str


class CopilotInsightCardSchema(BaseModel):
    title: str
    value: str
    explanation: str


class CopilotQuestionRequestSchema(BaseModel):
    tenant_id: int
    question: str = Field(min_length=1, max_length=2000)
    context: dict[str, Any] | None = None


class CopilotAnswerReadSchema(BaseModel):
    question: str
    summary: str
    insights: list[CopilotInsightCardSchema]
    sources: list[CopilotSourceReferenceSchema]
    warnings: list[str]


class CopilotQueryLogReadSchema(BaseModel):
    id: int
    tenant_id: int
    actor_id: str
    question: str
    query_type: str
    retrieved_sources_json: list[dict[str, Any]]
    answer_json: dict[str, Any]
    created_at: str
