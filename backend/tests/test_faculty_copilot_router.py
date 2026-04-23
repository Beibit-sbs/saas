"""Phase XII-XII1: Faculty Copilot router tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/admin/faculty-copilot"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="faculty.copilot@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["faculty_copilot.read", "faculty_copilot.write"],
        )
    )
}


def test_health_ok() -> None:
    response = client.get(f"{BASE}/health", headers=HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["module"] == "faculty_copilot"


def test_generate_lesson_plan() -> None:
    payload = {
        "faculty_id": "FAC-001",
        "course_title": "Data Structures",
        "topic": "Balanced Trees",
        "duration_minutes": 90,
        "learning_objectives": ["Explain AVL rotations", "Compare balancing strategies"],
    }
    response = client.post(f"{BASE}/lesson-plan", headers=HEADERS, json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "summary" in body
    assert body["question"]


def test_generate_materials() -> None:
    payload = {
        "faculty_id": "FAC-001",
        "course_title": "Databases",
        "topic": "Query Optimization",
        "material_type": "slides",
    }
    response = client.post(f"{BASE}/materials", headers=HEADERS, json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "summary" in body
    assert body["question"]


def test_qna() -> None:
    payload = {
        "faculty_id": "FAC-001",
        "course_title": "Operating Systems",
        "question": "How should I explain deadlock prevention in one lecture?",
    }
    response = client.post(f"{BASE}/qna", headers=HEADERS, json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "summary" in body
    assert body["question"] == payload["question"]
