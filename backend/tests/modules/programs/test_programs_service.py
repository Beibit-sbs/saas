from __future__ import annotations

from app.modules.programs import service as programs_service


def test_get_program_consistency_report_detects_missing_and_duplicate_codes(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        assert entity_name == "programs"
        return [
            {
                "id": 501,
                "program_code": "CS-BSC",
                "title": "Computer Science",
                "degree_type": "bachelor",
                "faculty": "Engineering",
                "status": "active",
                "tenant_id": "1",
            },
            {
                "id": 502,
                "program_code": "CS-BSC",
                "title": "Computer Science 2",
                "degree_type": "bachelor",
                "faculty": "Engineering",
                "status": "active",
                "tenant_id": "1",
            },
            {
                "id": 503,
                "program_code": "",
                "title": "No Code Program",
                "degree_type": "master",
                "faculty": "Science",
                "status": "active",
                "tenant_id": "1",
            },
        ]

    monkeypatch.setattr(
        programs_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = programs_service.get_program_consistency_report(1)

    assert report["program_count"] == 3
    assert report["issue_count"] == 3
    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert issue_types.count("duplicate_program_code") == 2
    assert "program_missing_code" in issue_types


def test_get_program_consistency_report_detects_field_and_type_drift(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        assert entity_name == "programs"
        return [
            {
                "id": 601,
                "program_code": "DRIFT01",
                "title": "",
                "degree_type": "unknown_type",
                "faculty": "Science",
                "status": "suspended",
                "tenant_id": "1",
            },
            {
                "id": 602,
                "program_code": "CLEAN01",
                "title": "Clean Program",
                "degree_type": "master",
                "faculty": "Engineering",
                "status": "active",
                "tenant_id": "1",
            },
        ]

    monkeypatch.setattr(
        programs_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = programs_service.get_program_consistency_report(1)
    assert report["program_count"] == 2

    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert "program_missing_name" in issue_types
    assert "program_invalid_degree_type" in issue_types
    assert "program_invalid_status" in issue_types
    assert report["issue_count"] == 3
