from __future__ import annotations

from unittest.mock import MagicMock

from app.modules.courses import service as courses_service


def test_get_course_consistency_report_detects_missing_programs(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "courses":
            return [
                {
                    "id": 7001,
                    "course_code": "CS101",
                    "title": "Intro to CS",
                    "credits": 3,
                    "program_id": 501,
                    "status": "active",
                    "tenant_id": "1",
                },
                {
                    "id": 7002,
                    "course_code": "CS999",
                    "title": "Ghost Course",
                    "credits": 3,
                    "program_id": 9999,
                    "status": "active",
                    "tenant_id": "1",
                },
            ]
        if entity_name == "programs":
            return [{"id": 501}]
        raise AssertionError(f"unexpected entity {entity_name}")

    monkeypatch.setattr(
        courses_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = courses_service.get_course_consistency_report(1)

    assert report["course_count"] == 2
    assert report["issue_count"] == 1
    assert report["issues"][0]["issue_type"] == "course_missing_program"
    assert report["issues"][0]["course_id"] == 7002
    assert report["issues"][0]["program_id"] == 9999


def test_get_course_consistency_report_detects_code_and_field_drift(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "courses":
            return [
                {
                    "id": 8001,
                    "course_code": "DUP101",
                    "title": "Dup A",
                    "credits": 3,
                    "program_id": 501,
                    "status": "active",
                    "tenant_id": "1",
                },
                {
                    "id": 8002,
                    "course_code": "DUP101",
                    "title": "Dup B",
                    "credits": 3,
                    "program_id": 501,
                    "status": "active",
                    "tenant_id": "1",
                },
                {
                    "id": 8003,
                    "course_code": None,
                    "title": "",
                    "credits": -1,
                    "program_id": 501,
                    "status": "BOGUS",
                    "tenant_id": "1",
                },
            ]
        if entity_name == "programs":
            return [{"id": 501}]
        raise AssertionError(f"unexpected entity {entity_name}")

    monkeypatch.setattr(
        courses_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = courses_service.get_course_consistency_report(1)
    assert report["course_count"] == 3

    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert issue_types.count("duplicate_course_code") == 2
    assert "course_missing_code" in issue_types
    assert "course_missing_title" in issue_types
    assert "course_invalid_credits" in issue_types
    assert "course_invalid_status" in issue_types
    assert "course_missing_program" not in issue_types


def test_create_course_calls_billing_write_guard(monkeypatch) -> None:
    billing_guard = MagicMock(name="assert_billing_write_allowed")
    create_entity = MagicMock(return_value={"id": 701, "course_code": "CS101"})

    monkeypatch.setattr(courses_service, "assert_billing_write_allowed", billing_guard)
    monkeypatch.setattr(courses_service, "create_entity_for_tenant", create_entity)

    created = courses_service.create_course(
        {"course_code": "CS101", "title": "Intro to CS"},
        tenant_id=1,
    )

    assert created["id"] == 701
    billing_guard.assert_called_once_with(1, action="courses.create")
    create_entity.assert_called_once_with(
        "courses",
        {"course_code": "CS101", "title": "Intro to CS"},
        1,
    )
