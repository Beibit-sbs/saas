from app.modules.audit.service import list_admin_actions

from conftest import ADMIN_HEADERS, client


def test_example_slice_reference_items_are_available() -> None:
    response = client.get("/api/admin/example-slice/reference-items", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    items = payload.get("items")
    assert isinstance(items, list)
    assert len(items) >= 1
    assert any(item.get("key") == "example_rbac_guarded_read" for item in items)


def test_example_slice_access_is_audited() -> None:
    response = client.get("/api/admin/example-slice/reference-items", headers=ADMIN_HEADERS)
    assert response.status_code == 200

    events = list_admin_actions(action="example_slice.read", entity="example_slice", limit=20, tenant_id=1)
    assert any(event.get("path") == "/api/admin/example-slice/reference-items" for event in events)
