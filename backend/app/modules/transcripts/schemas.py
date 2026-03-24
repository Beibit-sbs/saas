from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TranscriptItemSchema(BaseModel):
    enrollment_id: int
    term_id: int
    term_code: str | None
    term_name: str | None
    course_id: int
    course_code: str | None
    course_title: str | None
    credits: int
    grade_code: str | None
    grade_points: Decimal | None


class StudentTranscriptSchema(BaseModel):
    student_profile_id: int
    total_credits: int
    gpa: Decimal | None
    items: list[TranscriptItemSchema]


class TranscriptRecordReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    enrollment_id: int
    course_id: int
    term_id: int
    grade_code: str | None
    grade_points: Decimal | None
    credits: int
    recorded_at: datetime
    version: int
    metadata_json: dict


class TranscriptSnapshotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    student_profile_id: int
    snapshot_json: dict
    generated_by: str
    generated_at: datetime
