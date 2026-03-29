from fastapi.routing import APIRoute

from tests.conftest import client
from app.main import app


def test_runtime_does_not_expose_example_routes() -> None:
    route_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    assert "/api/admin/example-notes" not in route_paths
    assert "/api/admin/example-slice/reference-items" not in route_paths


def test_mock_login_endpoint_removed_from_runtime() -> None:
    response = client.post(
        "/api/auth/mock-login",
        json={"login": "admin", "password": "admin123"},
    )
    assert response.status_code == 404


def test_demo_endpoints_removed_from_runtime() -> None:
    users_response = client.get("/api/auth/demo-users")
    assert users_response.status_code == 404

    login_response = client.post("/api/auth/demo-login", json={"user_id": "student.001"})
    assert login_response.status_code == 404
