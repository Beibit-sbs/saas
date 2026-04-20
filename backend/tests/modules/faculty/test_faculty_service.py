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


def test_faculty_workload_returns_credit_sum_for_term(monkeypatch) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "faculty":
            return [
                {
                    "id": 10,
                    "faculty_id": "FAC-01",
                    "department": "Engineering",
                    "max_credit_hours": 12,
                    "fte_ratio": 1.0,
                }
            ]
        if entity_name == "courses":
            return [
                {"id": 101, "credits": 3},
                {"id": 102, "credits": 4},
            ]
        return []

    def fake_workload_rows(tenant_id: int, term_id: int):
        assert tenant_id == 1
        assert term_id == 20261
        return [
            {"instructor_id": "FAC-01", "term_id": 20261, "course_id": 101, "role": "primary"},
            {"instructor_id": "FAC-01", "term_id": 20261, "course_id": 102, "role": "assistant"},
        ]

    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", fake_list_entities_for_tenant)
    monkeypatch.setattr(faculty_service, "_list_scheduling_workload_rows", fake_workload_rows)

    workload = faculty_service.get_faculty_workload(1, "FAC-01", 20261)

    assert workload["total_credit_hours"] == 3
    assert workload["primary_assignments"] == 1
    assert workload["assistant_assignments"] == 1
    assert workload["max_credit_hours"] == 12
    assert workload["alerts"] == ["underload_alert"]


def test_faculty_workload_overload_and_department_fairness(monkeypatch) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        if entity_name == "faculty":
            return [
                {"id": 10, "faculty_id": "FAC-01", "department": "Engineering", "max_credit_hours": 8, "fte_ratio": 1.0},
                {"id": 11, "faculty_id": "FAC-02", "department": "Engineering", "max_credit_hours": 8, "fte_ratio": 1.0},
            ]
        if entity_name == "courses":
            return [
                {"id": 101, "credits": 4},
                {"id": 102, "credits": 4},
                {"id": 103, "credits": 4},
            ]
        return []

    def fake_workload_rows(_tenant_id: int, _term_id: int):
        return [
            {"instructor_id": "FAC-01", "term_id": 20261, "course_id": 101, "role": "primary"},
            {"instructor_id": "FAC-01", "term_id": 20261, "course_id": 102, "role": "primary"},
            {"instructor_id": "FAC-01", "term_id": 20261, "course_id": 103, "role": "primary"},
            {"instructor_id": "FAC-02", "term_id": 20261, "course_id": 101, "role": "assistant"},
        ]

    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", fake_list_entities_for_tenant)
    monkeypatch.setattr(faculty_service, "_list_scheduling_workload_rows", fake_workload_rows)

    workload = faculty_service.get_faculty_workload(1, "FAC-01", 20261)
    assert workload["total_credit_hours"] == 12
    assert workload["alerts"] == ["overload_threshold"]

    summary = faculty_service.get_department_workload_summary(1, "Engineering", 20261)
    assert len(summary) == 2
    assert any("fairness_check" in item["alerts"] for item in summary)


def test_update_faculty_capacity_persists_fields(monkeypatch) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert entity_name == "faculty"
        assert tenant_id == 1
        return [
            {
                "id": 17,
                "faculty_id": "FAC-17",
                "first_name": "Lin",
                "last_name": "Chen",
                "department": "Science",
                "email": "lin@example.edu",
                "status": "active",
                "tenant_id": "1",
            }
        ]

    def fake_update_entity_for_tenant(entity_name: str, item_id: int, payload: dict[str, object], tenant_id: int):
        assert entity_name == "faculty"
        assert item_id == 17
        assert tenant_id == 1
        assert payload["max_credit_hours"] == 16
        assert payload["fte_ratio"] == 0.75
        return payload

    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", fake_list_entities_for_tenant)
    monkeypatch.setattr(faculty_service, "update_entity_for_tenant", fake_update_entity_for_tenant)

    updated = faculty_service.update_faculty_capacity(1, "FAC-17", 16, 0.75)

    assert updated["max_credit_hours"] == 16
    assert updated["fte_ratio"] == 0.75
