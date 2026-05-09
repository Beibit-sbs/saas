"""A-025.3 — Rector KPI evidence drilldown: read-only, tenant-scoped, deterministic.

Constraints verified by this suite:
- No DB mutation (all functions return dict, no side-effect on drilldown path)
- No fake values — unavailable metrics labelled "Unavailable" not synthesised
- No autonomous decisions — readonly/no_policy_enforcement/no_autonomous_decision flags
- Tenant isolation — tenant_id <= 0 raises ValueError
- Determinism — same input cards produce same drilldown output
- API contract — GET /platform/kpi/drilldown returns 200 with valid schema
"""

from __future__ import annotations

import importlib
import pytest

from app.platform.kpi import service as kpi_service
from app.platform.kpi.schemas import RectorKpiDrilldownSummarySchema
from tests.conftest import ADMIN_HEADERS, client


# ---------------------------------------------------------------------------
# Module import sanity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_name",
    [
        "app.platform.kpi.service",
        "app.platform.kpi.schemas",
    ],
)
def test_a0253_module_imports_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# tenant_id guard — fail-closed on invalid input
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_tenant_id", [0, -1, -99])
def test_a0253_invalid_tenant_id_raises(bad_tenant_id: int) -> None:
    """get_rector_kpi_drilldown must raise ValueError for non-positive tenant_id."""
    with pytest.raises(ValueError):
        kpi_service.get_rector_kpi_drilldown(tenant_id=bad_tenant_id, uow=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _build_rector_kpi_evidence_drilldowns — unit contract
# ---------------------------------------------------------------------------


def test_a0253_drilldown_returns_all_configured_domains() -> None:
    """Every RECTOR_KPI_EVIDENCE_DRILLDOWN_CONFIG entry must produce one drilldown row."""
    drilldowns = kpi_service._build_rector_kpi_evidence_drilldowns(cards=[])
    config_count = len(kpi_service.RECTOR_KPI_EVIDENCE_DRILLDOWN_CONFIG)
    assert len(drilldowns) == config_count


def test_a0253_drilldown_with_empty_cards_marks_all_unavailable() -> None:
    drilldowns = kpi_service._build_rector_kpi_evidence_drilldowns(cards=[])
    for d in drilldowns:
        assert d["risk_level"] == "unavailable", f"Expected unavailable for {d['domain_id']}"


def test_a0253_drilldown_is_deterministic() -> None:
    """Same card input must produce identical output on two consecutive calls."""
    cards = [
        {"metric_key": "academic_integrity_high_risk_count", "value": 3, "title": "High Risk", "metadata_json": {}},
        {"metric_key": "security_high_risk_incidents_count", "value": 1, "title": "High Security", "metadata_json": {}},
    ]
    result1 = kpi_service._build_rector_kpi_evidence_drilldowns(cards=cards)
    result2 = kpi_service._build_rector_kpi_evidence_drilldowns(cards=cards)
    assert result1 == result2


def test_a0253_drilldown_does_not_synthesise_unavailable_metrics() -> None:
    """A missing metric must not produce a synthetic positive value."""
    drilldowns = kpi_service._build_rector_kpi_evidence_drilldowns(cards=[])
    for d in drilldowns:
        for src in d.get("evidence_sources", []):
            assert src["available"] is False
            assert src["value_label"] == "Unavailable"


def test_a0253_drilldown_with_critical_card_sets_critical_risk_level() -> None:
    cards = [
        {
            "metric_key": "academic_integrity_high_risk_count",
            "value": 5,
            "title": "High Risk",
            "metadata_json": {},
        }
    ]
    drilldowns = kpi_service._build_rector_kpi_evidence_drilldowns(cards=cards)
    academic = next(d for d in drilldowns if d["domain_id"] == "academic-governance")
    assert academic["risk_level"] == "critical"


def test_a0253_drilldown_readonly_and_tenant_scoped_flags_always_present() -> None:
    drilldowns = kpi_service._build_rector_kpi_evidence_drilldowns(cards=[])
    for d in drilldowns:
        assert d["readonly"] is True
        assert d["tenant_scoped"] is True


# ---------------------------------------------------------------------------
# get_rector_dashboard — drilldowns now embedded
# ---------------------------------------------------------------------------


def test_a0253_rector_dashboard_contains_drilldowns_key() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/dashboard?tenant_id=1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "drilldowns" in body
    assert isinstance(body["drilldowns"], list)


# ---------------------------------------------------------------------------
# GET /platform/kpi/drilldown — API contract
# ---------------------------------------------------------------------------


def test_a0253_drilldown_endpoint_returns_200() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/drilldown?tenant_id=1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200


def test_a0253_drilldown_endpoint_schema_valid() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/drilldown?tenant_id=1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    payload = RectorKpiDrilldownSummarySchema.model_validate(resp.json())
    assert payload.tenant_id == 1
    assert payload.total_domains == len(kpi_service.RECTOR_KPI_EVIDENCE_DRILLDOWN_CONFIG)
    assert payload.readonly is True
    assert payload.tenant_scoped is True
    assert payload.no_policy_enforcement is True
    assert payload.no_autonomous_decision is True
    assert payload.no_remediation_action is True


def test_a0253_drilldown_endpoint_unauthenticated_returns_401() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/drilldown?tenant_id=1")
    assert resp.status_code == 401


def test_a0253_drilldown_endpoint_domains_list_non_empty() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/drilldown?tenant_id=1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["domains"]) == len(kpi_service.RECTOR_KPI_EVIDENCE_DRILLDOWN_CONFIG)


def test_a0253_drilldown_endpoint_counts_are_non_negative() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/drilldown?tenant_id=1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_domains"] >= 0
    assert body["review_required_count"] >= 0
    assert body["unavailable_domains_count"] >= 0
    assert body["critical_domains_count"] >= 0
    assert body["high_domains_count"] >= 0


def test_a0253_drilldown_source_is_kpi_engine() -> None:
    resp = client.get("/api/v1/admin/platform/kpi/drilldown?tenant_id=1", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["source"] == "kpi_metrics_engine_v1"
