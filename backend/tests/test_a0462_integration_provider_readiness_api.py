from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.integration_provider_readiness import API_PREFIX
from app.modules.integration_provider_readiness import models


client = TestClient(app)


def _headers(permission: str, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0462-admin-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.fixture(autouse=True)
def db_factory() -> Generator[None, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine, tables=[model.__table__ for model in models.ALL_MODELS])
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    previous = getattr(app.state, "integration_provider_readiness_session_factory", None)
    app.state.integration_provider_readiness_session_factory = session_local
    try:
        yield
    finally:
        app.state.integration_provider_readiness_session_factory = previous
        models.Base.metadata.drop_all(bind=engine, tables=[model.__table__ for model in models.ALL_MODELS])


EXPECTED_PATHS = {
    "/providers",
    "/providers/{record_id}",
    "/providers/by-type/{provider_type}",
    "/providers/{provider_id}/profiles",
    "/profiles/{profile_id}",
    "/providers/{provider_id}/capabilities",
    "/capabilities/{capability_id}",
    "/providers/{provider_id}/assessments",
    "/assessments/{assessment_id}",
    "/providers/{provider_id}/evidence",
    "/evidence/{evidence_id}",
    "/providers/{provider_id}/evidence-links",
    "/evidence/{evidence_id}/links",
    "/providers/{provider_id}/compliance-reviews",
    "/providers/{provider_id}/security-reviews",
    "/compliance-reviews/{review_id}",
    "/security-reviews/{review_id}",
    "/providers/{provider_id}/risks",
    "/providers/{provider_id}/exceptions",
    "/exceptions/{exception_id}",
    "/providers/{provider_id}/audits",
    "/providers/{provider_id}/health",
    "/health-snapshots",
    "/health-summary",
    "/providers/{provider_id}/plans",
    "/plans/{plan_id}",
    "/roadmap",
    "/dashboards",
    "/dashboards/{dashboard_name}",
}


class TestRouteInventory:
    def test_route_path_count(self) -> None:
        paths = {path.removeprefix(API_PREFIX) for path in app.openapi()["paths"] if path.startswith(API_PREFIX)}
        assert len(paths) == 29
        assert paths == EXPECTED_PATHS

    def test_method_split(self) -> None:
        paths = {path: data for path, data in app.openapi()["paths"].items() if path.startswith(API_PREFIX)}
        get_count = sum(1 for data in paths.values() if "get" in data)
        post_count = sum(1 for data in paths.values() if "post" in data)
        put_count = sum(1 for data in paths.values() if "put" in data)
        delete_count = sum(1 for data in paths.values() if "delete" in data)
        assert get_count == 24
        assert post_count == 10
        assert put_count == 8
        assert delete_count == 2


@pytest.mark.parametrize(
    ("path", "permission"),
    [
        (f"{API_PREFIX}/providers", "admin.integration_provider_readiness.registry.list"),
        (f"{API_PREFIX}/health-summary", "admin.integration_provider_readiness.readiness_assessment.read"),
        (f"{API_PREFIX}/dashboards", "admin.integration_provider_readiness.dashboard.overview.read"),
    ],
)
def test_route_authenticated(path: str, permission: str) -> None:
    response = client.get(path, headers=_headers(permission))
    assert response.status_code == 200


def test_cross_tenant_denied() -> None:
    headers = _headers("admin.integration_provider_readiness.registry.list", tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = client.get(f"{API_PREFIX}/providers", headers=headers)
    assert response.status_code == 403


def test_dashboard_payload_flags() -> None:
    response = client.get(f"{API_PREFIX}/dashboards", headers=_headers("admin.integration_provider_readiness.dashboard.overview.read"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 6
    for item in payload["items"]:
        assert item["readiness_only"] is True
        assert item["fake_metrics"] is False
        assert item["provider_connected"] is False
        assert item["live_provider_calls"] is False
        assert item["external_submission"] is False