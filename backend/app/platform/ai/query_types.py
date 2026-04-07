from __future__ import annotations

from enum import StrEnum


class AiCopilotQueryType(StrEnum):
    KPI_OVERVIEW = "kpi_overview"
    ACADEMIC_RISK = "academic_risk"
    AUTOMATION_HEALTH = "automation_health"
    PLATFORM_HEALTH = "platform_health"
    STUDENT_CONTEXT = "student_context"
    FACULTY_CONTEXT = "faculty_context"
    STUDENT_SKILLS = "student_skills"
    MISSING_SKILLS = "missing_skills"
    RECOMMENDED_COURSES = "recommended_courses"
    UNSUPPORTED = "unsupported"
