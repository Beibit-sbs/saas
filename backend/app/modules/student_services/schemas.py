from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


StudentTicketPriority = Literal["low", "medium", "high", "urgent"]
StudentTicketStatus = Literal["open", "in_progress", "resolved", "closed"]


class StudentServiceTicketBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    category: str = Field(min_length=1, max_length=64)
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=3000)
    priority: StudentTicketPriority = "medium"
    status: StudentTicketStatus = "open"
    owner_id: str | None = Field(default=None, max_length=64)
    channel: str = Field(default="portal", min_length=1, max_length=32)
    resolution_notes: str | None = Field(default=None, max_length=3000)


class StudentServiceTicketCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    category: str = Field(min_length=1, max_length=64)
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=3000)
    priority: StudentTicketPriority = "medium"
    owner_id: str | None = Field(default=None, max_length=64)
    channel: str = Field(default="portal", min_length=1, max_length=32)


class StudentServiceTicketStatusUpdateSchema(BaseModel):
    status: StudentTicketStatus
    resolution_notes: str | None = Field(default=None, max_length=3000)


class StudentServiceTicketSchema(StudentServiceTicketBaseSchema):
    id: int
    tenant_id: str | None = None


class StudentServiceTicketListResponseSchema(BaseModel):
    items: list[StudentServiceTicketSchema]


class StudentServiceTicketItemResponseSchema(BaseModel):
    item: StudentServiceTicketSchema
