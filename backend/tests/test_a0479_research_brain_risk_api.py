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
        user_id="702",
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


def test_research_risk_requires_auth() -> None:
    assert client.get(f"{BASE}/risk/dashboard").status_code in (401, 403)


@patch("app.modules.research_science.runtime_shell_router.service.get_research_risk_profile_service")
def test_research_risk_dashboard_surface(mock_profile) -> None:
    mock_profile.return_value = {
        "tenant_id": 1,
        "generated_at": "2026-06-10T00:00:00Z",
        "summary": {
            "overall_risk_score": 62.5,
            "severity": "HIGH",
            "publication_risk": 58.0,
            "grant_risk": 72.0,
            "ethics_risk": 48.0,
            "scientometric_risk": 66.0,
            "execution_risk": 68.5,
            "risk_heatmap": {
                "publication": "MEDIUM",
                "grant": "HIGH",
                "ethics": "MEDIUM",
                "scientometric": "HIGH",
                "execution": "HIGH",
            },
            "top_critical_risks": ["grant_execution_risk", "research_output_drop"],
        },
        "signals": [
            {
                "family": "publication_delay",
                "owner": "brain_core",
                "dimension": "publication",
                "source": "research_science",
                "severity": "MEDIUM",
                "observed_count": 2,
                "affected_entities": ["R-100"],
                "description": "Publication delivery delay detected.",
                "read_only": True,
            },
            {
                "family": "grant_execution_risk",
                "owner": "brain_core",
                "dimension": "grant",
                "source": "research_grants",
                "severity": "HIGH",
                "observed_count": 3,
                "affected_entities": ["R-200"],
                "description": "Grant execution milestones are at risk.",
                "read_only": True,
            },
        ],
        "trends": [
            {
                "dimension": "publication",
                "current_score": 58.0,
                "previous_score": 50.0,
                "trend_direction": "up",
                "severity": "MEDIUM",
            }
        ],
        "recommendations": ["Review stalled publications."],
        "provider_execution_enabled": False,
        "external_calls_enabled": False,
    }

    resp = client.get(f"{BASE}/risk/dashboard", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["overall_risk_score"] == 62.5
    assert body["provider_execution_enabled"] is False
    assert body["external_calls_enabled"] is False


@patch("app.modules.research_science.runtime_shell_router.service.get_research_risk_summary_service")
def test_research_risk_summary_surface(mock_summary) -> None:
    mock_summary.return_value = {
        "overall_risk_score": 62.5,
        "severity": "HIGH",
        "publication_risk": 58.0,
        "grant_risk": 72.0,
        "ethics_risk": 48.0,
        "scientometric_risk": 66.0,
        "execution_risk": 68.5,
        "risk_heatmap": {
            "publication": "MEDIUM",
            "grant": "HIGH",
            "ethics": "MEDIUM",
            "scientometric": "HIGH",
            "execution": "HIGH",
        },
        "top_critical_risks": ["grant_execution_risk", "research_output_drop"],
    }

    resp = client.get(f"{BASE}/risk/summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["risk_heatmap"]["grant"] == "HIGH"


@patch("app.modules.research_science.runtime_shell_router.service.get_research_risk_signals_service")
def test_research_risk_signals_surface(mock_signals) -> None:
    mock_signals.return_value = [
        {
            "family": "publication_delay",
            "owner": "brain_core",
            "dimension": "publication",
            "source": "research_science",
            "severity": "MEDIUM",
            "observed_count": 2,
            "affected_entities": ["R-100"],
            "description": "Publication delivery delay detected.",
            "read_only": True,
        },
        {
            "family": "grant_execution_risk",
            "owner": "brain_core",
            "dimension": "grant",
            "source": "research_grants",
            "severity": "HIGH",
            "observed_count": 3,
            "affected_entities": ["R-200"],
            "description": "Grant execution milestones are at risk.",
            "read_only": True,
        },
        {
            "family": "ethics_expiration_risk",
            "owner": "brain_core",
            "dimension": "ethics",
            "source": "research_ethics",
            "severity": "MEDIUM",
            "observed_count": 1,
            "affected_entities": ["ETH-1"],
            "description": "Ethics review expiry window detected.",
            "read_only": True,
        },
        {
            "family": "citation_decline_risk",
            "owner": "brain_core",
            "dimension": "scientometric",
            "source": "analytics",
            "severity": "HIGH",
            "observed_count": 2,
            "affected_entities": ["R-100"],
            "description": "Citation decline trend detected.",
            "read_only": True,
        },
        {
            "family": "low_visibility_risk",
            "owner": "brain_core",
            "dimension": "scientometric",
            "source": "publication_registry",
            "severity": "HIGH",
            "observed_count": 2,
            "affected_entities": ["R-300"],
            "description": "Low visibility profile detected.",
            "read_only": True,
        },
        {
            "family": "research_output_drop",
            "owner": "brain_core",
            "dimension": "execution",
            "source": "research_science",
            "severity": "HIGH",
            "observed_count": 1,
            "affected_entities": ["R-400"],
            "description": "Research output drop detected.",
            "read_only": True,
        },
    ]

    resp = client.get(f"{BASE}/risk/signals", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    families = {item["family"] for item in resp.json()}
    assert {
        "publication_delay",
        "grant_execution_risk",
        "ethics_expiration_risk",
        "citation_decline_risk",
        "low_visibility_risk",
        "research_output_drop",
    } == families


@patch("app.modules.research_science.runtime_shell_router.service.get_research_risk_trends_service")
@patch("app.modules.research_science.runtime_shell_router.service.get_research_risk_recommendations_service")
def test_research_risk_trends_and_recommendations_surfaces(mock_recommendations, mock_trends) -> None:
    mock_trends.return_value = [
        {
            "dimension": "publication",
            "current_score": 58.0,
            "previous_score": 50.0,
            "trend_direction": "up",
            "severity": "MEDIUM",
        },
        {
            "dimension": "grant",
            "current_score": 72.0,
            "previous_score": 61.0,
            "trend_direction": "up",
            "severity": "HIGH",
        },
    ]
    mock_recommendations.return_value = [
        "Escalate near-deadline grants for delivery review.",
        "Review stalled publications and confirm output recovery plans.",
    ]

    trends_resp = client.get(f"{BASE}/risk/trends", headers=ADMIN_HEADERS)
    recommendations_resp = client.get(f"{BASE}/risk/recommendations", headers=ADMIN_HEADERS)

    assert trends_resp.status_code == 200
    assert recommendations_resp.status_code == 200
    assert len(trends_resp.json()) == 2
    assert recommendations_resp.json()[0].startswith("Escalate near-deadline grants")