from __future__ import annotations

from typing import Any


def _enrich_for_academic_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract academic integrity fields from signal payload."""
    return {
        "case_id": payload.get("case_id"),
        "case_type": payload.get("case_type"),
        "student_id": payload.get("student_id"),
        "source_module": "academic_integrity",
    }


def _enrich_for_academic_records(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract academic records fields from signal payload."""
    return {
        "issue_count": payload.get("issue_count"),
        "source_module": "academic_records",
    }


def _enrich_for_programs(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract programs fields from signal payload."""
    return {
        "program_id": payload.get("program_id"),
        "issue_count": payload.get("issue_count"),
        "source_module": "programs",
    }


def _enrich_for_courses(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract courses fields from signal payload."""
    return {
        "course_id": payload.get("course_id"),
        "issue_count": payload.get("issue_count"),
        "source_module": "courses",
    }


def _enrich_for_transcripts(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract transcripts fields from signal payload."""
    return {
        "issue_count": payload.get("issue_count"),
        "source_module": "transcripts",
    }


def _enrich_for_student_services(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract student services fields from signal payload."""
    return {
        "ticket_id": payload.get("ticket_id"),
        "priority": payload.get("priority"),
        "source_module": "student_services",
    }


# Map event_type prefix → domain enrichment function
_DOMAIN_ENRICHERS: dict[str, Any] = {
    "academic_integrity": _enrich_for_academic_integrity,
    "academic_records": _enrich_for_academic_records,
    "programs": _enrich_for_programs,
    "courses": _enrich_for_courses,
    "transcripts": _enrich_for_transcripts,
    "student_services": _enrich_for_student_services,
}


def fetch_academic_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return academic context slice for Brain Core decisions."""
    base: dict[str, Any] = {
        "student_id": subject.get("student_id") or payload.get("student_id"),
        "course_id": subject.get("course_id") or payload.get("course_id"),
        "section_id": subject.get("section_id") or payload.get("section_id"),
        "attendance_rate": payload.get("attendance_rate"),
        "grade_trend": payload.get("grade_trend"),
        "tenant_id": tenant_id,
    }

    # Enrich with domain-specific fields from payload based on event type
    event_type: str = str(payload.get("event_type") or subject.get("event_type") or "")
    for prefix, enricher in _DOMAIN_ENRICHERS.items():
        if event_type.startswith(prefix):
            base["domain_context"] = enricher(payload)
            break

    return base
