from app.modules.students.service import create_student
from app.modules.university_core import tenant_entity_service

from tests.conftest import ADMIN_HEADERS, client


def test_courses_crud() -> None:
    program_response = client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "CS-BSC",
            "title": "Computer Science",
            "degree_type": "bachelor",
            "faculty": "Engineering",
            "status": "active",
            "tenant_id": None,
        },
    )
    assert program_response.status_code == 200
    program_id = program_response.json()["program"]["id"]

    create_response = client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "CS101",
            "title": "Intro to Programming",
            "credits": 5,
            "program_id": program_id,
            "status": "active",
            "tenant_id": None,
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()["course"]
    assert created["course_code"] == "CS101"
    assert created["credits"] == 5

    update_response = client.put(
        f"/api/admin/org/courses/{created['id']}",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "CS101",
            "title": "Intro to Programming I",
            "credits": 6,
            "program_id": program_id,
            "status": "active",
            "tenant_id": "tenant-alpha",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()["course"]
    assert updated["title"] == "Intro to Programming I"
    assert updated["credits"] == 6

    delete_response = client.delete(f"/api/admin/org/courses/{created['id']}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_faculty_org_namespace_list() -> None:
    list_response = client.get("/api/admin/org/faculty", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    assert list_response.json()["faculty"] == []


def test_record_assignment() -> None:
    student = create_student(
        {
            "student_id": "ST-3001",
            "first_name": "Alina",
            "last_name": "Bek",
            "email": "alina.bek@example.edu",
            "status": "active",
            "tenant_id": None,
        },
        1,
    )
    student_id = student["id"]

    program_response = client.post(
        "/api/admin/org/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "PHYS-BSC",
            "title": "Physics",
            "degree_type": "bachelor",
            "faculty": "Science",
            "status": "active",
            "tenant_id": None,
        },
    )
    assert program_response.status_code == 200
    program_id = program_response.json()["program"]["id"]

    course_response = client.post(
        "/api/admin/org/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "PHYS101",
            "title": "Mechanics",
            "credits": 4,
            "program_id": program_id,
            "status": "active",
            "tenant_id": None,
        },
    )
    assert course_response.status_code == 200
    course_id = course_response.json()["course"]["id"]

    tenant_entity_service.create_entity_for_tenant(
        "enrollments",
        {
            "student_id": student_id,
            "course_id": course_id,
            "semester": "2026-spring",
            "status": "enrolled",
            "tenant_id": None,
        },
        1,
    )

    record_response = client.post(
        "/api/admin/university/records",
        headers=ADMIN_HEADERS,
        json={
            "student_id": student_id,
            "course_id": course_id,
            "grade": "A-",
            "semester": "2026-spring",
            "status": "published",
            "tenant_id": None,
        },
    )
    assert record_response.status_code == 200
    record = record_response.json()["record"]
    assert record["student_id"] == student_id
    assert record["course_id"] == course_id
    assert record["grade"] == "A-"


def test_university_core_consistency_endpoint_detects_cross_entity_drift(monkeypatch) -> None:
    def fake_list_entities_for_tenant(entity_name: str, tenant_id: int):
        assert tenant_id == 1
        fixtures = {
            "students": [{"id": 1001, "tenant_id": "1"}],
            "programs": [{"id": 501, "tenant_id": "1"}],
            "courses": [
                {"id": 701, "program_id": 501, "tenant_id": "1"},
                {"id": 702, "program_id": 9999, "tenant_id": "1"},
            ],
            "enrollments": [
                {"id": 801, "student_id": 1001, "course_id": 701, "tenant_id": "1"},
                {"id": 802, "student_id": 9999, "course_id": 702, "tenant_id": ""},
            ],
            "academic_records": [
                {"id": 901, "student_id": 1001, "course_id": 9998, "tenant_id": "1"},
            ],
        }
        return fixtures[entity_name]

    monkeypatch.setattr(
        tenant_entity_service,
        "list_entities_for_tenant",
        fake_list_entities_for_tenant,
    )

    response = client.get("/api/admin/university/consistency", headers=ADMIN_HEADERS)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["entity_counts"]["courses"] == 2
    issue_types = [issue["issue_type"] for issue in body["issues"]]
    assert "course_missing_program" in issue_types
    assert "enrollment_missing_student" in issue_types
    assert "missing_tenant_marker" in issue_types
    assert "academic_record_missing_course" in issue_types
