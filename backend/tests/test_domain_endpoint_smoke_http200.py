from __future__ import annotations

import os

import pytest

from app.core.db import clear_shared_engine
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


pytestmark = pytest.mark.integration

_DATABASE_URL: str = os.getenv("DATABASE_URL", "")


def _enable_real_db(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DATABASE_URL:
        pytest.skip("DATABASE_URL not set - skipping domain endpoint smoke")
    monkeypatch.setenv("DATABASE_URL", _DATABASE_URL)
    clear_shared_engine()


def _smoke_headers() -> dict[str, str]:
    permissions = [
        "advising.read",
        "alumni.read",
        "asset_inventory.read",
        "career_services.read",
        "facilities.read",
        "faculty.read",
        "finance.read",
        "financial_aid.read",
        "housing.read",
        "hr.read",
        "operations.read",
        "procurement.read",
        "research.read",
        "student_life.read",
        "student_services.read",
        "admin.faculty.read",
    ]
    token = create_access_token(
        user_id="domain.smoke@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=permissions,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/admin/advising",
        "/api/admin/hr-payroll/employees",
        "/api/admin/student-services/tickets",
        "/api/admin/career-services",
        "/api/admin/financial-aid",
        "/api/admin/housing",
        "/api/admin/alumni",
        "/api/admin/research/grants",
        "/api/admin/facilities/work-orders",
        "/api/admin/procurement/vendors",
        "/api/admin/student-life/counseling-cases",
        "/api/admin/student-life/wellbeing-checkins",
        "/api/admin/delinquency-collections",
        "/api/admin/budget-planning/plans",
        "/api/admin/asset-inventory/items",
        "/api/admin/operations/facility-issues",
        "/api/admin/campus-sla/sla-records",
        "/api/admin/transport/routes",
        "/api/admin/dining/menus",
        "/api/admin/security-operations/incidents",
        "/api/admin/research-ethics/reviews",
        "/api/admin/ip-management/assets",
        "/api/admin/equipment-booking/equipment",
        "/api/admin/scholarship/applications",
        "/api/admin/communications/messages",
        "/api/admin/faculty-performance-kpis",
        "/api/admin/teaching-quality/dashboard/ENG?term_id=20261",
    ],
)
def test_domain_endpoints_return_http200_not_500(
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
) -> None:
    """Release smoke: every listed domain endpoint must return HTTP 200.

    This catches regressions where DB wiring exists but runtime paths still 500.
    """
    _enable_real_db(monkeypatch)
    response = client.get(endpoint, headers=_smoke_headers())
    assert response.status_code == 200, f"{endpoint} returned {response.status_code}: {response.text}"
