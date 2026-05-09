"""A-024.3 targeted tests for observability L3->L4 operational visibility."""

from __future__ import annotations

import importlib
import inspect

import pytest

import app.main as main_module
from app.modules.observability import service as observability_service
from app.modules.platform_health import service as platform_health_service
from tests.conftest import ADMIN_HEADERS, client


@pytest.mark.parametrize("module_name", ["app.modules.observability.service"])
def test_a0243_observability_module_imports_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0243_tenant_id_must_be_positive(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        observability_service.build_observability_signal(
            tenant_id=tenant_id,
            component="api",
            status="healthy",
            source="test",
            source_entity_type="test",
            source_entity_id="1",
        )


def test_a0243_healthy_signal_produces_healthy_low_summary() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="api",
        status="healthy",
        source="test",
        source_entity_type="probe",
        source_entity_id="api",
    )
    summary = observability_service.build_observability_summary(tenant_id=1, signals=[signal])
    assert summary["overall_status"] == "healthy"
    assert summary["severity"] == "low"


def test_a0243_degraded_signal_increases_severity() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="api",
        status="degraded",
        source="test",
        source_entity_type="probe",
        source_entity_id="api",
    )
    summary = observability_service.build_observability_summary(tenant_id=1, signals=[signal])
    assert summary["overall_status"] == "degraded"
    assert summary["severity"] in {"medium", "high", "critical"}


def test_a0243_unhealthy_signal_sets_review_required() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="database",
        status="unhealthy",
        source="test",
        source_entity_type="probe",
        source_entity_id="db",
    )
    summary = observability_service.build_observability_summary(tenant_id=1, signals=[signal])
    assert summary["overall_status"] == "unhealthy"
    assert summary["review_required"] is True


def test_a0243_unknown_signal_creates_data_quality_note() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="worker",
        status="unknown",
        source="test",
        source_entity_type="probe",
        source_entity_id="worker",
    )
    summary = observability_service.build_observability_summary(tenant_id=1, signals=[signal])
    assert summary["overall_status"] == "unknown"
    assert summary["review_required"] is True
    assert summary["data_quality_note"] is not None


def test_a0243_high_latency_increases_severity() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="api",
        status="healthy",
        latency_ms=2200.0,
        source="test",
        source_entity_type="probe",
        source_entity_id="latency",
    )
    assert signal["severity"] in {"high", "critical"}


def test_a0243_high_error_rate_increases_severity() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="api",
        status="healthy",
        error_rate=0.12,
        source="test",
        source_entity_type="probe",
        source_entity_id="errors",
    )
    assert signal["severity"] in {"high", "critical"}


def test_a0243_dependency_unavailable_increases_severity() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="database",
        status="healthy",
        dependency_available=False,
        source="test",
        source_entity_type="probe",
        source_entity_id="db",
    )
    assert signal["severity"] == "critical"
    assert signal["review_required"] is True


def test_a0243_evidence_lineage_is_deterministic() -> None:
    payload = dict(
        tenant_id=1,
        component="api",
        status="degraded",
        latency_ms=1300.0,
        error_rate=0.03,
        source="metrics.latency",
        source_entity_type="runtime_metrics",
        source_entity_id="latency_snapshot",
    )
    first = observability_service.build_observability_signal(**payload)
    second = observability_service.build_observability_signal(**payload)
    assert first == second


def test_a0243_summary_contains_no_fake_uptime_flag() -> None:
    summary = observability_service.build_observability_summary(
        tenant_id=1,
        signals=[
            observability_service.build_observability_signal(
                tenant_id=1,
                component="api",
                status="healthy",
                source="test",
                source_entity_type="probe",
                source_entity_id="api",
            )
        ],
    )
    assert summary["no_fake_uptime"] is True


def test_a0243_summary_contains_no_fake_sla_flag() -> None:
    summary = observability_service.build_observability_summary(
        tenant_id=1,
        signals=[
            observability_service.build_observability_signal(
                tenant_id=1,
                component="api",
                status="healthy",
                source="test",
                source_entity_type="probe",
                source_entity_id="api",
            )
        ],
    )
    assert summary["no_fake_sla"] is True


def test_a0243_summary_contains_no_external_monitoring_provider_flag() -> None:
    summary = observability_service.build_observability_summary(
        tenant_id=1,
        signals=[
            observability_service.build_observability_signal(
                tenant_id=1,
                component="api",
                status="healthy",
                source="test",
                source_entity_type="probe",
                source_entity_id="api",
            )
        ],
    )
    assert summary["no_external_monitoring_provider"] is True


def test_a0243_no_fake_external_monitoring_provider_in_source() -> None:
    source = inspect.getsource(observability_service).lower()
    for forbidden in ["openai", "anthropic", "google.generativeai", "bedrock", "azure_openai", "datadog", "newrelic"]:
        assert forbidden not in source


def test_a0243_no_fake_alert_execution_claim_exists() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=1,
        component="api",
        status="healthy",
        source="test",
        source_entity_type="probe",
        source_entity_id="api",
    )
    summary = observability_service.build_observability_summary(tenant_id=1, signals=[signal])
    assert signal["no_fake_alert_execution"] is True
    assert summary["no_fake_alert_execution"] is True


def test_a0243_no_level5_or_level6_claim_in_summary() -> None:
    summary = observability_service.build_observability_summary(
        tenant_id=1,
        signals=[
            observability_service.build_observability_signal(
                tenant_id=1,
                component="api",
                status="healthy",
                source="test",
                source_entity_type="probe",
                source_entity_id="api",
            )
        ],
    )
    text = str(summary).lower()
    assert "level 5" not in text
    assert "level 6" not in text


def test_a0243_visible_surface_exists_if_l4_is_claimed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "deep_payload",
        lambda _app: {
            "deep": True,
            "dependencies": {
                "postgresql": {"healthy": True},
                "redis": {"healthy": True},
                "worker": {"healthy": True},
                "scheduler": {"healthy": True},
            },
        },
    )
    monkeypatch.setattr(
        main_module,
        "snapshot_latency_metrics",
        lambda: {
            "p95_latency_ms": 90.0,
            "p99_latency_ms": 150.0,
            "requests_per_minute": 15,
            "http_5xx_count": 0,
        },
    )

    response = client.get("/api/admin/observability/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["visible_surface"] == "/api/admin/observability/summary"


def test_a0243_api_router_contract_works(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "deep_payload",
        lambda _app: {
            "deep": False,
            "dependencies": {
                "postgresql": {"healthy": True},
                "redis": {"healthy": False},
                "worker": {"healthy": False},
                "scheduler": {"healthy": True},
            },
        },
    )
    monkeypatch.setattr(
        main_module,
        "snapshot_latency_metrics",
        lambda: {
            "p95_latency_ms": 1800.0,
            "p99_latency_ms": 2800.0,
            "requests_per_minute": 10,
            "http_5xx_count": 2,
        },
    )

    response = client.get("/api/admin/observability/summary", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tenant_id"] == 1
    assert "evidence_items" in payload
    assert "kpi_visibility" in payload
    assert payload["event_readiness_decision"] == "deferred_to_a0245"


def test_a0243_event_kpi_decision_is_explicitly_deferred() -> None:
    summary = observability_service.build_observability_summary(tenant_id=1, signals=[])
    assert summary["event_readiness_decision"] == "deferred_to_a0245"


def test_a0243_platform_health_integration_compatibility() -> None:
    health_evidence = platform_health_service.build_platform_health_evidence(
        tenant_id=1,
        component="platform_health",
        status="degraded",
        source_entity_type="service",
        source_entity_id="platform_health",
        latency_ms=1400.0,
        error_rate=0.09,
        dependency_available=True,
    )
    signal = observability_service.build_observability_signal_from_platform_health(
        tenant_id=1,
        platform_health_evidence=health_evidence,
    )
    assert signal["component"] == "platform_health"
    assert signal["tenant_id"] == 1
    assert signal["status"] in {"degraded", "unhealthy"}


def test_a0243_summary_enforces_tenant_consistency() -> None:
    signal = observability_service.build_observability_signal(
        tenant_id=2,
        component="api",
        status="healthy",
        source="test",
        source_entity_type="probe",
        source_entity_id="api",
    )
    with pytest.raises(ValueError, match="all observability signals must match tenant_id"):
        observability_service.build_observability_summary(tenant_id=1, signals=[signal])


def test_a0243_summary_integrated_components_include_ai_and_platform_health() -> None:
    signals = [
        observability_service.build_observability_signal(
            tenant_id=1,
            component="ai_routing",
            status="healthy",
            source="test",
            source_entity_type="probe",
            source_entity_id="ai_routing",
        ),
        observability_service.build_observability_signal(
            tenant_id=1,
            component="ai_copilot",
            status="healthy",
            source="test",
            source_entity_type="probe",
            source_entity_id="ai_copilot",
        ),
        observability_service.build_observability_signal(
            tenant_id=1,
            component="platform_health",
            status="degraded",
            source="test",
            source_entity_type="probe",
            source_entity_id="platform_health",
        ),
    ]
    summary = observability_service.build_observability_summary(tenant_id=1, signals=signals)
    assert summary["integrated_components"] == ["ai_copilot", "ai_routing", "platform_health"]
