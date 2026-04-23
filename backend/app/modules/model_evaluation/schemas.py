"""Phase XII-XII4: Model Evaluation schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvalRunCreateSchema(BaseModel):
    model_name: str = Field(min_length=1, max_length=256)
    eval_set_name: str = Field(min_length=1, max_length=256)
    metric_names: list[str] = Field(default_factory=lambda: ["accuracy", "latency_ms", "cost_tokens"])
    notes: str | None = Field(default=None, max_length=1000)


class EvalMetricSchema(BaseModel):
    metric_name: str
    value: float
    unit: str | None = None


class EvalRunReadSchema(BaseModel):
    run_id: str
    model_name: str
    eval_set_name: str
    status: Literal["pending", "running", "completed", "failed"]
    metrics: list[EvalMetricSchema]
    notes: str | None
    created_by: str
    created_at: str
    completed_at: str | None


class LeaderboardEntrySchema(BaseModel):
    rank: int
    model_name: str
    eval_set_name: str
    primary_metric: str
    primary_score: float
    run_id: str
    completed_at: str | None


class EvalRunSubmitResultSchema(BaseModel):
    run_id: str
    metrics: list[EvalMetricSchema]
