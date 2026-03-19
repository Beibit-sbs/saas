"""Cross-tenant isolation tests for University Core modules.

Verifies that each tenant only sees its own data and cannot
read, update, or delete another tenant's records.
"""
from tests.conftest import ADMIN_HEADERS, client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STUDENT_PAYLOAD = {
    "student_id": "ST-ISO-001",
    "first_name": "Test",
    "last_name": "User",
    "email": "test.user@example.edu",
    "status": "active",
}

_STUDENT_UPDATE_PAYLOAD = {
    "student_id": "ST-ISO-001",
    "first_name": "Test",
    "last_name": "Changed",
    "email": "test.user@example.edu",
    "status": "active",
}


def _create_extra_tenant() -> dict:
    """Create a second (non-default) tenant and return the response dict."""
    resp = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b", "name": "Tenant B", "status": "active"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tenant"]


def _tenant_headers(tenant_id: int) -> dict:
    return {**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_id)}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_default_tenant_stores_correct_tenant_id() -> None:
    """Creating a student without X-Tenant-ID stmps tenant_id='1'."""
    resp = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json=_STUDENT_PAYLOAD,
    )
    assert resp.status_code == 200, resp.text
    student = resp.json()["student"]
    assert student["tenant_id"] == "1"


def test_payload_tenant_id_is_ignored() -> None:
    """Supplying tenant_id in the request body has no effect; context wins."""
    payload = {**_STUDENT_PAYLOAD, "student_id": "ST-ISO-002", "tenant_id": "evil-override"}
    resp = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["student"]["tenant_id"] == "1"


def test_tenant_a_sees_only_own_rows() -> None:
    """Tenant B cannot see rows created by the default tenant."""
    # Create a student under the default tenant (id=1)
    resp = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json=_STUDENT_PAYLOAD,
    )
    assert resp.status_code == 200, resp.text

    # Create tenant B and fetch its students
    tenant_b = _create_extra_tenant()
    b_headers = _tenant_headers(int(tenant_b["id"]))

    list_resp = client.get("/api/admin/university/students", headers=b_headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["students"] == []


def test_default_tenant_sees_only_own_rows() -> None:
    """The default tenant cannot see rows created by tenant B."""
    tenant_b = _create_extra_tenant()
    b_headers = _tenant_headers(int(tenant_b["id"]))

    # Create a student under tenant B
    resp = client.post(
        "/api/admin/university/students",
        headers=b_headers,
        json=_STUDENT_PAYLOAD,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["student"]["tenant_id"] == str(tenant_b["id"])

    # Default tenant list is empty
    list_resp = client.get("/api/admin/university/students", headers=ADMIN_HEADERS)
    assert list_resp.status_code == 200
    assert list_resp.json()["students"] == []


def test_cross_tenant_update_returns_404() -> None:
    """Tenant B cannot update a record owned by the default tenant."""
    # Create under default tenant
    create_resp = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json=_STUDENT_PAYLOAD,
    )
    assert create_resp.status_code == 200
    student_id = create_resp.json()["student"]["id"]

    # Tenant B tries to update it
    tenant_b = _create_extra_tenant()
    b_headers = _tenant_headers(int(tenant_b["id"]))

    update_resp = client.put(
        f"/api/admin/university/students/{student_id}",
        headers=b_headers,
        json=_STUDENT_UPDATE_PAYLOAD,
    )
    assert update_resp.status_code == 404


def test_cross_tenant_delete_returns_404() -> None:
    """Tenant B cannot delete a record owned by the default tenant."""
    create_resp = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json=_STUDENT_PAYLOAD,
    )
    assert create_resp.status_code == 200
    student_id = create_resp.json()["student"]["id"]

    tenant_b = _create_extra_tenant()
    b_headers = _tenant_headers(int(tenant_b["id"]))

    delete_resp = client.delete(
        f"/api/admin/university/students/{student_id}",
        headers=b_headers,
    )
    assert delete_resp.status_code == 404

    # Original record still intact under default tenant
    list_resp = client.get("/api/admin/university/students", headers=ADMIN_HEADERS)
    ids = [s["id"] for s in list_resp.json()["students"]]
    assert student_id in ids


def test_both_tenants_independent_counters() -> None:
    """Each tenant maintains independent data sets."""
    tenant_b = _create_extra_tenant()
    b_headers = _tenant_headers(int(tenant_b["id"]))

    # Create 2 students under default tenant
    for i in range(2):
        r = client.post(
            "/api/admin/university/students",
            headers=ADMIN_HEADERS,
            json={**_STUDENT_PAYLOAD, "student_id": f"ST-DEFAULT-{i}"},
        )
        assert r.status_code == 200

    # Create 1 student under tenant B
    r = client.post(
        "/api/admin/university/students",
        headers=b_headers,
        json={**_STUDENT_PAYLOAD, "student_id": "ST-B-001"},
    )
    assert r.status_code == 200

    default_list = client.get("/api/admin/university/students", headers=ADMIN_HEADERS)
    b_list = client.get("/api/admin/university/students", headers=b_headers)

    assert len(default_list.json()["students"]) == 2
    assert len(b_list.json()["students"]) == 1
    assert b_list.json()["students"][0]["student_id"] == "ST-B-001"


def test_tenant_own_update_succeeds() -> None:
    """A tenant can update its own records."""
    create_resp = client.post(
        "/api/admin/university/students",
        headers=ADMIN_HEADERS,
        json=_STUDENT_PAYLOAD,
    )
    assert create_resp.status_code == 200
    student_id = create_resp.json()["student"]["id"]

    update_resp = client.put(
        f"/api/admin/university/students/{student_id}",
        headers=ADMIN_HEADERS,
        json=_STUDENT_UPDATE_PAYLOAD,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["student"]["last_name"] == "Changed"
    assert update_resp.json()["student"]["tenant_id"] == "1"


def test_inactive_tenant_is_rejected() -> None:
    """A request with X-Tenant-ID pointing to an inactive tenant gets 403."""
    tenant_b = _create_extra_tenant()

    # Deactivate tenant B
    deactivate_resp = client.delete(
        f"/api/admin/tenants/{tenant_b['id']}",
        headers=ADMIN_HEADERS,
    )
    assert deactivate_resp.status_code == 200

    b_headers = _tenant_headers(int(tenant_b["id"]))
    resp = client.get("/api/admin/university/students", headers=b_headers)
    assert resp.status_code == 403


def test_nonexistent_tenant_is_rejected() -> None:
    """A request with X-Tenant-ID pointing to a non-existent tenant gets 404."""
    headers = _tenant_headers(99999)
    resp = client.get("/api/admin/university/students", headers=headers)
    assert resp.status_code == 404
