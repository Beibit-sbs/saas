from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


OutboxEventStatus = Literal["pending", "processing", "processed", "failed"]


class OutboxEventRead(BaseModel):
    id: int
    tenant_id: int
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload_json: dict[str, Any]
    status: OutboxEventStatus
    retry_count: int
    available_at: str
    created_at: str
    processed_at: str | None = None
    last_error: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None


class OutboxEventPublishRequest(BaseModel):
    tenant_id: int = Field(gt=0)
    event_type: str = Field(min_length=3, max_length=128)
    aggregate_type: str = Field(min_length=2, max_length=128)
    aggregate_id: str = Field(min_length=1, max_length=255)
    payload_json: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = Field(default=None, max_length=255)
    causation_id: str | None = Field(default=None, max_length=255)


class TenantCreatedEventPayload(BaseModel):
    tenant_id: int
    slug: str
    name: str
    status: str
    actor: str | None = None


class StudentCreatedEventPayload(BaseModel):
    student_profile_id: int
    person_id: int
    student_number: str
    current_status: str
    created_by: str


class EnrollmentCreatedEventPayload(BaseModel):
    enrollment_id: int
    student_profile_id: int
    course_id: int
    term_id: int
    enrollment_status: str
    created_by: str


class GradeSubmittedEventPayload(BaseModel):
    submission_id: int
    enrollment_id: int
    student_profile_id: int
    grade_code: str
    grade_points: str
    submitted_by: str


class OutboxWorkerResult(BaseModel):
    processed: int
    succeeded: int
    retried: int
    failed: int