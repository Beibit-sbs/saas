"""A-024.4 targeted tests for attendance + student_portal L3->L4 visibility."""

from __future__ import annotations

import importlib
import inspect

import pytest

import app.main as main_module
from app.modules.attendance import service as attendance_service
from app.modules.student_portal import service as student_portal_service
from tests.conftest import ADMIN_HEADERS, client


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.attendance.service",
        "app.modules.student_portal.service",
    ],
)
def test_a0244_modules_import_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0244_attendance_tenant_id_required_and_positive(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        attendance_service.build_attendance_visibility_summary(
            tenant_id=tenant_id,
            records=[],
            source_entity_type="attendance_records",
            source_entity_id="summary",
        )


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0244_student_portal_tenant_id_required_and_positive(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        student_portal_service.build_student_portal_visibility_summary(
            tenant_id=tenant_id,
            access_status="active",
            has_required_profile=True,
            has_active_enrollment=True,
            has_portal_role=True,
            has_contact_channel=True,
            source_entity_type="portal_requests",
            source_entity_id="summary",
        )


def test_a0244_attendance_empty_records_safe_summary_with_data_quality_note() -> None:
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=[],
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert summary["total_records"] == 0
    assert summary["data_quality_note"] is not None
    assert summary["review_required"] is True


def test_a0244_attendance_status_counts_are_deterministic() -> None:
    records = [
        {"id": "r1", "tenant_id": 1, "student_id": "s1", "session_id": "x1", "status": "PRESENT"},
        {"id": "r2", "tenant_id": 1, "student_id": "s1", "session_id": "x2", "status": "ABSENT"},
        {"id": "r3", "tenant_id": 1, "student_id": "s1", "session_id": "x3", "status": "LATE"},
        {"id": "r4", "tenant_id": 1, "student_id": "s1", "session_id": "x4", "status": "EXCUSED"},
        {"id": "r5", "tenant_id": 1, "student_id": "s1", "session_id": "x5", "status": "MISSING"},
    ]
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=records,
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert summary["present_count"] == 1
    assert summary["absent_count"] == 1
    assert summary["late_count"] == 1
    assert summary["excused_count"] == 1
    assert summary["unknown_count"] == 1


def test_a0244_attendance_high_absence_ratio_increases_risk_and_review() -> None:
    records = [
        {"id": "r1", "tenant_id": 1, "student_id": "s1", "session_id": "a", "status": "ABSENT"},
        {"id": "r2", "tenant_id": 1, "student_id": "s1", "session_id": "b", "status": "ABSENT"},
        {"id": "r3", "tenant_id": 1, "student_id": "s1", "session_id": "c", "status": "ABSENT"},
        {"id": "r4", "tenant_id": 1, "student_id": "s1", "session_id": "d", "status": "PRESENT"},
    ]
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=records,
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert summary["risk_level"] in {"high", "critical"}
    assert summary["review_required"] is True


def test_a0244_attendance_unknown_status_produces_data_quality_note() -> None:
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=[
            {"id": "r1", "tenant_id": 1, "student_id": "s1", "session_id": "x", "status": "UNKNOWNISH"}
        ],
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert summary["unknown_count"] == 1
    assert summary["data_quality_note"] is not None


def test_a0244_attendance_evidence_lineage_is_deterministic() -> None:
    records = [
        {"id": "r1", "tenant_id": 1, "student_id": "s1", "session_id": "x", "status": "PRESENT"}
    ]
    first = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=records,
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    second = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=records,
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert first == second


def test_a0244_attendance_no_fake_attendance_flag_exists() -> None:
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=[],
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert summary["no_fake_attendance_data"] is True


def test_a0244_attendance_no_level5_claim_exists() -> None:
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=[],
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    text = str(summary).lower()
    assert "level 5" not in text
    assert "level 6" not in text


def test_a0244_student_portal_ready_summary_when_requirements_complete() -> None:
    summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
        student_id="st-1",
        user_id="u-1",
    )
    assert summary["readiness_level"] == "ready"
    assert summary["review_required"] is False


def test_a0244_student_portal_missing_requirements_detected() -> None:
    summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="limited",
        has_required_profile=False,
        has_active_enrollment=False,
        has_portal_role=True,
        has_contact_channel=False,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    assert summary["readiness_level"] == "partially_ready"
    assert set(summary["missing_requirements"]) == {"required_profile", "active_enrollment", "contact_channel"}


def test_a0244_student_portal_unknown_access_status_requires_review() -> None:
    summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="weird_status",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    assert summary["access_status"] == "unknown"
    assert summary["review_required"] is True
    assert summary["data_quality_note"] is not None


def test_a0244_student_portal_readiness_is_deterministic() -> None:
    payload = dict(
        tenant_id=1,
        access_status="pending_setup",
        has_required_profile=True,
        has_active_enrollment=False,
        has_portal_role=False,
        has_contact_channel=False,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    assert student_portal_service.build_student_portal_visibility_summary(**payload) == (
        student_portal_service.build_student_portal_visibility_summary(**payload)
    )


def test_a0244_student_portal_evidence_lineage_is_deterministic() -> None:
    item_a = student_portal_service.build_student_portal_evidence_item(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
        student_id="st-1",
    )
    item_b = student_portal_service.build_student_portal_evidence_item(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
        student_id="st-1",
    )
    assert item_a == item_b


def test_a0244_student_portal_no_fake_student_data_flag_exists() -> None:
    summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    assert summary["no_fake_student_data"] is True


def test_a0244_student_portal_no_fake_portal_activity_flag_exists() -> None:
    summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    assert summary["no_fake_portal_activity"] is True


def test_a0244_student_portal_no_level5_claim_exists() -> None:
    summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    text = str(summary).lower()
    assert "level 5" not in text
    assert "level 6" not in text


def test_a0244_attendance_visible_surface_exists_if_l4_claimed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "list_attendance_records",
        lambda tenant_id, session_id=None, student_id=None: [
            {"id": "r1", "tenant_id": tenant_id, "student_id": "s1", "session_id": "x1", "status": "PRESENT"}
        ],
    )
    response = client.get("/api/admin/attendance/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["visible_surface"] == "/api/admin/attendance/summary"


def test_a0244_student_portal_visible_surface_exists_if_l4_claimed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "list_student_portal_requests",
        lambda tenant_id, student_id=None, request_type=None, status=None: [
            {"id": "p1", "student_id": "s1", "status": "SUBMITTED", "tenant_id": tenant_id}
        ],
    )
    response = client.get("/api/admin/student-portal/summary?student_id=s1", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["visible_surface"] == "/api/admin/student-portal/summary"


def test_a0244_attendance_summary_api_route_returns_deterministic_tenant_safe_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "list_attendance_records",
        lambda tenant_id, session_id=None, student_id=None: [
            {"id": "r1", "tenant_id": tenant_id, "student_id": "s1", "session_id": "x1", "status": "ABSENT"},
            {"id": "r2", "tenant_id": tenant_id, "student_id": "s1", "session_id": "x2", "status": "PRESENT"},
        ],
    )
    response = client.get("/api/admin/attendance/summary?student_id=s1", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tenant_id"] == 1
    assert payload["total_records"] == 2


def test_a0244_student_portal_summary_api_route_returns_deterministic_tenant_safe_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "list_student_portal_requests",
        lambda tenant_id, student_id=None, request_type=None, status=None: [
            {"id": "p1", "student_id": student_id or "s1", "status": "SUBMITTED", "tenant_id": tenant_id}
        ],
    )
    response = client.get("/api/admin/student-portal/summary?student_id=s1&user_id=u1", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tenant_id"] == 1
    assert payload["request_count"] == 1


def test_a0244_missing_tenant_context_fails_closed_with_mismatch_records(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "list_attendance_records",
        lambda tenant_id, session_id=None, student_id=None: [
            {"id": "r1", "tenant_id": 99, "student_id": "s1", "session_id": "x1", "status": "PRESENT"}
        ],
    )
    with pytest.raises(ValueError, match="attendance record tenant_id mismatch"):
        client.get("/api/admin/attendance/summary", headers=ADMIN_HEADERS)


def test_a0244_no_level5_or_level6_claims_cross_module() -> None:
    attendance_summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=[],
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    portal_summary = student_portal_service.build_student_portal_visibility_summary(
        tenant_id=1,
        access_status="active",
        has_required_profile=True,
        has_active_enrollment=True,
        has_portal_role=True,
        has_contact_channel=True,
        source_entity_type="portal_requests",
        source_entity_id="summary",
    )
    text = f"{attendance_summary} {portal_summary}".lower()
    assert "level 5" not in text
    assert "level 6" not in text


def test_a0244_no_fake_data_generation_in_sources() -> None:
    attendance_source = inspect.getsource(attendance_service).lower()
    portal_source = inspect.getsource(student_portal_service).lower()
    for forbidden in ["faker", "random.", "generate_fake", "synthetic_record"]:
        assert forbidden not in attendance_source
        assert forbidden not in portal_source


def test_a0244_no_module_count_expansion_constant_present() -> None:
    assert not hasattr(attendance_service, "MODULE_COUNT")
    assert not hasattr(student_portal_service, "MODULE_COUNT")


def test_a0244_no_unrelated_observability_mutation_from_new_contracts() -> None:
    summary = attendance_service.build_attendance_visibility_summary(
        tenant_id=1,
        records=[],
        source_entity_type="attendance_records",
        source_entity_id="summary",
    )
    assert "no_fake_attendance_analytics" in summary
