from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from app.core.db import get_raw_conn

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


@dataclass(frozen=True)
class EntityConfig:
    table: str
    fields: tuple[str, ...]
    required: tuple[str, ...]
    fk_fields: tuple[str, ...] = ()


ENTITY_CONFIGS: dict[str, EntityConfig] = {
    "students": EntityConfig(
        table="university_students",
        fields=("student_id", "first_name", "last_name", "email", "status", "tenant_id"),
        required=("student_id", "first_name", "last_name", "email", "status"),
    ),
    "faculty": EntityConfig(
        table="university_faculty",
        fields=("faculty_id", "first_name", "last_name", "department", "email", "status", "tenant_id"),
        required=("faculty_id", "first_name", "last_name", "department", "email", "status"),
    ),
    "faculty_contracts": EntityConfig(
        table="university_faculty_contracts",
        fields=(
            "faculty_id",
            "contract_type",
            "start_date",
            "end_date",
            "fte_ratio",
            "max_credit_hours",
            "status",
            "notes",
            "tenant_id",
        ),
        required=(
            "faculty_id",
            "contract_type",
            "start_date",
            "fte_ratio",
            "max_credit_hours",
            "status",
        ),
        fk_fields=(),
    ),
    "programs": EntityConfig(
        table="university_programs",
        fields=("program_code", "title", "degree_type", "faculty", "status", "tenant_id"),
        required=("program_code", "title", "degree_type", "faculty", "status"),
    ),
    "courses": EntityConfig(
        table="university_courses",
        fields=("course_code", "title", "credits", "program_id", "status", "tenant_id"),
        required=("course_code", "title", "credits", "program_id", "status"),
        fk_fields=("program_id",),
    ),
    "enrollments": EntityConfig(
        table="university_enrollments",
        fields=("student_id", "course_id", "semester", "status", "tenant_id"),
        required=("student_id", "course_id", "semester", "status"),
        fk_fields=("student_id", "course_id"),
    ),
    "academic_records": EntityConfig(
        table="university_academic_records",
        fields=("student_id", "course_id", "grade", "semester", "status", "tenant_id"),
        required=("student_id", "course_id", "grade", "semester", "status"),
        fk_fields=("student_id", "course_id"),
    ),
    "advising_sessions": EntityConfig(
        table="university_advising_sessions",
        fields=(
            "student_id",
            "advisor_id",
            "session_type",
            "status",
            "scheduled_at",
            "notes",
            "outcome",
            "tenant_id",
        ),
        required=("student_id", "advisor_id", "session_type", "status"),
        fk_fields=(),
    ),
    "student_service_tickets": EntityConfig(
        table="university_student_service_tickets",
        fields=(
            "student_id",
            "category",
            "subject",
            "description",
            "priority",
            "status",
            "owner_id",
            "channel",
            "resolution_notes",
            "tenant_id",
        ),
        required=("student_id", "category", "subject", "description", "priority", "status"),
        fk_fields=(),
    ),
    "career_opportunities": EntityConfig(
        table="university_career_opportunities",
        fields=(
            "student_id",
            "title",
            "company",
            "opportunity_type",
            "status",
            "owner_id",
            "start_date",
            "notes",
            "tenant_id",
        ),
        required=("student_id", "title", "company", "opportunity_type", "status"),
        fk_fields=(),
    ),
    "financial_aid_records": EntityConfig(
        table="university_financial_aid_records",
        fields=(
            "student_id",
            "aid_type",
            "amount",
            "currency",
            "status",
            "term",
            "reviewer_id",
            "notes",
            "tenant_id",
        ),
        required=("student_id", "aid_type", "amount", "currency", "status", "term"),
        fk_fields=(),
    ),
    "housing_requests": EntityConfig(
        table="university_housing_requests",
        fields=(
            "student_id",
            "request_type",
            "dormitory",
            "room_preference",
            "status",
            "manager_id",
            "notes",
            "tenant_id",
        ),
        required=("student_id", "request_type", "dormitory", "status"),
        fk_fields=(),
    ),
    "alumni_records": EntityConfig(
        table="university_alumni_records",
        fields=(
            "student_id",
            "graduation_year",
            "status",
            "engagement_type",
            "employer",
            "contact_email",
            "notes",
            "tenant_id",
        ),
        required=("student_id", "graduation_year", "status", "engagement_type"),
        fk_fields=(),
    ),
}


@dataclass
class UniversityMemoryState:
    data: dict[str, dict[int, dict[str, object]]] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)


_state_lock = Lock()
_state = UniversityMemoryState(
    data={name: {} for name in ENTITY_CONFIGS},
    counters={name: 0 for name in ENTITY_CONFIGS},
)


def clear_university_state() -> None:
    with _state_lock:
        for name in ENTITY_CONFIGS:
            _state.data[name].clear()
            _state.counters[name] = 0


__all__ = [
    "EntityConfig",
    "ENTITY_CONFIGS",
    "UniversityMemoryState",
    "_state",
    "_state_lock",
    "clear_university_state",
    "get_raw_conn",
    "psycopg",
]
