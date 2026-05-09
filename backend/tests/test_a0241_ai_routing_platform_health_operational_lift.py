"""A-024.1 targeted Level-3 operational contract tests.

Scope: ai_routing_control + platform_health L2->L3 evidence-only lift.
No API/frontend assertions, no external AI calls, no fake observability claims.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

from app.modules.ai_routing_control import service as ai_routing_control_service
from app.modules.platform_health import service as platform_health_service


def _routing_input(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "tenant_id": 7,
        "requested_capability": "classification",
        "data_classification": "internal",
        "estimated_cost": 120.0,
        "user_role": "analyst",
        "purpose": "triage assistant",
        "policy_mode": "advisory",
        "source_entity_type": "case",
        "source_entity_id": "C-123",
    }
    payload.update(overrides)
    return payload


def _health_input(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "tenant_id": 7,
        "component": "routing_engine",
        "status": "healthy",
        "source_entity_type": "service",
        "source_entity_id": "routing_engine",
        "latency_ms": 100.0,
        "error_rate": 0.01,
        "dependency_available": True,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "module_name",
    [
        "app.modules.ai_routing_control.service",
        "app.modules.platform_health.service",
    ],
)
def test_a0241_modules_import_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0241_ai_routing_requires_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        ai_routing_control_service.build_ai_routing_control_decision(
            **_routing_input(tenant_id=tenant_id)
        )


def test_a0241_ai_routing_disabled_mode_blocks() -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(
        **_routing_input(policy_mode="disabled")
    )
    assert result["decision_status"] == "blocked"
    assert result["review_required"] is True


@pytest.mark.parametrize("mode", ["monitor_only", "advisory"])
def test_a0241_ai_routing_monitor_and_advisory_are_evidence_only(mode: str) -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(
        **_routing_input(policy_mode=mode)
    )
    assert result["decision_status"] in {"allowed", "review_required"}
    assert result["no_external_call"] is True
    assert result["no_autonomous_execution"] is True


def test_a0241_ai_routing_sensitive_data_requires_review() -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(
        **_routing_input(data_classification="restricted")
    )
    assert result["review_required"] is True
    assert "SENSITIVE_DATA_CLASSIFICATION" in result["safety_reasons"]


def test_a0241_ai_routing_high_cost_requires_review() -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(
        **_routing_input(estimated_cost=2200.0)
    )
    assert result["review_required"] is True
    assert "HIGH_ESTIMATED_COST" in result["safety_reasons"]


def test_a0241_ai_routing_unknown_capability_requires_review_or_block() -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(
        **_routing_input(requested_capability="unknown_capability_x")
    )
    assert result["decision_status"] in {"review_required", "blocked"}
    assert "UNKNOWN_CAPABILITY" in result["safety_reasons"]


def test_a0241_ai_routing_no_external_llm_or_autonomous_fields_exist() -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(**_routing_input())
    assert result["no_external_call"] is True
    assert result["no_autonomous_execution"] is True


def test_a0241_ai_routing_has_no_autonomous_execution_claim() -> None:
    result = ai_routing_control_service.build_ai_routing_control_decision(**_routing_input())
    joined = " ".join(result["policy_reasons"]).lower()
    assert "autonomous" in joined
    assert "execution" in joined


def test_a0241_ai_routing_evidence_payload_is_deterministic() -> None:
    payload = _routing_input()
    first = ai_routing_control_service.build_ai_routing_control_decision(**payload)
    second = ai_routing_control_service.build_ai_routing_control_decision(**payload)
    assert first == second


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0241_platform_health_requires_positive_tenant(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        platform_health_service.build_platform_health_evidence(**_health_input(tenant_id=tenant_id))


def test_a0241_platform_health_healthy_low_severity_no_review() -> None:
    result = platform_health_service.build_platform_health_evidence(**_health_input(status="healthy"))
    assert result["severity"] == "low"
    assert result["review_required"] is False


def test_a0241_platform_health_degraded_medium_or_high_severity() -> None:
    result = platform_health_service.build_platform_health_evidence(**_health_input(status="degraded"))
    assert result["severity"] in {"medium", "high", "critical"}


def test_a0241_platform_health_unhealthy_dependency_is_high_or_critical() -> None:
    result = platform_health_service.build_platform_health_evidence(
        **_health_input(status="unhealthy", dependency_available=False)
    )
    assert result["severity"] in {"high", "critical"}
    assert result["review_required"] is True


def test_a0241_platform_health_unknown_status_requires_review() -> None:
    result = platform_health_service.build_platform_health_evidence(**_health_input(status="unknown"))
    assert result["review_required"] is True


def test_a0241_platform_health_high_latency_or_error_rate_raises_severity() -> None:
    result = platform_health_service.build_platform_health_evidence(
        **_health_input(status="healthy", latency_ms=2500.0, error_rate=0.2)
    )
    assert result["severity"] in {"high", "critical"}
    assert result["review_required"] is True


def test_a0241_platform_health_no_fake_uptime_or_sla_claim() -> None:
    result = platform_health_service.build_platform_health_evidence(**_health_input())
    assert result["no_fake_uptime"] is True
    assert result["no_fake_sla"] is True


def test_a0241_platform_health_no_fake_observability_alert_claim() -> None:
    result = platform_health_service.build_platform_health_evidence(**_health_input())
    assert result["no_external_monitoring_integration"] is True


def test_a0241_platform_health_evidence_payload_is_deterministic() -> None:
    payload = _health_input()
    first = platform_health_service.build_platform_health_evidence(**payload)
    second = platform_health_service.build_platform_health_evidence(**payload)
    assert first == second


def test_a0241_no_level4_or_higher_claims_in_service_outputs() -> None:
    routing = ai_routing_control_service.build_ai_routing_control_decision(**_routing_input())
    health = platform_health_service.build_platform_health_evidence(**_health_input())
    text = f"{routing} {health}".lower()
    assert "level 4" not in text
    assert "level 5" not in text
    assert "level 6" not in text


def test_a0241_services_do_not_expose_api_or_frontend_behavior() -> None:
    routing_source = inspect.getsource(ai_routing_control_service)
    health_source = inspect.getsource(platform_health_service)
    combined = (routing_source + "\n" + health_source).lower()
    assert "fastapi" not in combined
    assert "apirouter" not in combined


def test_a0241_no_external_provider_integration_in_service_source() -> None:
    routing_source = inspect.getsource(ai_routing_control_service).lower()
    for forbidden in ["openai", "anthropic", "google.generativeai", "bedrock", "azure_openai"]:
        assert forbidden not in routing_source


def test_a0241_no_module_count_expansion_constant_present() -> None:
    assert not hasattr(ai_routing_control_service, "MODULE_COUNT")
    assert not hasattr(platform_health_service, "MODULE_COUNT")


def test_a0241_state_status_constants_exist() -> None:
    assert isinstance(ai_routing_control_service.ROUTING_STATES, frozenset)
    assert isinstance(ai_routing_control_service.ROUTING_DECISION_STATUSES, frozenset)
    assert isinstance(platform_health_service.HEALTH_STATES, frozenset)
    assert isinstance(platform_health_service.PLATFORM_COMPONENT_STATUSES, frozenset)


def test_a0241_safety_constants_exist() -> None:
    assert "NO_EXTERNAL_LLM_PROVIDER_CALLS" in ai_routing_control_service.SAFETY_GUARDS
    assert "NO_AUTONOMOUS_EXECUTION" in ai_routing_control_service.SAFETY_GUARDS
    assert "NO_FAKE_UPTIME_CLAIMS" in platform_health_service.PLATFORM_HEALTH_SAFETY_GUARDS


def test_a0241_event_readiness_constants_are_deterministic() -> None:
    assert ai_routing_control_service.ROUTING_EVENT_READINESS["review_required"] == "ai.routing.review_required"
    assert platform_health_service.PLATFORM_HEALTH_EVENT_READINESS["critical"] == "platform.health.unhealthy"


def test_a0241_modules_qualify_as_l3_backend_tested_operational_contracts() -> None:
    routing = ai_routing_control_service.build_ai_routing_control_decision(**_routing_input())
    health = platform_health_service.build_platform_health_evidence(**_health_input())
    assert routing["audit_action"].startswith("ai_routing_control.")
    assert health["audit_action"].startswith("platform_health.")
    assert "event_readiness" in routing
    assert "event_readiness" in health
