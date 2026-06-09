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
        user_id="701",
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


def test_scientometrics_requires_auth() -> None:
    assert client.get(f"{BASE}/scientometrics/dashboard").status_code in (401, 403)


@patch("app.modules.research_science.runtime_shell_router.service.get_scientometrics_dashboard_service")
def test_scientometrics_dashboard_surface(mock_dashboard) -> None:
    mock_dashboard.return_value = {
        "tenant_id": 1,
        "top_researchers": [
            {
                "researcher_id": "R-100",
                "citation_count": 100,
                "h_index": 12,
                "i10_index": 10,
                "publication_count": 20,
                "international_publications": 6,
                "indexed_publications": 14,
                "top_publications": ["PUB-1", "PUB-2"],
                "trend_direction": "up",
                "impact_score": 88.5,
                "scientometric_risk": "LOW",
                "external_identities": [
                    {"provider_name": "ORCID", "provider_identifier": "orcid:R-100", "provider_status": "PENDING"}
                ],
                "trends": [
                    {"period": "current", "citation_count": 100, "h_index": 12, "i10_index": 10, "trend_direction": "up", "impact_score": 88.5}
                ],
            }
        ],
        "citation_leaderboard": [
            {
                "researcher_id": "R-100",
                "citation_count": 100,
                "h_index": 12,
                "i10_index": 10,
                "publication_count": 20,
                "international_publications": 6,
                "indexed_publications": 14,
                "top_publications": ["PUB-1"],
                "trend_direction": "up",
                "impact_score": 88.5,
                "scientometric_risk": "LOW",
            }
        ],
        "h_index_leaderboard": [
            {
                "researcher_id": "R-100",
                "citation_count": 100,
                "h_index": 12,
                "i10_index": 10,
                "publication_count": 20,
                "international_publications": 6,
                "indexed_publications": 14,
                "top_publications": ["PUB-1"],
                "trend_direction": "up",
                "impact_score": 88.5,
                "scientometric_risk": "LOW",
            }
        ],
        "publication_impact_summary": [
            {
                "researcher_id": "R-100",
                "publication_count": 20,
                "international_publications": 6,
                "indexed_publications": 14,
                "top_publications": ["PUB-1"],
                "citation_count": 100,
                "h_index": 12,
                "i10_index": 10,
                "trend_direction": "up",
                "impact_score": 88.5,
                "scientometric_risk": "LOW",
            }
        ],
        "scientometric_trend_summary": [
            {"period": "R-100", "citation_count": 100, "h_index": 12, "i10_index": 10, "trend_direction": "up", "impact_score": 88.5}
        ],
        "provider_execution_enabled": False,
        "external_calls_enabled": False,
    }

    resp = client.get(f"{BASE}/scientometrics/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider_execution_enabled"] is False
    assert body["external_calls_enabled"] is False
    assert body["top_researchers"][0]["researcher_id"] == "R-100"


@patch("app.modules.research_science.runtime_shell_router.service.get_scientometric_researcher_ranking_service")
def test_scientometric_ranking_surface(mock_ranking) -> None:
    mock_ranking.return_value = {
        "tenant_id": 1,
        "items": [
            {"researcher_id": "R-100", "rank": 1, "impact_score": 88.5, "scientometric_risk": "LOW"},
            {"researcher_id": "R-200", "rank": 2, "impact_score": 74.0, "scientometric_risk": "MEDIUM"},
        ],
    }

    resp = client.get(f"{BASE}/scientometrics/ranking", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["rank"] == 1


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_scientometric_profile_service")
def test_researcher_scientometric_profile_surface(mock_profile) -> None:
    mock_profile.return_value = {
        "researcher_id": "R-100",
        "citation_count": 100,
        "h_index": 12,
        "i10_index": 10,
        "publication_count": 20,
        "international_publications": 6,
        "indexed_publications": 14,
        "top_publications": ["PUB-1"],
        "trend_direction": "up",
        "impact_score": 88.5,
        "scientometric_risk": "LOW",
        "external_identities": [
            {"provider_name": "ORCID", "provider_identifier": "orcid:R-100", "provider_status": "PENDING"},
            {"provider_name": "Scopus", "provider_identifier": "scopus:R-100", "provider_status": "NOT_CONNECTED"},
            {"provider_name": "WebOfScience", "provider_identifier": "webofscience:R-100", "provider_status": "NOT_CONNECTED"},
            {"provider_name": "GoogleScholar", "provider_identifier": "googlescholar:R-100", "provider_status": "NOT_CONNECTED"},
            {"provider_name": "DOI", "provider_identifier": "doi:R-100", "provider_status": "READY"},
        ],
        "trends": [
            {"period": "current", "citation_count": 100, "h_index": 12, "i10_index": 10, "trend_direction": "up", "impact_score": 88.5}
        ],
    }

    resp = client.get(f"{BASE}/scientometrics/R-100", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    statuses = {identity["provider_status"] for identity in resp.json()["external_identities"]}
    assert statuses.issubset({"NOT_CONNECTED", "READY", "PENDING"})


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_citation_summary_service")
def test_researcher_citation_surface(mock_citation) -> None:
    mock_citation.return_value = {
        "researcher_id": "R-100",
        "citation_count": 100,
        "h_index": 12,
        "i10_index": 10,
        "publication_count": 20,
        "international_publications": 6,
        "indexed_publications": 14,
        "top_publications": ["PUB-1"],
        "trend_direction": "up",
        "impact_score": 88.5,
        "scientometric_risk": "LOW",
    }

    resp = client.get(f"{BASE}/scientometrics/R-100/citations", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["citation_count"] == 100


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_impact_analysis_service")
def test_researcher_impact_surface(mock_impact) -> None:
    mock_impact.return_value = {
        "researcher_id": "R-100",
        "publication_count": 20,
        "international_publications": 6,
        "indexed_publications": 14,
        "top_publications": ["PUB-1"],
        "citation_count": 100,
        "h_index": 12,
        "i10_index": 10,
        "trend_direction": "up",
        "impact_score": 88.5,
        "scientometric_risk": "LOW",
    }

    resp = client.get(f"{BASE}/scientometrics/R-100/impact", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["impact_score"] == 88.5


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_scientometric_trends_service")
def test_scientometric_trends_surface(mock_trends) -> None:
    mock_trends.return_value = [
        {"period": "trailing_12m", "citation_count": 90, "h_index": 11, "i10_index": 9, "trend_direction": "stable", "impact_score": 80.0},
        {"period": "current", "citation_count": 100, "h_index": 12, "i10_index": 10, "trend_direction": "up", "impact_score": 88.5},
    ]

    resp = client.get(f"{BASE}/scientometrics/R-100/trends", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@patch("app.modules.research_science.runtime_shell_router.service.get_research_brain_signal_surface_service")
def test_scientometric_signal_generation_surface(mock_signals) -> None:
    mock_signals.return_value = {
        "tenant_id": 1,
        "signals": [
            {"family": "citation_decline", "owner": "brain_core", "source": "analytics", "consumer": "scientometrics", "review_queue": "scientometrics_review_queue", "read_only": True, "scoring_engine_enabled": False, "observed_count": 1},
            {"family": "publication_stagnation", "owner": "brain_core", "source": "analytics", "consumer": "scientometrics", "review_queue": "scientometrics_review_queue", "read_only": True, "scoring_engine_enabled": False, "observed_count": 1},
            {"family": "impact_drop", "owner": "brain_core", "source": "analytics", "consumer": "scientometrics", "review_queue": "scientometrics_review_queue", "read_only": True, "scoring_engine_enabled": False, "observed_count": 1},
            {"family": "low_visibility", "owner": "brain_core", "source": "analytics", "consumer": "scientometrics", "review_queue": "scientometrics_review_queue", "read_only": True, "scoring_engine_enabled": False, "observed_count": 1},
            {"family": "researcher_ranking_drop", "owner": "brain_core", "source": "analytics", "consumer": "scientometrics", "review_queue": "scientometrics_review_queue", "read_only": True, "scoring_engine_enabled": False, "observed_count": 1},
        ],
    }

    resp = client.get(f"{BASE}/signals", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    families = {item["family"] for item in resp.json()["signals"]}
    assert {"citation_decline", "publication_stagnation", "impact_drop", "low_visibility", "researcher_ranking_drop"}.issubset(families)
