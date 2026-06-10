from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_shell_service import ReportingRuntimeShellService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime"


def _headers(*, tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id="702",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_reporting_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_reporting_runtime_surface_contract() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    assert body["tenant_id"] == 1
    assert body["reporting_center_name"] == "Reporting Brain Runtime Shell"
    assert body["active_reporting_cycles"] >= 1
    assert body["active_submissions"] >= 1
    assert body["active_deadlines"] >= 1
    assert body["provider_readiness"]["owner_module"] == "regulatory_reporting_integration"
    assert body["provider_readiness"]["provider_readiness"] == "NON_LIVE_PROFILE_ONLY"
    assert body["compliance_score"] >= 55
    assert body["read_only"] is True
    assert body["auditability_preserved"] is True
    assert body["generated_at"]


def test_reporting_runtime_preserves_tenant_isolation() -> None:
    service = ReportingRuntimeShellService()
    body2 = service.get_runtime_shell(2).model_dump(mode="json")
    body9 = service.get_runtime_shell(9).model_dump(mode="json")

    assert body2["tenant_id"] == 2
    assert body9["tenant_id"] == 9
    assert body2["active_reporting_cycles"] != body9["active_reporting_cycles"]


def test_reporting_runtime_provider_boundaries_are_non_live() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    provider = response.json()["provider_readiness"]

    assert provider["live_integrations_enabled"] is False
    assert provider["sync_enabled"] is False
    assert provider["submission_execution_enabled"] is False


def test_reporting_runtime_rbac_roles_surface() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    assert body["rbac_roles"] == [
        "reporting_admin",
        "vice_rector",
        "quality_manager",
        "auditor",
        "analyst",
    ]
    assert body["widgets"] == [
        "Reporting Overview",
        "Provider Readiness",
        "Compliance Summary",
        "Reporting Deadlines",
        "Reporting Status",
    ]
