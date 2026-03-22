from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class ProfileStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DegreeType(str, Enum):
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    DIPLOMA = "diploma"
    CERTIFICATE = "certificate"
    OTHER = "other"


class PersonBaseSchema(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    phone: str | None = Field(None, max_length=32)
    external_person_key: str | None = Field(None, max_length=128)
    status: ProfileStatus = Field(ProfileStatus.ACTIVE)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be a valid address")
        return normalized


class PersonCreateSchema(PersonBaseSchema):
    pass


class PersonUpdateSchema(BaseModel):
    version: int = Field(..., ge=1)
    email: str | None = Field(None, min_length=5, max_length=255)
    first_name: str | None = Field(None, min_length=1, max_length=128)
    last_name: str | None = Field(None, min_length=1, max_length=128)
    phone: str | None = Field(None, max_length=32)
    external_person_key: str | None = Field(None, max_length=128)
    status: ProfileStatus | None = None
    metadata_json: dict | None = None

    @field_validator("email")
    @classmethod
    def validate_optional_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be a valid address")
        return normalized

    @model_validator(mode="after")
    def validate_has_mutations(self) -> "PersonUpdateSchema":
        if all(
            value is None
            for value in (
                self.email,
                self.first_name,
                self.last_name,
                self.phone,
                self.external_person_key,
                self.status,
                self.metadata_json,
            )
        ):
            raise ValueError("at least one mutable field must be provided")
        return self


class PersonReadSchema(PersonBaseSchema):
    id: int
    tenant_id: int
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonListResponseSchema(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    items: list[PersonReadSchema]


class DepartmentBaseSchema(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=255)
    parent_department_id: int | None = Field(None, gt=0)
    status: ProfileStatus = Field(ProfileStatus.ACTIVE)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("code is required")
        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name is required")
        return normalized


class DepartmentCreateSchema(DepartmentBaseSchema):
    pass


class DepartmentReadSchema(DepartmentBaseSchema):
    id: int
    tenant_id: int
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgramBaseSchema(BaseModel):
    department_id: int = Field(..., gt=0)
    code: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=255)
    degree_type: DegreeType
    status: ProfileStatus = Field(ProfileStatus.ACTIVE)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("code is required")
        return normalized

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("title is required")
        return normalized


class ProgramCreateSchema(ProgramBaseSchema):
    pass


class ProgramReadSchema(ProgramBaseSchema):
    id: int
    tenant_id: int
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentCreateSchema(BaseModel):
    person_id: int = Field(..., gt=0)
    program_id: int = Field(..., gt=0)
    student_number: str = Field(..., min_length=1, max_length=64)
    cohort_year: int = Field(..., ge=2020, le=2099)
    status: ProfileStatus = Field(ProfileStatus.ACTIVE)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("student_number")
    @classmethod
    def normalize_student_number(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("student_number is required")
        return normalized


class StudentReadSchema(BaseModel):
    id: int
    tenant_id: int
    person_id: int
    program_id: int
    student_number: str
    cohort_year: int
    status: ProfileStatus
    metadata_json: dict
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FacultyCreateSchema(BaseModel):
    person_id: int = Field(..., gt=0)
    department_id: int = Field(..., gt=0)
    faculty_number: str = Field(..., min_length=1, max_length=64)
    academic_title: str | None = Field(None, max_length=128)
    status: ProfileStatus = Field(ProfileStatus.ACTIVE)
    metadata_json: dict = Field(default_factory=dict)

    @field_validator("faculty_number")
    @classmethod
    def normalize_faculty_number(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("faculty_number is required")
        return normalized


class FacultyReadSchema(BaseModel):
    id: int
    tenant_id: int
    person_id: int
    department_id: int
    faculty_number: str
    academic_title: str | None
    status: ProfileStatus
    metadata_json: dict
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}