from tests.conftest import ADMIN_HEADERS, client


def test_students_crud() -> None:
    list_response = client.get("/api/admin/university/students", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    assert list_response.json()["students"] == []

    create_response = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json={
            "student_id": "ST-1001",
            "first_name": "Ainur",
            "last_name": "Sarsen",
            "email": "ainur.sarsen@example.edu",
            "status": "active",
            "tenant_id": None,
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()["student"]
    assert created["student_id"] == "ST-1001"
    assert created["status"] == "active"

    update_response = client.put(
        f"/api/admin/university/students/{created['id']}",
        headers=ADMIN_HEADERS,
        json={
            "student_id": "ST-1001",
            "first_name": "Ainur",
            "last_name": "Sarsenova",
            "email": "ainur.sarsen@example.edu",
            "status": "on_leave",
            "tenant_id": "tenant-alpha",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()["student"]
    assert updated["last_name"] == "Sarsenova"
    assert updated["status"] == "on_leave"
    assert updated["tenant_id"] == "1"

    delete_response = client.delete(f"/api/admin/university/students/{created['id']}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_courses_crud() -> None:
    program_response = client.post(
        "/api/admin/university/programs",
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
        "/api/admin/university/courses",
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
        f"/api/admin/university/courses/{created['id']}",
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

    delete_response = client.delete(f"/api/admin/university/courses/{created['id']}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_enrollment_creation() -> None:
    student_response = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json={
            "student_id": "ST-2001",
            "first_name": "Dana",
            "last_name": "Imanova",
            "email": "dana.imanova@example.edu",
            "status": "active",
            "tenant_id": None,
        },
    )
    assert student_response.status_code == 200
    student_id = student_response.json()["student"]["id"]

    program_response = client.post(
        "/api/admin/university/programs",
        headers=ADMIN_HEADERS,
        json={
            "program_code": "MATH-BSC",
            "title": "Mathematics",
            "degree_type": "bachelor",
            "faculty": "Science",
            "status": "active",
            "tenant_id": None,
        },
    )
    assert program_response.status_code == 200
    program_id = program_response.json()["program"]["id"]

    course_response = client.post(
        "/api/admin/university/courses",
        headers=ADMIN_HEADERS,
        json={
            "course_code": "MATH101",
            "title": "Calculus I",
            "credits": 5,
            "program_id": program_id,
            "status": "active",
            "tenant_id": None,
        },
    )
    assert course_response.status_code == 200
    course_id = course_response.json()["course"]["id"]

    enrollment_response = client.post(
        "/api/admin/university/enrollments",
        headers=ADMIN_HEADERS,
        json={
            "student_id": student_id,
            "course_id": course_id,
            "semester": "2026-spring",
            "status": "enrolled",
            "tenant_id": None,
        },
    )
    assert enrollment_response.status_code == 200
    assert enrollment_response.headers["Deprecation"] == "true"
    assert enrollment_response.headers["Sunset"] == "Fri, 31 Jul 2026 00:00:00 GMT"
    assert enrollment_response.headers["Link"] == '</api/admin/enrollments>; rel="successor-version"'
    assert enrollment_response.headers["Warning"] == '299 - "Deprecated API: use /api/admin/enrollments"'
    enrollment = enrollment_response.json()["enrollment"]
    assert enrollment["student_id"] == student_id
    assert enrollment["course_id"] == course_id
    assert enrollment["status"] == "enrolled"


def test_record_assignment() -> None:
    student_response = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json={
            "student_id": "ST-3001",
            "first_name": "Alina",
            "last_name": "Bek",
            "email": "alina.bek@example.edu",
            "status": "active",
            "tenant_id": None,
        },
    )
    assert student_response.status_code == 200
    student_id = student_response.json()["student"]["id"]

    program_response = client.post(
        "/api/admin/university/programs",
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
        "/api/admin/university/courses",
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
