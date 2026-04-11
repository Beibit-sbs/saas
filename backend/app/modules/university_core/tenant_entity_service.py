"""Tenant-aware facade for shared university entity CRUD helpers."""

from pydantic import BaseModel, Field

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


class UniversityCoreConsistencyIssueSchema(BaseModel):
    issue_type: str
    entity_name: str
    item_id: int | None = None
    reference_field: str | None = None
    reference_id: int | None = None
    detail: str


class UniversityCoreConsistencyReportSchema(BaseModel):
    tenant_id: int = Field(..., ge=1)
    entity_counts: dict[str, int] = Field(default_factory=dict)
    issue_count: int = Field(..., ge=0)
    issues: list[UniversityCoreConsistencyIssueSchema] = Field(default_factory=list)


def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_tenant_entity_consistency_report(tenant_id: int) -> UniversityCoreConsistencyReportSchema:
    students = list_entities_for_tenant("students", tenant_id)
    programs = list_entities_for_tenant("programs", tenant_id)
    courses = list_entities_for_tenant("courses", tenant_id)
    enrollments = list_entities_for_tenant("enrollments", tenant_id)
    records = list_entities_for_tenant("academic_records", tenant_id)

    student_ids = {item_id for item_id in (_safe_int(item.get("id")) for item in students) if item_id is not None}
    program_ids = {item_id for item_id in (_safe_int(item.get("id")) for item in programs) if item_id is not None}
    course_ids = {item_id for item_id in (_safe_int(item.get("id")) for item in courses) if item_id is not None}

    issues: list[UniversityCoreConsistencyIssueSchema] = []

    for entity_name, rows in {
        "students": students,
        "programs": programs,
        "courses": courses,
        "enrollments": enrollments,
        "academic_records": records,
    }.items():
        for row in rows:
            item_id = _safe_int(row.get("id"))
            tenant_marker = str(row.get("tenant_id") or "").strip()
            if not tenant_marker:
                issues.append(
                    UniversityCoreConsistencyIssueSchema(
                        issue_type="missing_tenant_marker",
                        entity_name=entity_name,
                        item_id=item_id,
                        detail="Entity row is missing tenant_id marker.",
                    )
                )

    for course in courses:
        course_id = _safe_int(course.get("id"))
        program_id = _safe_int(course.get("program_id"))
        if program_id is None or program_id not in program_ids:
            issues.append(
                UniversityCoreConsistencyIssueSchema(
                    issue_type="course_missing_program",
                    entity_name="courses",
                    item_id=course_id,
                    reference_field="program_id",
                    reference_id=program_id,
                    detail="Course references a program that does not exist in tenant scope.",
                )
            )

    for entity_name, rows in {
        "enrollments": enrollments,
        "academic_records": records,
    }.items():
        for row in rows:
            item_id = _safe_int(row.get("id"))
            student_id = _safe_int(row.get("student_id"))
            course_id = _safe_int(row.get("course_id"))

            if student_id is None or student_id not in student_ids:
                issues.append(
                    UniversityCoreConsistencyIssueSchema(
                        issue_type=f"{entity_name.rstrip('s')}_missing_student",
                        entity_name=entity_name,
                        item_id=item_id,
                        reference_field="student_id",
                        reference_id=student_id,
                        detail="Entity references a student that does not exist in tenant scope.",
                    )
                )
            if course_id is None or course_id not in course_ids:
                issues.append(
                    UniversityCoreConsistencyIssueSchema(
                        issue_type=f"{entity_name.rstrip('s')}_missing_course",
                        entity_name=entity_name,
                        item_id=item_id,
                        reference_field="course_id",
                        reference_id=course_id,
                        detail="Entity references a course that does not exist in tenant scope.",
                    )
                )

    return UniversityCoreConsistencyReportSchema(
        tenant_id=tenant_id,
        entity_counts={
            "students": len(students),
            "programs": len(programs),
            "courses": len(courses),
            "enrollments": len(enrollments),
            "academic_records": len(records),
        },
        issue_count=len(issues),
        issues=issues,
    )

__all__ = [
    "list_entities_for_tenant",
    "create_entity_for_tenant",
    "update_entity_for_tenant",
    "delete_entity_for_tenant",
    "UniversityCoreConsistencyIssueSchema",
    "UniversityCoreConsistencyReportSchema",
    "get_tenant_entity_consistency_report",
]
