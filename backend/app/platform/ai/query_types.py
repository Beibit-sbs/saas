from __future__ import annotations

from enum import StrEnum


class AiCopilotQueryType(StrEnum):
    KPI_OVERVIEW = "kpi_overview"
    ACADEMIC_RISK = "academic_risk"
    AUTOMATION_HEALTH = "automation_health"
    PLATFORM_HEALTH = "platform_health"
    STUDENT_CONTEXT = "student_context"
    UNSUPPORTED = "unsupported"
