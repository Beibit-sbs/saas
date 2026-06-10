from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.research_science.dependencies import get_research_science_db
from app.modules.research_science.permissions import ALL_PERMISSIONS
from tests.conftest import client


BASE = "/api/admin/research-brain"


def _admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="601",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=sorted(ALL_PERMISSIONS),
    )
    return {"Authorization": f"Bearer {token}"}


ADMIN_HEADERS = _admin_headers()


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_research_science_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_research_science_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_runtime_shell_requires_auth() -> None:
    assert client.get(f"{BASE}/shell").status_code in (401, 403)


@patch("app.modules.research_science.runtime_shell_router.service.get_research_brain_shell_service")
def test_runtime_shell_surface(mock_shell) -> None:
    mock_shell.return_value = {
        "tenant_id": 1,
        "owner_module": "research_science",
        "runtime_boundary": "UNIFIED_READ_ONLY_RUNTIME_SHELL",
        "navigation_entry": "/console/research-brain",
        "bridge_modules": ["research", "analytics", "brain_core"],
        "read_only_aggregation": True,
        "provider_execution_enabled": False,
        "external_calls_enabled": False,
    }
    resp = client.get(f"{BASE}/shell", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner_module"] == "research_science"
    assert body["provider_execution_enabled"] is False


@patch("app.modules.research_science.runtime_shell_router.service.get_research_brain_orchestration_service")
def test_orchestration_surface(mock_orchestration) -> None:
    mock_orchestration.return_value = {
        "tenant_id": 1,
        "projects": {"source_module": "research_science", "read_only": True, "total": 3, "notes": "projects"},
        "grants": {"source_module": "research_science", "read_only": True, "total": 2, "notes": "grants"},
        "publications": {"source_module": "research_science", "read_only": True, "total": 4, "notes": "publications"},
        "ethics": {"source_module": "research_ethics", "read_only": True, "total": 1, "notes": "ethics"},
        "kpi": {"source_module": "analytics", "read_only": True, "total": 4, "notes": "kpi"},
        "signals": {"source_module": "brain_core", "read_only": True, "total": 4, "notes": "signals"},
        "researchers": {"source_module": "research_science", "read_only": True, "total": 6, "notes": "researchers"},
        "researcher_summary": {"source_module": "research_science", "read_only": True, "total": 1, "notes": "researcher_summary"},
        "researcher_health": {"source_module": "analytics", "read_only": True, "total": 1, "notes": "researcher_health"},
        "researcher_workload": {"source_module": "research_science", "read_only": True, "total": 6, "notes": "researcher_workload"},
        "researcher_risk": {"source_module": "brain_core", "read_only": True, "total": 6, "notes": "researcher_risk"},
        "scientometrics": {"source_module": "analytics", "read_only": True, "total": 5, "notes": "scientometrics"},
        "citation_analytics": {"source_module": "analytics", "read_only": True, "total": 5, "notes": "citation_analytics"},
        "impact_analytics": {"source_module": "analytics", "read_only": True, "total": 5, "notes": "impact_analytics"},
        "publication_impact": {"source_module": "publication_registry", "read_only": True, "total": 5, "notes": "publication_impact"},
        "researcher_ranking": {"source_module": "analytics", "read_only": True, "total": 5, "notes": "researcher_ranking"},
        "risk_profile": {"source_module": "brain_core", "read_only": True, "total": 1, "notes": "risk_profile"},
        "risk_summary": {"source_module": "brain_core", "read_only": True, "total": 1, "notes": "risk_summary"},
        "risk_signals": {"source_module": "brain_core", "read_only": True, "total": 6, "notes": "risk_signals"},
        "risk_trends": {"source_module": "brain_core", "read_only": True, "total": 5, "notes": "risk_trends"},
        "risk_recommendations": {"source_module": "brain_core", "read_only": True, "total": 3, "notes": "risk_recommendations"},
        "dashboard_summary": {"source_module": "research_science", "read_only": True, "total": 1, "notes": "dashboard_summary"},
        "dashboard_kpi_plane": {"source_module": "analytics", "read_only": True, "total": 10, "notes": "dashboard_kpi_plane"},
        "dashboard_signal_plane": {"source_module": "brain_core", "read_only": True, "total": 9, "notes": "dashboard_signal_plane"},
        "dashboard_risk_plane": {"source_module": "brain_core", "read_only": True, "total": 5, "notes": "dashboard_risk_plane"},
        "dashboard_scientometric_plane": {"source_module": "analytics", "read_only": True, "total": 5, "notes": "dashboard_scientometric_plane"},
    }
    resp = client.get(f"{BASE}/orchestration", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["kpi"]["source_module"] == "analytics"


@patch("app.modules.research_science.runtime_shell_router.service.get_research_brain_kpi_surface_service")
def test_kpi_surface(mock_kpi) -> None:
    mock_kpi.return_value = {
        "tenant_id": 1,
        "owner_module": "analytics",
        "publication_count": 6,
        "grant_count": 4,
        "project_count": 5,
        "ethics_count": 2,
        "read_only": True,
        "provider_execution_enabled": False,
    }
    resp = client.get(f"{BASE}/kpis", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner_module"] == "analytics"
    assert body["project_count"] == 5


@patch("app.modules.research_science.runtime_shell_router.service.get_research_brain_signal_surface_service")
def test_signal_surface(mock_signals) -> None:
    mock_signals.return_value = {
        "tenant_id": 1,
        "signals": [
            {
                "family": "publication_risk",
                "owner": "brain_core",
                "source": "research.publications",
                "consumer": "research_dashboard",
                "review_queue": "research_review_queue",
                "read_only": True,
                "scoring_engine_enabled": False,
                "observed_count": 1,
            },
            {
                "family": "grant_risk",
                "owner": "brain_core",
                "source": "research_grants",
                "consumer": "grant_dashboard",
                "review_queue": "grants_review_queue",
                "read_only": True,
                "scoring_engine_enabled": False,
                "observed_count": 1,
            },
            {
                "family": "ethics_risk",
                "owner": "brain_core",
                "source": "research_ethics",
                "consumer": "risk_dashboard",
                "review_queue": "ethics_review_queue",
                "read_only": True,
                "scoring_engine_enabled": False,
                "observed_count": 1,
            },
            {
                "family": "project_delay",
                "owner": "brain_core",
                "source": "research_science.projects",
                "consumer": "operations_dashboard",
                "review_queue": "project_delay_queue",
                "read_only": True,
                "scoring_engine_enabled": False,
                "observed_count": 1,
            },
        ],
    }
    resp = client.get(f"{BASE}/signals", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["signals"]) == 4


@patch("app.modules.research_science.runtime_shell_router.service.get_research_brain_rbac_validation_service")
def test_rbac_validation_surface(mock_rbac) -> None:
    mock_rbac.return_value = {
        "tenant_id": 1,
        "tenant": "PASS",
        "rbac": "PASS",
        "audit": "PASS",
        "roles": [
            {"role": "researcher", "required_permissions": ["research.read"], "status": "PASS"},
            {"role": "research_admin", "required_permissions": ["research_science.audit.read"], "status": "PASS"},
        ],
    }
    resp = client.get(f"{BASE}/rbac-validation", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tenant"] == "PASS"
    assert body["rbac"] == "PASS"
    assert body["audit"] == "PASS"
