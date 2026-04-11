from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterator
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.main import app
from app.modules.rbac import service as rbac_service
from app.modules.transcripts import service as transcripts_service
from app.modules.transcripts.dependencies import get_transcripts_db
from app.modules.transcripts.schemas import (
    StudentTranscriptSchema,
    TranscriptConsistencyIssueSchema,
    TranscriptConsistencyReportSchema,
    TranscriptTenantConsistencyReportSchema,
    TranscriptItemSchema,
    TranscriptSnapshotSchema,
)
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client


@pytest.fixture(autouse=True)
def _enable_transcripts_permissions_for_admin(monkeypatch: pytest.MonkeyPatch):
    permissions = set(rbac_service.BASELINE_ROLE_PERMISSIONS.get("admin", set()))
    permissions.update({"transcripts.read", "transcripts.write"})
    monkeypatch.setitem(rbac_service.BASELINE_ROLE_PERMISSIONS, "admin", permissions)
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student.no.transcripts@example.com": ["student"],
        },
    )


@pytest.fixture
def override_transcripts_db() -> Iterator[MagicMock]:
    session = MagicMock()
    app.dependency_overrides[get_transcripts_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_transcripts_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student.no.transcripts@example.com", ["student"])


def test_get_transcript_success(
    monkeypatch: pytest.MonkeyPatch,
    override_transcripts_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_student_transcript(self, tenant_id: int, *, student_profile_id: int):
        return StudentTranscriptSchema(
            student_profile_id=student_profile_id,
            total_credits=3,
            gpa=Decimal("4.00"),
            items=[
                TranscriptItemSchema(
                    enrollment_id=4001,
                    term_id=1,
                    term_code="2026-SPRING",
                    term_name="Spring 2026",
                    course_id=701,
                    course_code="CS101",
                    course_title="Intro to CS",
                    credits=3,
                    grade_code="A",
                    grade_points=Decimal("4.00"),
                )
            ],
        )

    monkeypatch.setattr(transcripts_service.TranscriptService, "get_student_transcript", fake_get_student_transcript)

    response = client.get("/api/admin/students/1001/transcript", headers=admin_headers)

    assert response.status_code == 200, response.text
    assert response.json()["student_profile_id"] == 1001


def test_get_transcript_tenant_isolation_404(
    monkeypatch: pytest.MonkeyPatch,
    override_transcripts_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_student_transcript(self, tenant_id: int, *, student_profile_id: int):
        raise TenantResourceNotFoundError("student not found for tenant")

    monkeypatch.setattr(transcripts_service.TranscriptService, "get_student_transcript", fake_get_student_transcript)

    response = client.get("/api/admin/students/1001/transcript", headers=admin_headers)

    assert response.status_code == 404, response.text


def test_snapshot_requires_permission(student_headers: dict[str, str]) -> None:
    response = client.post("/api/admin/students/1001/transcript/snapshot", headers=student_headers)
    assert response.status_code == 403, response.text


def test_create_snapshot_success(
    monkeypatch: pytest.MonkeyPatch,
    override_transcripts_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    now = datetime(2026, 3, 24, 11, 0, 0, tzinfo=UTC)

    async def fake_create_snapshot(self, tenant_id: int, *, student_profile_id: int, actor_id: str):
        return TranscriptSnapshotSchema(
            id=9301,
            tenant_id=tenant_id,
            student_profile_id=student_profile_id,
            snapshot_json={"student_profile_id": student_profile_id},
            generated_by=actor_id,
            generated_at=now,
        )

    monkeypatch.setattr(transcripts_service.TranscriptService, "create_transcript_snapshot", fake_create_snapshot)

    response = client.post("/api/admin/students/1001/transcript/snapshot", headers=admin_headers)

    assert response.status_code == 201, response.text
    assert response.json()["id"] == 9301


def test_get_transcript_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    override_transcripts_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_consistency_report(self, tenant_id: int, *, student_profile_id: int):
        return TranscriptConsistencyReportSchema(
            student_profile_id=student_profile_id,
            enrollment_count=2,
            transcript_record_count=2,
            issue_count=1,
            issues=[
                TranscriptConsistencyIssueSchema(
                    issue_type="transcript_record_mismatch",
                    enrollment_id=4002,
                    transcript_record_id=9202,
                    field="grade_code",
                    expected="B",
                    actual="C",
                )
            ],
        )

    monkeypatch.setattr(
        transcripts_service.TranscriptService,
        "get_student_transcript_consistency_report",
        fake_get_consistency_report,
    )

    response = client.get("/api/admin/students/1001/transcript/consistency", headers=admin_headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["student_profile_id"] == 1001
    assert payload["issue_count"] == 1
    assert payload["issues"][0]["issue_type"] == "transcript_record_mismatch"


def test_get_tenant_transcript_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    override_transcripts_db: MagicMock,
    admin_headers: dict[str, str],
) -> None:
    async def fake_get_tenant_consistency_report(self, tenant_id: int):
        assert tenant_id == 1
        return TranscriptTenantConsistencyReportSchema(
            scanned_student_count=2,
            students_with_issues=1,
            total_issue_count=2,
            reports=[
                TranscriptConsistencyReportSchema(
                    student_profile_id=1002,
                    enrollment_count=1,
                    transcript_record_count=1,
                    issue_count=2,
                    issues=[
                        TranscriptConsistencyIssueSchema(
                            issue_type="transcript_record_mismatch",
                            enrollment_id=4002,
                            transcript_record_id=9202,
                            field="grade_code",
                            expected="B",
                            actual="C",
                        ),
                        TranscriptConsistencyIssueSchema(
                            issue_type="transcript_record_mismatch",
                            enrollment_id=4002,
                            transcript_record_id=9202,
                            field="grade_points",
                            expected="3.00",
                            actual="2.00",
                        ),
                    ],
                )
            ],
        )

    monkeypatch.setattr(
        transcripts_service.TranscriptService,
        "list_tenant_transcript_consistency_reports",
        fake_get_tenant_consistency_report,
    )

    response = client.get("/api/admin/transcripts/consistency", headers=admin_headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["scanned_student_count"] == 2
    assert payload["students_with_issues"] == 1
    assert payload["total_issue_count"] == 2
    assert payload["reports"][0]["student_profile_id"] == 1002
