from __future__ import annotations

from app.modules.academic_records import service as academic_records_service


def test_get_record_consistency_report_detects_missing_references(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "academic_records":
            return [
                {
                    "id": 9001,
                    "student_id": 1001,
                    "course_id": 701,
                    "grade": "A",
                    "semester": "2026-spring",
                    "status": "published",
                    "tenant_id": "1",
                },
                {
                    "id": 9002,
                    "student_id": 9999,
                    "course_id": 702,
                    "grade": "B",
                    "semester": "2026-spring",
                    "status": "published",
                    "tenant_id": "1",
                },
                {
                    "id": 9003,
                    "student_id": 9998,
                    "course_id": 799,
                    "grade": "C",
                    "semester": "2026-fall",
                    "status": "draft",
                    "tenant_id": "1",
                },
            ]
        if entity_name == "students":
            return [{"id": 1001}]
        if entity_name == "courses":
            return [{"id": 701}, {"id": 702}]
        raise AssertionError(f"unexpected entity {entity_name}")

    monkeypatch.setattr(
        academic_records_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = academic_records_service.get_record_consistency_report(1)

    assert report["record_count"] == 3
    assert report["issue_count"] == 2
    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert "record_missing_student" in issue_types
    assert "record_orphaned_references" in issue_types


def test_get_record_consistency_report_detects_grade_and_field_drift(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "academic_records":
            return [
                {
                    "id": 10001,
                    "student_id": 2001,
                    "course_id": 801,
                    "grade": "Z",
                    "semester": "2026-spring",
                    "status": "archived",
                    "tenant_id": "1",
                },
                {
                    "id": 10002,
                    "student_id": 2002,
                    "course_id": 802,
                    "grade": "A",
                    "semester": "invalid",
                    "status": "bogus_status",
                    "tenant_id": "1",
                },
                {
                    "id": 10003,
                    "student_id": 2003,
                    "course_id": 803,
                    "grade": None,
                    "semester": None,
                    "status": None,
                    "tenant_id": "1",
                },
            ]
        if entity_name == "students":
            return [{"id": 2001}, {"id": 2002}, {"id": 2003}]
        if entity_name == "courses":
            return [{"id": 801}, {"id": 802}, {"id": 803}]
        raise AssertionError(f"unexpected entity {entity_name}")

    monkeypatch.setattr(
        academic_records_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = academic_records_service.get_record_consistency_report(1)
    assert report["record_count"] == 3

    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert "record_invalid_grade" in issue_types
    assert "record_invalid_semester_format" in issue_types
    assert "record_invalid_status" in issue_types
    assert "record_missing_status" in issue_types
    assert "record_missing_semester" in issue_types


def test_get_record_consistency_report_detects_duplicate_enrollments(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "academic_records":
            return [
                {
                    "id": 11001,
                    "student_id": 3001,
                    "course_id": 901,
                    "grade": "A",
                    "semester": "2026-spring",
                    "status": "published",
                    "tenant_id": "1",
                },
                {
                    "id": 11002,
                    "student_id": 3001,
                    "course_id": 901,
                    "grade": "B",
                    "semester": "2026-spring",
                    "status": "draft",
                    "tenant_id": "1",
                },
                {
                    "id": 11003,
                    "student_id": 3002,
                    "course_id": 902,
                    "grade": "A",
                    "semester": "2026-fall",
                    "status": "published",
                    "tenant_id": "1",
                },
            ]
        if entity_name == "students":
            return [{"id": 3001}, {"id": 3002}]
        if entity_name == "courses":
            return [{"id": 901}, {"id": 902}]
        raise AssertionError(f"unexpected entity {entity_name}")

    monkeypatch.setattr(
        academic_records_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = academic_records_service.get_record_consistency_report(1)
    assert report["record_count"] == 3

    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert issue_types.count("record_duplicate_enrollment") == 2
