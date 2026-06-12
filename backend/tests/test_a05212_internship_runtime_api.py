from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.academic_operations.dependencies import get_academic_operations_db
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


BASE = "/api/academic-operations/runtime/internship"


def _summary_headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="778",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["academic_operations.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_academic_operations_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_academic_operations_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def test_internship_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


@patch("app.modules.academic_operations_runtime.internship_runtime_router.get_internship_runtime")
def test_internship_runtime_returns_contract(mock_runtime) -> None:
    mock_runtime.return_value = {
        "tenant_id": 1,
        "overview": {
            "owner_module": "academic_operations_runtime",
            "runtime_scope": "INTERNSHIP_RUNTIME",
            "generated_at": "2026-06-12T00:00:00Z",
            "read_only": True,
            "aggregator_only": True,
        },
        "internship_statistics": {
            "participation_rate": 80.0,
            "completion_rate": 62.5,
            "active_rate": 55.0,
            "placement_rate": 40.0,
            "total_internships": 20,
            "active_internships": 11,
            "completed_internships": 9,
            "employer_count": 6,
        },
        "placement_distribution": {
            "by_employer": {"EMP-1": 5, "EMP-2": 3},
            "by_industry": {"engineering": 6, "finance": 2},
            "by_department": {"cs": 4, "ba": 4},
            "read_only": True,
        },
        "completion_summary": {
            "completed": 9,
            "active": 11,
            "overdue": 2,
            "read_only": True,
        },
        "active_internships": {
            "owner_module": "internship",
            "records": 2,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["internship", "academic_operations"],
            "items": [
                {
                    "internship_identifier": "POST-1",
                    "employer": "EMP-1",
                    "student_count": 3,
                    "status": "ACTIVE",
                }
            ],
        },
        "employer_engagement": {
            "employer_participation_rate": 60.0,
            "repeat_employers": 2,
            "placement_volume": 8,
            "employer_count": 6,
            "read_only": True,
        },
        "internship_risk_summary": {
            "high_risk_count": 2,
            "medium_risk_count": 4,
            "low_risk_count": 14,
            "read_only": True,
        },
        "high_risk_internships": {
            "owner_module": "internship",
            "records": 1,
            "read_only": True,
            "aggregator_only": True,
            "source_modules": ["internship", "brain_core", "academic_operations"],
            "items": [
                {
                    "internship_identifier": "POST-5",
                    "employer": "EMP-2",
                    "student_count": 0,
                    "risk_reason": "no_participation_detected",
                }
            ],
        },
        "internship_signals": {
            "generated_signals": 2,
            "signal_types": ["AO-SIG-INT-001", "AO-SIG-INT-002"],
            "indicators": ["high_risk_internships_present", "overdue_internships_detected"],
            "read_only": True,
        },
        "internship_readiness": {
            "readiness_score": 71,
            "readiness_classification": "READY",
            "readiness_drivers": ["read_only_runtime", "aggregator_only_runtime"],
            "ready_for_runtime": True,
        },
    }

    response = client.get(BASE, headers=_summary_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["overview"]["runtime_scope"] == "INTERNSHIP_RUNTIME"
    assert body["internship_statistics"]["total_internships"] == 20
    assert body["completion_summary"]["overdue"] == 2


@patch("app.modules.academic_operations_runtime.internship_runtime_router.get_internship_runtime")
def test_internship_runtime_enforces_tenant_isolation(mock_runtime) -> None:
    def _by_tenant(_db, tenant_id: int):
        return {
            "tenant_id": tenant_id,
            "overview": {
                "owner_module": "academic_operations_runtime",
                "runtime_scope": "INTERNSHIP_RUNTIME",
                "generated_at": "2026-06-12T00:00:00Z",
                "read_only": True,
                "aggregator_only": True,
            },
            "internship_statistics": {
                "participation_rate": 0.0,
                "completion_rate": 0.0,
                "active_rate": 0.0,
                "placement_rate": 0.0,
                "total_internships": tenant_id,
                "active_internships": 0,
                "completed_internships": 0,
                "employer_count": 0,
            },
            "placement_distribution": {"by_employer": {}, "by_industry": {}, "by_department": {}, "read_only": True},
            "completion_summary": {"completed": 0, "active": 0, "overdue": 0, "read_only": True},
            "active_internships": {
                "owner_module": "internship",
                "records": 0,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["internship"],
                "items": [],
            },
            "employer_engagement": {
                "employer_participation_rate": 0.0,
                "repeat_employers": 0,
                "placement_volume": 0,
                "employer_count": 0,
                "read_only": True,
            },
            "internship_risk_summary": {
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "read_only": True,
            },
            "high_risk_internships": {
                "owner_module": "internship",
                "records": 0,
                "read_only": True,
                "aggregator_only": True,
                "source_modules": ["internship"],
                "items": [],
            },
            "internship_signals": {
                "generated_signals": 0,
                "signal_types": [],
                "indicators": [],
                "read_only": True,
            },
            "internship_readiness": {
                "readiness_score": 10,
                "readiness_classification": "NOT_READY",
                "readiness_drivers": ["read_only_runtime"],
                "ready_for_runtime": False,
            },
        }

    mock_runtime.side_effect = _by_tenant

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 7, "name": "Tenant-7"}
    tenant7 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 12, "name": "Tenant-12"}
    tenant12 = client.get(BASE, headers=_summary_headers())

    app.dependency_overrides.pop(get_current_tenant, None)

    assert tenant7.status_code == 200
    assert tenant12.status_code == 200
    assert tenant7.json()["tenant_id"] == 7
    assert tenant12.json()["tenant_id"] == 12


@patch("app.modules.academic_operations_runtime.internship_runtime_router.get_internship_runtime")
def test_internship_runtime_requires_summary_permission(mock_runtime) -> None:
    mock_runtime.return_value = {}
    token = create_access_token(
        user_id="779",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["academic_operations.overview.read"],
    )
    response = client.get(BASE, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_internship_runtime_is_read_only() -> None:
    assert client.post(BASE, headers=_summary_headers()).status_code == 405
    assert client.patch(BASE, headers=_summary_headers()).status_code == 405
    assert client.delete(BASE, headers=_summary_headers()).status_code == 405
