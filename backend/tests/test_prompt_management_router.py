"""Phase XII-XII3: Prompt Management router tests."""
from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/prompt-management"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="pm@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["prompt_management.read", "prompt_management.write"],
        )
    )
}

_TEMPLATE_ID: list[str] = []


def test_health_ok() -> None:
    response = client.get(f"{BASE}/health", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["module"] == "prompt_management"


def test_create_template() -> None:
    payload = {
        "name": "student-risk-summary",
        "description": "Summarise a student risk signal for the advisor",
        "template_text": "Student {{student_id}} has {{risk_level}} risk. Trend: {{trend}}.",
        "variables": ["student_id", "risk_level", "trend"],
        "category": "academic",
        "is_active": True,
    }
    response = client.post(f"{BASE}/templates", headers=HEADERS, json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "student-risk-summary"
    assert body["version"] == 1
    assert body["template_id"]
    _TEMPLATE_ID.append(body["template_id"])


def test_list_templates() -> None:
    response = client.get(f"{BASE}/templates", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_update_template() -> None:
    if not _TEMPLATE_ID:
        test_create_template()
    tid = _TEMPLATE_ID[0]
    response = client.patch(
        f"{BASE}/templates/{tid}",
        headers=HEADERS,
        json={"description": "Updated description"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["description"] == "Updated description"


def test_ab_route() -> None:
    # Create two templates first
    def _create(name: str) -> str:
        r = client.post(
            f"{BASE}/templates",
            headers=HEADERS,
            json={
                "name": name,
                "template_text": f"Template {name}",
                "variables": [],
                "category": "general",
            },
        )
        return r.json()["template_id"]

    id_a = _create("ab-variant-alpha")
    id_b = _create("ab-variant-beta")

    response = client.post(
        f"{BASE}/ab-test/route",
        headers=HEADERS,
        json={
            "template_id_a": id_a,
            "template_id_b": id_b,
            "traffic_split_pct": 50,
            "context_key": "user-42",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["variant"] in ("A", "B")
    assert body["selected_template_id"] in (id_a, id_b)
