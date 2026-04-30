"""Academic Integrity Pydantic schemas for API contracts."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class IntegrityCaseStatus(str, Enum):
    """Integrity case lifecycle states."""
    FLAGGED = "flagged"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class IntegrityCaseType(str, Enum):
    """Types of academic integrity violations."""
    PLAGIARISM = "plagiarism"
    UNAUTHORIZED_COLLABORATION = "unauthorized_collaboration"
    UNAUTHORIZED_AID = "unauthorized_aid"
    FABRICATION = "fabrication"
    CHEATING = "cheating"


class IntegrityCaseCreateSchema(BaseModel):
    """Request schema for creating an integrity case."""
    student_id: str = Field(..., description="Student UUID")
    course_id: str = Field(..., description="Course UUID")
    assignment_id: Optional[str] = Field(None, description="Assignment UUID if applicable")
    case_type: IntegrityCaseType = Field(..., description="Type of violation")
    description: str = Field(..., min_length=10, description="Detailed description of suspicion")
    evidence_url: Optional[str] = Field(None, description="URL to evidence (plagiarism report, etc)")
    priority: str = Field("normal", description="Case priority: low, normal, high")
    reviewer_notes: Optional[str] = Field(None, max_length=500, description="Optional reviewer notes")


class IntegrityCaseStatusUpdateSchema(BaseModel):
    """Request schema for updating case status."""
    status: IntegrityCaseStatus = Field(..., description="New status")
    resolution_notes: Optional[str] = Field(None, description="Notes on resolution/dismissal")
    recommended_action: Optional[str] = Field(None, description="Recommended action (warning, grade penalty, etc)")


class IntegrityCaseRecordSchema(BaseModel):
    """Response schema for integrity case record."""
    id: str
    student_id: str
    course_id: str
    assignment_id: Optional[str]
    case_type: IntegrityCaseType
    description: str
    evidence_url: Optional[str]
    priority: str
    status: IntegrityCaseStatus
    resolution_notes: Optional[str]
    recommended_action: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    tenant_id: str

    model_config = ConfigDict(from_attributes=True)


class IntegrityCaseListResponseSchema(BaseModel):
    """Response schema for listing integrity cases."""
    cases: list[IntegrityCaseRecordSchema]
    total: int
    page: int
    page_size: int


class IntegrityCaseDetailResponseSchema(BaseModel):
    """Response schema for single integrity case with details."""
    case: IntegrityCaseRecordSchema
