from app.modules.auth.token_service import create_access_token

from conftest import client


def _platform_headers() -> dict[str, str]:
    token = create_access_token(user_id="platform.owner@example.com", roles=["superadmin"], auth_source="test", tenant_id=1)
    return {"Authorization": f"Bearer {token}"}


def test_platform_lists_seeded_plans() -> None:
    response = client.get("/platform/plans", headers=_platform_headers())

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()["plans"]]
    assert "free" in codes
    assert "pro" in codes
    assert "enterprise" in codes


def test_platform_can_create_and_update_plan() -> None:
    create_response = client.post(
        "/platform/plans",
        headers=_platform_headers(),
        json={
            "code": "team",
            "name": "Team",
            "description": "Team plan",
            "active": True,
        },
    )
    assert create_response.status_code == 200
    plan_id = create_response.json()["plan"]["id"]

    update_response = client.put(
        f"/platform/plans/{plan_id}",
        headers=_platform_headers(),
        json={"name": "Team Plus", "active": False},
    )

    assert update_response.status_code == 200
    updated = update_response.json()["plan"]
    assert updated["name"] == "Team Plus"
    assert updated["active"] is False
