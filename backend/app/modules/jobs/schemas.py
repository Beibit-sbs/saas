from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class JobCreate(BaseModel):
    job_type: str = Field(min_length=2, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=20)


class JobResponse(BaseModel):
    id: int
    tenant_id: int
    job_type: str
    status: JobStatus
    payload_json: dict[str, Any]
    result_json: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int
    max_retries: int
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_by: str | None = None
    deduplicated: bool = False
    dedup_key: str | None = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]


class JobResultResponse(BaseModel):
    job: JobResponse


class JobCreateResultResponse(BaseModel):
    job: JobResponse
    idempotent_replay: bool
