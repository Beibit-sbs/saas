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
        user_id="710",
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


def test_research_dashboard_requires_auth() -> None:
    assert client.get(f"{BASE}/dashboard/summary").status_code in (401, 403)


@patch("app.modules.research_science.runtime_shell_router.service.get_research_dashboard_summary_service")
def test_research_dashboard_summary_surface(mock_summary) -> None:
    mock_summary.return_value = {
        "tenant_id": 1,
        "generated_at": "2026-06-10T00:00:00Z",
        "kpis": {
            "researchers": 8,
            "publications": 42,
            "citations": 640,
            "h_index": 66,
            "international_publications": 14,
            "indexed_publications": 21,
            "grants": 7,
            "ethics_reviews": 5,
            "risk_count": 9,
            "signal_count": 9,
        },
        "signals": {
            "owner": "brain_core",
            "signal_count": 9,
            "signals": [
                {
                    "family": "citation_decline",
                    "owner": "brain_core",
                    "dimension": "scientometric",
                    "source": "analytics",
                    "severity": "HIGH",
                    "observed_count": 2,
                    "affected_entities": ["R-100"],
                    "description": "Citation baseline and trend indicate decline risk.",
                    "read_only": True,
                }
            ],
        },
        "risks": {
            "owner": "brain_core",
            "critical_risks": 3,
            "medium_risks": 4,
            "low_risks": 2,
            "trend_direction": "up",
            "recommendations": ["Escalate near-deadline grants for delivery review."],
        },
        "scientometrics": {
            "owner": "analytics",
            "top_researchers": [],
            "citation_leaderboard": [],
            "h_index_leaderboard": [],
            "impact_leaders": [],
            "publication_leaders": [],
        },
        "activity": {
            "generated_at": "2026-06-10T00:00:00Z",
            "publication_activity": 42,
            "grant_activity": 7,
            "ethics_activity": 5,
            "risk_activity": 9,
            "signal_activity": 9,
        },
        "provider_execution_enabled": False,
        "external_calls_enabled": False,
    }

    resp = client.get(f"{BASE}/dashboard/summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["kpis"]["publications"] == 42
    assert payload["provider_execution_enabled"] is False


@patch("app.modules.research_science.runtime_shell_router.service.get_research_dashboard_kpi_plane_service")
@patch("app.modules.research_science.runtime_shell_router.service.get_research_dashboard_signal_plane_service")
@patch("app.modules.research_science.runtime_shell_router.service.get_research_dashboard_risk_plane_service")
@patch("app.modules.research_science.runtime_shell_router.service.get_research_dashboard_scientometric_plane_service")
def test_dashboard_plane_endpoints(
    mock_scientometrics,
    mock_risks,
    mock_signals,
    mock_kpis,
) -> None:
    mock_kpis.return_value = {
        "researchers": 8,
        "publications": 42,
        "citations": 640,
        "h_index": 66,
        "international_publications": 14,
        "indexed_publications": 21,
        "grants": 7,
        "ethics_reviews": 5,
        "risk_count": 9,
        "signal_count": 9,
    }
    mock_signals.return_value = {
        "owner": "brain_core",
        "signal_count": 9,
        "signals": [
            {
                "family": "publication_gap",
                "owner": "brain_core",
                "dimension": "publication",
                "source": "research_science",
                "severity": "HIGH",
                "observed_count": 2,
                "affected_entities": ["R-200"],
                "description": "Researchers with no publications indicate publication gap.",
                "read_only": True,
            }
        ],
    }
    mock_risks.return_value = {
        "owner": "brain_core",
        "critical_risks": 3,
        "medium_risks": 4,
        "low_risks": 2,
        "trend_direction": "up",
        "recommendations": ["Review stalled publications."],
    }
    mock_scientometrics.return_value = {
        "owner": "analytics",
        "top_researchers": [],
        "citation_leaderboard": [],
        "h_index_leaderboard": [],
        "impact_leaders": [],
        "publication_leaders": [],
    }

    kpis_resp = client.get(f"{BASE}/dashboard/kpis", headers=ADMIN_HEADERS)
    signals_resp = client.get(f"{BASE}/dashboard/signals", headers=ADMIN_HEADERS)
    risks_resp = client.get(f"{BASE}/dashboard/risks", headers=ADMIN_HEADERS)
    scientometrics_resp = client.get(f"{BASE}/dashboard/scientometrics", headers=ADMIN_HEADERS)

    assert kpis_resp.status_code == 200
    assert signals_resp.status_code == 200
    assert risks_resp.status_code == 200
    assert scientometrics_resp.status_code == 200
    assert kpis_resp.json()["signal_count"] == 9
    assert signals_resp.json()["signals"][0]["family"] == "publication_gap"
    assert risks_resp.json()["trend_direction"] == "up"
    assert scientometrics_resp.json()["owner"] == "analytics"
