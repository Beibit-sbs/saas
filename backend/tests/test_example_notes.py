from tests.conftest import ADMIN_HEADERS, client


def test_example_notes_endpoint_removed_from_runtime() -> None:
    response = client.get("/api/admin/example-notes", headers=ADMIN_HEADERS)
    assert response.status_code == 404


def test_example_notes_mutation_endpoint_removed_from_runtime() -> None:
    response = client.post(
        "/api/admin/example-notes",
        headers=ADMIN_HEADERS,
        json={"title": "blocked", "summary": "blocked", "is_active": True},
    )
    assert response.status_code == 404
