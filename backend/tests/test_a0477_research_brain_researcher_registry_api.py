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


def test_researcher_registry_requires_auth() -> None:
    assert client.get(f"{BASE}/researchers").status_code in (401, 403)


@patch("app.modules.research_science.runtime_shell_router.service.list_researchers_service")
def test_researcher_registry_list_surface(mock_list) -> None:
    mock_list.return_value = {
        "items": [
            {
                "researcher_id": "R-100",
                "employee_id": "EMP-100",
                "full_name": "Dr. Ada Lovelace",
                "position": "Principal Investigator",
                "faculty": "Engineering",
                "department": "Computer Science",
                "laboratory": "AI Systems Lab",
                "research_areas": ["AI", "Systems"],
                "specializations": ["ML"],
                "active_projects": 2,
                "active_grants": 1,
                "publication_count": 14,
                "citation_count": 240,
                "h_index": 11,
                "risk_level": "LOW",
                "status": "ACTIVE",
            }
        ]
    }

    resp = client.get(f"{BASE}/researchers", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["researcher_id"] == "R-100"


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_dashboard_summary_service")
def test_researcher_summary_surface(mock_summary) -> None:
    mock_summary.return_value = {
        "tenant_id": 1,
        "total_researchers": 6,
        "active_researchers": 5,
        "high_risk_researchers": 1,
        "publication_total": 42,
        "active_projects_total": 8,
        "active_grants_total": 4,
    }

    resp = client.get(f"{BASE}/researchers/summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["high_risk_researchers"] == 1


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_service")
def test_researcher_profile_surface(mock_researcher) -> None:
    mock_researcher.return_value = {
        "researcher_id": "R-100",
        "employee_id": "EMP-100",
        "full_name": "Dr. Ada Lovelace",
        "position": "Principal Investigator",
        "faculty": "Engineering",
        "department": "Computer Science",
        "laboratory": "AI Systems Lab",
        "research_areas": ["AI", "Systems"],
        "specializations": ["ML"],
        "active_projects": 2,
        "active_grants": 1,
        "publication_count": 14,
        "citation_count": 240,
        "h_index": 11,
        "risk_level": "LOW",
        "status": "ACTIVE",
    }

    resp = client.get(f"{BASE}/researchers/R-100", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Dr. Ada Lovelace"


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_activity_profile_service")
def test_researcher_activity_surface(mock_activity) -> None:
    mock_activity.return_value = {
        "tenant_id": 1,
        "researcher": {
            "researcher_id": "R-100",
            "employee_id": "EMP-100",
            "full_name": "Dr. Ada Lovelace",
            "position": "Principal Investigator",
            "faculty": "Engineering",
            "department": "Computer Science",
            "laboratory": "AI Systems Lab",
            "research_areas": ["AI", "Systems"],
            "specializations": ["ML"],
            "status": "ACTIVE",
        },
        "project_summary": {"active_projects": 2},
        "grant_summary": {"active_grants": 1},
        "publication_summary": {"publication_count": 14, "citation_count": 240},
        "scientometric_summary": {"h_index": 11, "citation_count": 240},
    }

    resp = client.get(f"{BASE}/researchers/R-100/activity", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["scientometric_summary"]["h_index"] == 11


@patch("app.modules.research_science.runtime_shell_router.service.get_researcher_risk_profile_service")
def test_researcher_risk_surface(mock_risk) -> None:
    mock_risk.return_value = {
        "tenant_id": 1,
        "researcher_id": "R-100",
        "risk_level": "MEDIUM",
        "workload": {"active_projects": 3, "active_grants": 2, "publication_count": 9},
        "signals": ["workload_pressure", "publication_stagnation"],
        "notes": ["Elevated workload", "Publication throughput dropped in trailing quarter"],
    }

    resp = client.get(f"{BASE}/researchers/R-100/risk", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] == "MEDIUM"
    assert "workload_pressure" in body["signals"]
