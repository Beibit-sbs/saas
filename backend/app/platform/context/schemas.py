from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ContextEntityRead(BaseModel):
    id: int
    tenant_id: int
    entity_type: str
    entity_id: str
    data_json: dict[str, Any]
    created_at: str
    updated_at: str


class ContextRelationRead(BaseModel):
    id: int
    tenant_id: int
    source_entity_type: str
    source_entity_id: str
    relation_type: str
    target_entity_type: str
    target_entity_id: str
    metadata_json: dict[str, Any]
    created_at: str


class StudentProfileRead(BaseModel):
    """Full semantic profile of a student — base object for AI reasoning."""

    student: dict[str, Any] | None
    program: dict[str, Any] | None
    advisor: dict[str, Any] | None
    enrollments: list[dict[str, Any]]
    grades: list[dict[str, Any]]
    department: dict[str, Any] | None
    automation_flags: dict[str, Any]
