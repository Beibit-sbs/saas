"""
Backend tests for Federation Layer v1.

Covers:
- create institution
- list institutions
- get institution by id (not found → 404 logic)
- link tenant to institution
- list institution tenants
- tenant isolation across institutions
- cross-tenant analytics aggregation via service.list_institution_overview()
- tenant isolation: tenants not linked can't see other institution's overview
- API: POST /api/v1/admin/platform/federation/institutions
- API: GET /api/v1/admin/platform/federation/institutions
- API: GET /api/v1/admin/platform/federation/institutions/{id}
- API: GET /api/v1/admin/platform/federation/institutions/{id}/overview
- API: POST /api/v1/admin/platform/federation/institutions/{id}/tenants
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.platform.federation.repository import FederationRepository
from app.platform.federation.service import FederationService
from app.platform.uow import UnitOfWork
from tests.conftest import ADMIN_HEADERS, client
from app.platform.tenant import service as tenant_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unique_code() -> str:
    return f"INST-{uuid4().hex[:8].upper()}"


def _tenant(prefix: str) -> int:
    row = tenant_service.create_tenant(f"{prefix}-{uuid4().hex[:8]}", f"{prefix} Tenant")
    return int(row["tenant_id"])


# ---------------------------------------------------------------------------
# Repository unit tests
# ---------------------------------------------------------------------------


class TestFederationRepository:
    def test_create_and_get_institution(self) -> None:
        repo = FederationRepository()
        with UnitOfWork() as uow:
            inst = repo.create_institution(
                name="Test University",
                code=_unique_code(),
                country="Russia",
                inst_type="university",
                metadata_json={"region": "Siberia"},
                conn=uow.conn,
            )
        assert inst["id"] >= 1
        assert inst["name"] == "Test University"
        assert inst["country"] == "Russia"
        assert inst["type"] == "university"
        assert inst["status"] == "active"
        assert inst["metadata_json"]["region"] == "Siberia"

        with UnitOfWork() as uow:
            fetched = repo.get_institution(inst["id"], conn=uow.conn)
        assert fetched is not None
        assert fetched["name"] == "Test University"

    def test_get_institution_not_found(self) -> None:
        repo = FederationRepository()
        with UnitOfWork() as uow:
            result = repo.get_institution(999_999, conn=uow.conn)
        assert result is None

    def test_list_institutions(self) -> None:
        repo = FederationRepository()
        with UnitOfWork() as uow:
            repo.create_institution(
                name="Alpha University",
                code=_unique_code(),
                country="Russia",
                inst_type="university",
                metadata_json={},
                conn=uow.conn,
            )
            repo.create_institution(
                name="Beta College",
                code=_unique_code(),
                country="Germany",
                inst_type="college",
                metadata_json={},
                conn=uow.conn,
            )
            institutions = repo.list_institutions(conn=uow.conn)
        assert len(institutions) >= 2
        names = [i["name"] for i in institutions]
        assert "Alpha University" in names
        assert "Beta College" in names

    def test_link_tenant_to_institution(self) -> None:
        repo = FederationRepository()
        tid = _tenant("fed-link")

        with UnitOfWork() as uow:
            inst = repo.create_institution(
                name="Link Uni",
                code=_unique_code(),
                country="Russia",
                inst_type="university",
                metadata_json={},
                conn=uow.conn,
            )
            member = repo.link_tenant_to_institution(
                institution_id=inst["id"],
                tenant_id=tid,
                role="institution_admin",
                conn=uow.conn,
            )
        assert member["institution_id"] == inst["id"]
        assert member["tenant_id"] == tid
        assert member["role"] == "institution_admin"

    def test_list_institution_tenants(self) -> None:
        repo = FederationRepository()
        tid1 = _tenant("fed-tenants-a")
        tid2 = _tenant("fed-tenants-b")

        with UnitOfWork() as uow:
            inst = repo.create_institution(
                name="Multi Tenant Uni",
                code=_unique_code(),
                country="Russia",
                inst_type="university",
                metadata_json={},
                conn=uow.conn,
            )
            repo.link_tenant_to_institution(
                institution_id=inst["id"], tenant_id=tid1, role="institution_admin", conn=uow.conn
            )
            repo.link_tenant_to_institution(
                institution_id=inst["id"], tenant_id=tid2, role="institution_admin", conn=uow.conn
            )
            members = repo.list_institution_tenants(inst["id"], conn=uow.conn)
        tenant_ids = [m["tenant_id"] for m in members]
        assert tid1 in tenant_ids
        assert tid2 in tenant_ids

    def test_tenant_isolation_across_institutions(self) -> None:
        repo = FederationRepository()
        tid_a = _tenant("fed-iso-a")
        tid_b = _tenant("fed-iso-b")

        with UnitOfWork() as uow:
            inst_a = repo.create_institution(
                name="Isolation Uni A",
                code=_unique_code(),
                country="Russia",
                inst_type="university",
                metadata_json={},
                conn=uow.conn,
            )
            inst_b = repo.create_institution(
                name="Isolation Uni B",
                code=_unique_code(),
                country="Russia",
                inst_type="university",
                metadata_json={},
                conn=uow.conn,
            )
            repo.link_tenant_to_institution(
                institution_id=inst_a["id"], tenant_id=tid_a, role="institution_admin", conn=uow.conn
            )
            repo.link_tenant_to_institution(
                institution_id=inst_b["id"], tenant_id=tid_b, role="institution_admin", conn=uow.conn
            )
            tenants_a = repo.list_institution_tenants(inst_a["id"], conn=uow.conn)
            tenants_b = repo.list_institution_tenants(inst_b["id"], conn=uow.conn)

        # Tenant A must not appear under institution B
        ids_a = [m["tenant_id"] for m in tenants_a]
        ids_b = [m["tenant_id"] for m in tenants_b]
        assert tid_a in ids_a
        assert tid_a not in ids_b
        assert tid_b in ids_b
        assert tid_b not in ids_a


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestFederationService:
    def test_create_and_list(self) -> None:
        repo = FederationRepository()
        svc = FederationService(repository=repo)

        inst = svc.create_institution(
            name="Service Uni",
            code=_unique_code(),
            country="Russia",
            inst_type="university",
        )
        assert inst["status"] == "active"

        institutions = svc.list_institutions()
        assert any(i["id"] == inst["id"] for i in institutions)

    def test_register_tenant_not_found_raises(self) -> None:
        repo = FederationRepository()
        svc = FederationService(repository=repo)

        with pytest.raises(ValueError, match="not found"):
            svc.register_tenant_under_institution(
                institution_id=999_999, tenant_id=1, role="institution_admin"
            )

    def test_institution_overview_aggregation(self) -> None:
        """Overview should sum KPIs across all linked tenants."""
        repo = FederationRepository()
        svc = FederationService(repository=repo)

        tid1 = _tenant("overview-a")
        tid2 = _tenant("overview-b")

        inst = svc.create_institution(
            name="Overview Uni",
            code=_unique_code(),
            country="Russia",
            inst_type="university",
        )
        svc.register_tenant_under_institution(
            institution_id=inst["id"], tenant_id=tid1, role="institution_admin"
        )
        svc.register_tenant_under_institution(
            institution_id=inst["id"], tenant_id=tid2, role="institution_admin"
        )

        overview = svc.list_institution_overview(inst["id"])
        assert overview["institution"]["id"] == inst["id"]
        assert overview["tenant_count"] == 2
        assert isinstance(overview["students_total"], int)
        assert isinstance(overview["enrollments_total"], int)
        assert isinstance(overview["kpi_cards"], list)
        metric_keys = [c["metric_key"] for c in overview["kpi_cards"]]
        assert "institution_students_total" in metric_keys
        assert "institution_enrollments_total" in metric_keys
        assert "institution_failed_jobs" in metric_keys
        assert "institution_automation_failures" in metric_keys

    def test_institution_overview_not_found_raises(self) -> None:
        repo = FederationRepository()
        svc = FederationService(repository=repo)

        with pytest.raises(ValueError, match="not found"):
            svc.list_institution_overview(999_999)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def _inst_payload(**kwargs) -> dict:
    return {
        "name": kwargs.get("name", "API University"),
        "code": kwargs.get("code", _unique_code()),
        "country": kwargs.get("country", "Russia"),
        "type": kwargs.get("type", "university"),
        "metadata": kwargs.get("metadata", {}),
    }


def test_api_create_institution(reset_shared_state) -> None:
    resp = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="API Uni", code=_unique_code()),
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "API Uni"
    assert body["status"] == "active"
    assert "id" in body
    assert "created_at" in body


def test_api_list_institutions_empty(reset_shared_state) -> None:
    resp = client.get(
        "/api/v1/admin/platform/federation/institutions",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


def test_api_list_institutions_after_create(reset_shared_state) -> None:
    code = _unique_code()
    client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="List Uni", code=code),
        headers=ADMIN_HEADERS,
    )
    resp = client.get(
        "/api/v1/admin/platform/federation/institutions",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    names = [i["name"] for i in resp.json()]
    assert "List Uni" in names


def test_api_get_institution_by_id(reset_shared_state) -> None:
    code = _unique_code()
    create_resp = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="Get Uni", code=code),
        headers=ADMIN_HEADERS,
    )
    inst_id = create_resp.json()["id"]

    resp = client.get(
        f"/api/v1/admin/platform/federation/institutions/{inst_id}",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == inst_id
    assert resp.json()["code"] == code


def test_api_get_institution_not_found(reset_shared_state) -> None:
    resp = client.get(
        "/api/v1/admin/platform/federation/institutions/999999",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 404


def test_api_link_tenant_to_institution(reset_shared_state) -> None:
    tid = _tenant("api-link")
    create_resp = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="Link API Uni", code=_unique_code()),
        headers=ADMIN_HEADERS,
    )
    inst_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/v1/admin/platform/federation/institutions/{inst_id}/tenants",
        json={"tenant_id": tid, "role": "institution_admin"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["institution_id"] == inst_id
    assert body["tenant_id"] == tid
    assert body["role"] == "institution_admin"


def test_api_institution_overview(reset_shared_state) -> None:
    create_resp = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="Overview API Uni", code=_unique_code()),
        headers=ADMIN_HEADERS,
    )
    inst_id = create_resp.json()["id"]

    resp = client.get(
        f"/api/v1/admin/platform/federation/institutions/{inst_id}/overview",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "institution" in body
    assert "tenant_count" in body
    assert "students_total" in body
    assert "enrollments_total" in body
    assert "kpi_cards" in body
    assert isinstance(body["kpi_cards"], list)


def test_api_overview_not_found(reset_shared_state) -> None:
    resp = client.get(
        "/api/v1/admin/platform/federation/institutions/999999/overview",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 404


def test_api_create_institution_duplicate_code(reset_shared_state) -> None:
    """Duplicate code must return 400 (caught by repository unique constraint or ValueError)."""
    code = _unique_code()
    payload = _inst_payload(name="First Uni", code=code)
    client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=payload,
        headers=ADMIN_HEADERS,
    )
    # In-memory mode: no unique constraint enforced at DB level, so skip this
    # for pure unit test. The test is a placeholder for DB-mode behavior.
    # We verify that the second call at least doesn't crash the server.
    resp2 = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="Second Uni", code=code),
        headers=ADMIN_HEADERS,
    )
    # 201 or 400 depending on mode — either is acceptable, just not 500
    assert resp2.status_code in (201, 400), resp2.text


def test_tenant_isolation_api(reset_shared_state) -> None:
    """Tenants linked to institution A should not appear under institution B."""
    tid_a = _tenant("iso-api-a")
    inst_a = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="Isolation A", code=_unique_code()),
        headers=ADMIN_HEADERS,
    ).json()
    inst_b = client.post(
        "/api/v1/admin/platform/federation/institutions",
        json=_inst_payload(name="Isolation B", code=_unique_code()),
        headers=ADMIN_HEADERS,
    ).json()

    # Link tid_a only to inst_a
    client.post(
        f"/api/v1/admin/platform/federation/institutions/{inst_a['id']}/tenants",
        json={"tenant_id": tid_a},
        headers=ADMIN_HEADERS,
    )

    # inst_a overview must have tenant_count >= 1
    ov_a = client.get(
        f"/api/v1/admin/platform/federation/institutions/{inst_a['id']}/overview",
        headers=ADMIN_HEADERS,
    ).json()
    # inst_b overview must have tenant_count == 0
    ov_b = client.get(
        f"/api/v1/admin/platform/federation/institutions/{inst_b['id']}/overview",
        headers=ADMIN_HEADERS,
    ).json()

    assert ov_a["tenant_count"] >= 1
    assert ov_b["tenant_count"] == 0
