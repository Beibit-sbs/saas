from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


OutboxEventStatus = Literal["pending", "processing", "processed", "failed", "dead_lettered"]


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


class OutboxEventListSchema(BaseModel):
    tenant_id: int
    total: int
    items: list[OutboxEventRead]


class OutboxEventMutationRead(BaseModel):
    event: OutboxEventRead
    idempotent_replay: bool


class TenantCreatedEventPayload(BaseModel):
    tenant_id: int
    slug: str | None = None
    name: str | None = None
    status: str | None = None
    actor: str | None = None

    model_config = ConfigDict(extra="allow")


class StudentCreatedEventPayload(BaseModel):
    student_profile_id: int | str
    person_id: int | str | None = None
    student_number: str | None = None
    current_status: str | None = None
    created_by: str | None = None

    model_config = ConfigDict(extra="allow")


class EnrollmentCreatedEventPayload(BaseModel):
    enrollment_id: int | str | None = None
    student_profile_id: int | str | None = None
    course_id: int | str | None = None
    term_id: int | str | None = None
    enrollment_status: str | None = None
    created_by: str | None = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _require_identity(self) -> "EnrollmentCreatedEventPayload":
        if self.enrollment_id is None and self.student_profile_id is None:
            raise ValueError("enrollment.created requires enrollment_id or student_profile_id")
        return self


class GradeSubmittedEventPayload(BaseModel):
    submission_id: int | str | None = None
    enrollment_id: int | str | None = None
    student_profile_id: int | str | None = None
    grade_code: str | None = None
    grade_points: str | None = None
    submitted_by: str | None = None
    grade_id: str | None = None
    value: float | str | None = None

    model_config = ConfigDict(extra="allow")


class IntegrationUpdatedEventPayload(BaseModel):
    integration_type: str
    actor: str
    fields_updated: list[str] = Field(default_factory=list)
    idempotent_replay: bool = False
    provider: str | None = None
    secret_fields_updated: list[str] = Field(default_factory=list)


class OutboxWorkerResult(BaseModel):
    processed: int
    succeeded: int
    retried: int
    failed: int