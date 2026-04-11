from __future__ import annotations

from app.modules.faculty import service as faculty_service


def test_get_faculty_consistency_report_detects_missing_and_duplicate_fields(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        assert entity_name == "faculty"
        return [
            {
                "id": 1001,
                "faculty_id": "FAC-01",
                "first_name": "Ann",
                "last_name": "Stone",
                "department": "Engineering",
                "email": "ann@example.edu",
                "status": "active",
                "tenant_id": "1",
            },
            {
                "id": 1002,
                "faculty_id": "FAC-01",
                "first_name": "Bob",
                "last_name": "Miller",
                "department": "Engineering",
                "email": "",
                "status": "active",
                "tenant_id": "1",
            },
            {
                "id": 1003,
                "faculty_id": "",
                "first_name": "Cara",
                "last_name": "Reed",
                "department": "Science",
                "email": "cara@example.edu",
                "status": "active",
                "tenant_id": "1",
            },
        ]

    monkeypatch.setattr(
        faculty_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = faculty_service.get_faculty_consistency_report(1)

    assert report["faculty_count"] == 3
    assert report["issue_count"] == 4
    issue_types = [issue["issue_type"] for issue in report["issues"]]
    assert issue_types.count("duplicate_faculty_identifier") == 2
    assert "faculty_missing_email" in issue_types
    assert "faculty_missing_identifier" in issue_types


def test_get_faculty_consistency_report_detects_email_and_status_drift(
    monkeypatch,
) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        assert entity_name == "faculty"
        return [
            {
                "id": 2001,
                "faculty_id": "FAC-11",
                "email": "dup@example.edu",
                "status": "active",
                "tenant_id": "1",
            },
            {
                "id": 2002,
                "faculty_id": "FAC-12",
                "email": "DUP@example.edu",
                "status": "active",
                "tenant_id": "1",
            },
            {
                "id": 2003,
                "faculty_id": "FAC-13",
                "email": "bad-email-format",
                "status": "paused",
                "tenant_id": "1",
            },
        ]

    monkeypatch.setattr(
        faculty_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    report = faculty_service.get_faculty_consistency_report(1)
    issue_types = [issue["issue_type"] for issue in report["issues"]]

    assert issue_types.count("duplicate_faculty_email") == 2
    assert "faculty_invalid_email_format" in issue_types
    assert "faculty_invalid_status" in issue_types
