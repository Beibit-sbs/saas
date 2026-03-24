from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.platform.developer.models import DeveloperAppStatus, DeveloperInstallationStatus


class DeveloperAppCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    owner_email: str = Field(min_length=3, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    webhook_url: str | None = Field(default=None, max_length=1024)

    @field_validator("owner_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email address")
        return v.strip().lower()



class DeveloperAppReadSchema(BaseModel):
    id: int
    name: str
    app_key: str
    description: str
    owner_email: str
    status: DeveloperAppStatus
    webhook_url: str | None = None
    scopes: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class DeveloperAppSecretReadSchema(DeveloperAppReadSchema):
    app_secret: str


class DeveloperAppInstallSchema(BaseModel):
    tenant_id: int = Field(gt=0)


class DeveloperAppInstallationReadSchema(BaseModel):
    id: int
    app_id: int
    tenant_id: int
    status: DeveloperInstallationStatus
    installed_by: str
    created_at: str


class DeveloperApiLogReadSchema(BaseModel):
    id: int
    app_id: int
    tenant_id: int
    endpoint: str
    status_code: int
    latency_ms: float
    created_at: str


class DeveloperAppEventSubscriptionCreateSchema(BaseModel):
    event_type: str = Field(min_length=2, max_length=255)


class DeveloperAppEventSubscriptionReadSchema(BaseModel):
    id: int
    app_id: int
    event_type: str
    created_at: str


class PublicStudentReadSchema(BaseModel):
    id: int
    tenant_id: int | str | None = None
    student_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    status: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PublicEnrollmentReadSchema(BaseModel):
    id: int
    tenant_id: int | str | None = None
    student_id: int | None = None
    course_id: int | None = None
    semester: str | None = None
    status: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PublicGradeReadSchema(BaseModel):
    id: int
    tenant_id: int
    enrollment_id: int
    grade_code: str
    grade_points: str
    grading_scale_id: int
    submitted_by: str
    submitted_at: str