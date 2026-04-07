from conftest import ADMIN_HEADERS, client


def test_example_slice_endpoint_removed_from_runtime() -> None:
    response = client.get("/api/admin/example-slice/reference-items", headers=ADMIN_HEADERS)
    assert response.status_code == 404

