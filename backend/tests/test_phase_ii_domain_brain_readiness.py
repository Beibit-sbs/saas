"""Phase II — Domain Full Brain-Readiness tests.

Covers:
  II.1 — academic_integrity: get_brain_context service function + /brain-context endpoint
  II.2 — academic_records: get_academic_records_brain_context + /brain-context endpoint
  II.3 — programs: get_programs_brain_context + /brain-context endpoint
  II.4 — courses: get_courses_brain_context + /brain-context endpoint
  II.5 — transcripts: get_transcripts_brain_context service function
  II.6 — student_services: get_student_services_brain_context + /brain-context endpoint
  II.7 — Brain Core academic context source: domain_context enrichment for Phase I3 signals
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch


from tests.conftest import ADMIN_HEADERS, client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakePub:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish_event(self, **kwargs: object) -> dict:
        self.events.append(dict(kwargs))
        return {}


# ---------------------------------------------------------------------------
# II.1 — academic_integrity brain context service
# ---------------------------------------------------------------------------


def test_academic_integrity_brain_context_empty_tenant() -> None:
    """get_brain_context returns expected schema with zero cases."""
    from app.modules.academic_integrity.service import AcademicIntegrityService

    mock_es = MagicMock()
    mock_es.list_entities = AsyncMock(return_value=[])

    svc = AcademicIntegrityService(tenant_entity_service=mock_es)

    # Patch list_integrity_cases to return empty
    async def _fake_list(**kwargs: Any) -> dict:
        return {"cases": [], "total": 0, "page": 1, "page_size": 200}

    svc.list_integrity_cases = _fake_list  # type: ignore[method-assign]

    ctx = asyncio.run(svc.get_brain_context(tenant_id="tenant-1"))

    assert ctx["snapshot_type"] == "brain_context"
    assert ctx["module"] == "academic_integrity"
    assert ctx["total_cases"] == 0
    assert ctx["escalated_cases"] == 0
    assert ctx["integrity_risk_level"] == "low"


def test_academic_integrity_brain_context_escalated() -> None:
    """get_brain_context returns high risk when escalated cases present."""
    from app.modules.academic_integrity.service import AcademicIntegrityService

    mock_es = MagicMock()
    svc = AcademicIntegrityService(tenant_entity_service=mock_es)

    escalated_case = {"id": "c1", "status": "escalated", "case_type": "plagiarism", "student_id": "s1"}

    async def _fake_list(**kwargs: Any) -> dict:
        return {"cases": [escalated_case], "total": 1, "page": 1, "page_size": 200}

    svc.list_integrity_cases = _fake_list  # type: ignore[method-assign]

    ctx = asyncio.run(svc.get_brain_context(tenant_id="tenant-1"))

    assert ctx["escalated_cases"] == 1
    assert ctx["integrity_risk_level"] == "high"


def test_academic_integrity_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/academic-integrity/brain-context returns 200."""
    resp = client.get("/api/admin/academic-integrity/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["snapshot_type"] == "brain_context"
    assert data["module"] == "academic_integrity"
    assert "total_cases" in data
    assert "integrity_risk_level" in data


def test_academic_integrity_brain_context_endpoint_requires_auth() -> None:
    """GET /api/admin/academic-integrity/brain-context without auth returns 401."""
    resp = client.get("/api/admin/academic-integrity/brain-context")
    assert resp.status_code in {401, 403}


# ---------------------------------------------------------------------------
# II.2 — academic_records brain context service
# ---------------------------------------------------------------------------


def test_academic_records_brain_context_zero_records() -> None:
    """get_academic_records_brain_context returns expected schema with no records."""
    from app.modules.academic_records.service import get_academic_records_brain_context

    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=[],
    ):
        ctx = get_academic_records_brain_context(tenant_id=1)

    assert ctx["snapshot_type"] == "brain_context"
    assert ctx["module"] == "academic_records"
    assert ctx["total_records"] == 0
    assert ctx["records_risk_level"] == "low"


def test_academic_records_brain_context_with_issues() -> None:
    """get_academic_records_brain_context reports high risk with many issues."""
    from app.modules.academic_records.service import get_academic_records_brain_context

    # 15 orphaned records -> high risk (>10 issues)
    bad_records = [
        {"id": i, "student_id": None, "course_id": None, "grade": "A", "semester": "2024-1", "status": "published"}
        for i in range(1, 16)
    ]

    with patch(
        "app.modules.academic_records.service.list_entities_for_tenant",
        return_value=bad_records,
    ):
        ctx = get_academic_records_brain_context(tenant_id=1)

    assert ctx["inconsistency_count"] > 0
    assert ctx["records_risk_level"] in {"high", "medium"}


def test_academic_records_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/university/records/brain-context returns 200."""
    resp = client.get("/api/admin/university/records/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["snapshot_type"] == "brain_context"
    assert data["module"] == "academic_records"
    assert "inconsistency_count" in data


# ---------------------------------------------------------------------------
# II.3 — programs brain context service
# ---------------------------------------------------------------------------


def test_programs_brain_context_empty() -> None:
    """get_programs_brain_context returns expected schema with no programs."""
    from app.modules.programs.service import get_programs_brain_context

    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        return_value=[],
    ):
        ctx = get_programs_brain_context(tenant_id=1)

    assert ctx["snapshot_type"] == "brain_context"
    assert ctx["module"] == "programs"
    assert ctx["total_programs"] == 0
    assert ctx["programs_risk_level"] == "low"


def test_programs_brain_context_active_count() -> None:
    """get_programs_brain_context correctly counts active programs."""
    from app.modules.programs.service import get_programs_brain_context

    programs = [
        {"id": 1, "program_code": "CS101", "title": "CS", "degree_type": "bachelor", "status": "active"},
        {"id": 2, "program_code": "EE101", "title": "EE", "degree_type": "master", "status": "inactive"},
    ]

    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        return_value=programs,
    ):
        ctx = get_programs_brain_context(tenant_id=1)

    assert ctx["total_programs"] == 2
    assert ctx["active_programs"] == 1


def test_programs_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/org/programs/brain-context returns 200."""
    resp = client.get("/api/admin/org/programs/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["snapshot_type"] == "brain_context"
    assert data["module"] == "programs"


# ---------------------------------------------------------------------------
# II.4 — courses brain context service
# ---------------------------------------------------------------------------


def test_courses_brain_context_empty() -> None:
    """get_courses_brain_context returns expected schema with no courses."""
    from app.modules.courses.service import get_courses_brain_context

    with patch(
        "app.modules.courses.service.list_entities_for_tenant",
        return_value=[],
    ):
        ctx = get_courses_brain_context(tenant_id=1)

    assert ctx["snapshot_type"] == "brain_context"
    assert ctx["module"] == "courses"
    assert ctx["total_courses"] == 0
    assert ctx["courses_risk_level"] == "low"


def test_courses_brain_context_active_count() -> None:
    """get_courses_brain_context correctly counts active courses."""
    from app.modules.courses.service import get_courses_brain_context

    courses = [
        {"id": 1, "course_code": "CS101", "title": "Intro CS", "credits": 3, "status": "active", "program_id": 1},
        {"id": 2, "course_code": "CS102", "title": "Data Structures", "credits": 3, "status": "inactive", "program_id": 1},
        {"id": 3, "course_code": "CS103", "title": "Algorithms", "credits": 3, "status": "active", "program_id": 1},
    ]

    with patch(
        "app.modules.courses.service.list_entities_for_tenant",
        return_value=courses,
    ):
        ctx = get_courses_brain_context(tenant_id=1)

    assert ctx["total_courses"] == 3
    assert ctx["active_courses"] == 2


def test_courses_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/org/courses/brain-context returns 200."""
    resp = client.get("/api/admin/org/courses/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["snapshot_type"] == "brain_context"
    assert data["module"] == "courses"


# ---------------------------------------------------------------------------
# II.5 — transcripts brain context service (unit-level, no real DB)
# ---------------------------------------------------------------------------


def test_transcripts_brain_context_schema_fields() -> None:
    """get_transcripts_brain_context returns expected schema keys."""
    import app.modules.transcripts.service as ts_mod
    from app.modules.transcripts.schemas import TranscriptTenantConsistencyReportSchema

    fake_report = TranscriptTenantConsistencyReportSchema(
        scanned_student_count=10,
        students_with_issues=2,
        total_issue_count=5,
        reports=[],
    )

    original_list = ts_mod.TranscriptService.list_tenant_transcript_consistency_reports

    async def _fake_list(self: Any, *, tenant_id: int) -> TranscriptTenantConsistencyReportSchema:
        return fake_report

    ts_mod.TranscriptService.list_tenant_transcript_consistency_reports = _fake_list  # type: ignore[method-assign]

    try:
        ctx = asyncio.run(ts_mod.get_transcripts_brain_context(tenant_id=1, db=MagicMock()))
    finally:
        ts_mod.TranscriptService.list_tenant_transcript_consistency_reports = original_list

    assert ctx["snapshot_type"] == "brain_context"
    assert ctx["module"] == "transcripts"
    assert ctx["scanned_student_count"] == 10
    assert ctx["students_with_issues"] == 2
    assert ctx["total_inconsistency_count"] == 5
    assert ctx["transcripts_risk_level"] == "medium"  # 5 issues > 0 → medium


def test_transcripts_brain_context_high_risk() -> None:
    """get_transcripts_brain_context returns high risk when total_issue_count > 10."""
    import app.modules.transcripts.service as ts_mod
    from app.modules.transcripts.schemas import TranscriptTenantConsistencyReportSchema

    fake_report = TranscriptTenantConsistencyReportSchema(
        scanned_student_count=50,
        students_with_issues=15,
        total_issue_count=30,
        reports=[],
    )

    original_list = ts_mod.TranscriptService.list_tenant_transcript_consistency_reports

    async def _fake_list(self: Any, *, tenant_id: int) -> TranscriptTenantConsistencyReportSchema:
        return fake_report

    ts_mod.TranscriptService.list_tenant_transcript_consistency_reports = _fake_list  # type: ignore[method-assign]

    try:
        ctx = asyncio.run(ts_mod.get_transcripts_brain_context(tenant_id=1, db=MagicMock()))
    finally:
        ts_mod.TranscriptService.list_tenant_transcript_consistency_reports = original_list

    assert ctx["transcripts_risk_level"] == "high"


# ---------------------------------------------------------------------------
# II.6 — student_services brain context service + endpoint
# ---------------------------------------------------------------------------


def test_student_services_brain_context_empty() -> None:
    """get_student_services_brain_context returns expected schema with no tickets."""
    from app.modules.student_services.service import get_student_services_brain_context

    with patch(
        "app.modules.student_services.service.list_entities_for_tenant",
        return_value=[],
    ):
        ctx = get_student_services_brain_context(tenant_id=1)

    assert ctx["snapshot_type"] == "brain_context"
    assert ctx["module"] == "student_services"
    assert ctx["total_tickets"] == 0
    assert ctx["open_tickets"] == 0
    assert ctx["student_services_risk_level"] == "low"


def test_student_services_brain_context_escalated() -> None:
    """get_student_services_brain_context returns high risk with open high-priority tickets."""
    from app.modules.student_services.service import get_student_services_brain_context

    tickets = [
        {"id": 1, "status": "open", "priority": "high", "ticket_type": "accommodation"},
        {"id": 2, "status": "open", "priority": "normal", "ticket_type": "counseling"},
        {"id": 3, "status": "resolved", "priority": "high", "ticket_type": "financial"},
    ]

    with patch(
        "app.modules.student_services.service.list_entities_for_tenant",
        return_value=tickets,
    ):
        ctx = get_student_services_brain_context(tenant_id=1)

    assert ctx["total_tickets"] == 3
    assert ctx["open_tickets"] == 2
    assert ctx["escalated_high_priority_tickets"] == 1
    assert ctx["student_services_risk_level"] == "high"


def test_student_services_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/student-services/tickets/brain-context returns 200."""
    resp = client.get("/api/admin/student-services/tickets/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["snapshot_type"] == "brain_context"
    assert data["module"] == "student_services"
    assert "open_tickets" in data


def test_student_services_brain_context_endpoint_requires_auth() -> None:
    """GET /api/admin/student-services/tickets/brain-context without auth returns 401/403."""
    resp = client.get("/api/admin/student-services/tickets/brain-context")
    assert resp.status_code in {401, 403}


# ---------------------------------------------------------------------------
# II.7 — Brain Core academic context source: domain_context enrichment
# ---------------------------------------------------------------------------


def test_fetch_academic_context_basic_fields() -> None:
    """fetch_academic_context returns baseline fields for any signal."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={"student_id": "s1", "course_id": "c1"},
        payload={"attendance_rate": 0.6, "grade_trend": "declining"},
    )

    assert ctx["tenant_id"] == 1
    assert ctx["student_id"] == "s1"
    assert ctx["course_id"] == "c1"
    assert ctx["attendance_rate"] == 0.6
    assert ctx["grade_trend"] == "declining"


def test_fetch_academic_context_enriches_academic_integrity_signal() -> None:
    """fetch_academic_context adds domain_context for academic_integrity event."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={
            "event_type": "academic_integrity.case.escalated",
            "case_id": "case-42",
            "case_type": "plagiarism",
            "student_id": "s-7",
        },
    )

    assert "domain_context" in ctx
    assert ctx["domain_context"]["case_id"] == "case-42"
    assert ctx["domain_context"]["case_type"] == "plagiarism"
    assert ctx["domain_context"]["source_module"] == "academic_integrity"


def test_fetch_academic_context_enriches_academic_records_signal() -> None:
    """fetch_academic_context adds domain_context for academic_records event."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={
            "event_type": "academic_records.inconsistency.detected",
            "issue_count": 7,
        },
    )

    assert "domain_context" in ctx
    assert ctx["domain_context"]["issue_count"] == 7
    assert ctx["domain_context"]["source_module"] == "academic_records"


def test_fetch_academic_context_enriches_programs_signal() -> None:
    """fetch_academic_context adds domain_context for programs event."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={
            "event_type": "programs.status.risk_detected",
            "program_id": 5,
            "issue_count": 2,
        },
    )

    assert "domain_context" in ctx
    assert ctx["domain_context"]["program_id"] == 5
    assert ctx["domain_context"]["source_module"] == "programs"


def test_fetch_academic_context_enriches_courses_signal() -> None:
    """fetch_academic_context adds domain_context for courses event."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={
            "event_type": "courses.status.risk_detected",
            "course_id": 10,
            "issue_count": 1,
        },
    )

    assert "domain_context" in ctx
    assert ctx["domain_context"]["course_id"] == 10
    assert ctx["domain_context"]["source_module"] == "courses"


def test_fetch_academic_context_enriches_transcripts_signal() -> None:
    """fetch_academic_context adds domain_context for transcripts event."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={
            "event_type": "transcripts.inconsistency.detected",
            "issue_count": 3,
        },
    )

    assert "domain_context" in ctx
    assert ctx["domain_context"]["source_module"] == "transcripts"


def test_fetch_academic_context_enriches_student_services_signal() -> None:
    """fetch_academic_context adds domain_context for student_services event."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={
            "event_type": "student_services.ticket.escalated",
            "ticket_id": 99,
            "priority": "high",
        },
    )

    assert "domain_context" in ctx
    assert ctx["domain_context"]["ticket_id"] == 99
    assert ctx["domain_context"]["priority"] == "high"
    assert ctx["domain_context"]["source_module"] == "student_services"


def test_fetch_academic_context_no_domain_context_for_unknown_event() -> None:
    """fetch_academic_context does not add domain_context for unknown event types."""
    from app.modules.brain_core.context_sources.academic import fetch_academic_context

    ctx = fetch_academic_context(
        tenant_id=1,
        subject={},
        payload={"event_type": "scheduling.attendance_risk.detected"},
    )

    assert "domain_context" not in ctx
