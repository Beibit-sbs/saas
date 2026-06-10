from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.reporting_runtime.runtime_ranking_service import RankingReportingRuntimeService


client = TestClient(app)
BASE = "/api/admin/reporting-brain/runtime/ranking"


def _headers(
    *,
    tenant_id: int = 1,
    permissions: list[str] | None = None,
    roles: list[str] | None = None,
) -> dict[str, str]:
    token = create_access_token(
        user_id="710",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["admin.reporting_runtime.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def test_ranking_reporting_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_ranking_reporting_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == 403


def test_ranking_reporting_rbac_roles_have_access() -> None:
    for role in ["reporting_admin", "vice_rector", "quality_manager", "research_manager", "auditor", "analyst"]:
        response = client.get(BASE, headers=_headers(roles=[role]))
        assert response.status_code == 200


def test_ranking_reporting_qs_the_coverage_and_signal_inventory() -> None:
    response = client.get(BASE, headers=_headers())
    assert response.status_code == 200
    body = response.json()

    systems = {item["ranking_system"] for item in body["reports"]}
    indicator_names = {item["indicator_name"] for item in body["reports"]}

    assert systems == {"QS", "THE"}
    assert indicator_names == {
        "Academic Reputation",
        "Employer Reputation",
        "Faculty Student Ratio",
        "Citations Per Faculty",
        "International Faculty",
        "International Students",
        "Teaching",
        "Research Environment",
        "Research Quality",
        "International Outlook",
        "Industry Engagement",
    }
    assert set(body["signal_inventory"]) == {
        "ranking_readiness_low",
        "qs_indicator_decline",
        "the_indicator_decline",
        "ranking_risk_high",
        "benchmark_gap_high",
    }
    assert body["read_only"] is True


def test_ranking_reporting_tenant_isolation_service_level() -> None:
    service = RankingReportingRuntimeService()
    tenant2 = service.get_ranking(2).model_dump(mode="json")
    tenant9 = service.get_ranking(9).model_dump(mode="json")

    assert tenant2["tenant_id"] == 2
    assert tenant9["tenant_id"] == 9
    assert tenant2["reports"][0]["id"] != tenant9["reports"][0]["id"]


def test_ranking_reporting_visibility_surfaces() -> None:
    indicators = client.get(f"{BASE}/indicators", headers=_headers())
    readiness = client.get(f"{BASE}/readiness", headers=_headers())
    benchmarks = client.get(f"{BASE}/benchmarks", headers=_headers())
    trends = client.get(f"{BASE}/trends", headers=_headers())
    risks = client.get(f"{BASE}/risks", headers=_headers())

    assert indicators.status_code == 200
    assert readiness.status_code == 200
    assert benchmarks.status_code == 200
    assert trends.status_code == 200
    assert risks.status_code == 200

    indicator_items = indicators.json()["indicators"]
    readiness_items = readiness.json()["readiness"]
    benchmark_items = benchmarks.json()["benchmarks"]
    trend_items = trends.json()["trends"]
    risk_items = risks.json()["risks"]

    assert indicator_items and readiness_items and benchmark_items and trend_items and risk_items
    assert all("indicator_weight" in item for item in indicator_items)
    assert all("readiness_score" in item for item in readiness_items)
    assert all("benchmark_gap" in item for item in benchmark_items)
    assert all("trend_delta" in item for item in trend_items)
    assert all(item["signal_owner_module"] == "brain_core" for item in risk_items)


def test_ranking_reporting_related_endpoints_are_read_only() -> None:
    headers = _headers()
    for endpoint in ["", "/indicators", "/readiness", "/benchmarks", "/trends", "/risks"]:
        response = client.get(f"{BASE}{endpoint}", headers=headers)
        assert response.status_code == 200
        assert response.json()["read_only"] is True
