from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.ai_gateway import service as ai_gateway_service
from app.modules.observability import metrics as obs_metrics
from app.modules.observability.security_signals import clear_security_signal_state, record_security_signal
from app.modules.scheduling.room_allocation_readiness import (
    CapacityMatchStatus,
    CapacityRiskLevel,
    RoomAllocationRecommendationStatus,
    RoomAllocationRequirement,
    RoomCapability,
    RoomCapabilityMatchEvidence,
    _capacity_delta,
    _derive_recommendation_status,
    build_capacity_matching_result,
    build_room_allocation_recommendation_result,
)


@pytest.fixture(autouse=True)
def _reset_global_states() -> None:
    ai_gateway_service.clear_ai_gateway_state()
    obs_metrics.clear_metrics_state()
    clear_security_signal_state()


def _req(**kwargs) -> RoomAllocationRequirement:
    data = {
        "section_id": 10,
        "course_id": 11,
        "group_id": 12,
        "teacher_id": "t-1",
        "students_count": 30,
        "max_capacity": 40,
        "required_room_type": "computer_lab",
        "required_computers": 20,
        "equipment_required": ["projector"],
        "restrictions_required": ["exam_enabled"],
    }
    data.update(kwargs)
    return RoomAllocationRequirement(**data)


def _cap(**kwargs) -> RoomCapability:
    data = {
        "tenant_id": 1,
        "room_id": "R-1",
        "room_code": "R-1",
        "room_name": "R-1",
        "room_type": "computer_lab",
        "capacity": 40,
        "computers_count": 25,
        "equipment_available": ["projector", "whiteboard"],
        "supported_lesson_types": ["lecture", "lab"],
        "restrictions": ["exam_enabled"],
        "availability_status": "available",
        "booking_status": "released",
        "maintenance_status": "ok",
        "is_active": True,
        "source_entity_type": "campus_room",
        "source_entity_id": "entity-r1",
    }
    data.update(kwargs)
    return RoomCapability(**data)


def test_ai_gateway_fallback_and_rate_limit_helpers_cover_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    assert ai_gateway_service._should_fallback_to_memory(RuntimeError("database unavailable")) is True
    assert ai_gateway_service._should_fallback_to_memory(ConnectionError("boom")) is True
    assert ai_gateway_service._should_fallback_to_memory(Exception("other")) is False

    monkeypatch.setenv("AI_PROVIDER_TIMEOUT_SECONDS", "not-a-float")
    assert ai_gateway_service._timeout() == 8.0

    monkeypatch.setattr(ai_gateway_service, "get_global_runtime_value", lambda *args, **kwargs: "abc")
    assert ai_gateway_service._runtime_int("k", "ENV", 7) == 7

    monkeypatch.setattr(ai_gateway_service, "get_global_runtime_value", lambda *args, **kwargs: "3")
    assert ai_gateway_service._user_limit("user@example.com") == 3
    assert ai_gateway_service._role_limit("admin") == 3


def test_render_metrics_includes_security_event_and_anomaly_series() -> None:
    for _ in range(3):
        record_security_signal(signal="tenant.override.denied", outcome="denied", actor="u1")

    rendered = obs_metrics.render_metrics()

    assert 'security_events_total{signal="tenant.override.denied",outcome="denied"}' in rendered
    assert 'security_anomalies_total{signal="tenant.override.denied"}' in rendered


def test_render_metrics_includes_ai_routing_and_guardrail_series() -> None:
    obs_metrics.observe_ai_routing_selection(tenant_id=1, mode="fallback", selection="provider_b")
    obs_metrics.observe_ai_guardrail_evaluation(
        tenant_id=1,
        stage="pre",
        detector="pii",
        decision="blocked",
        duration_seconds=0.75,
    )
    obs_metrics.observe_ai_guardrail_blocked(
        tenant_id=1,
        detector="pii",
        reason="sensitive_content",
    )

    rendered = obs_metrics.render_metrics()

    assert 'ai_routing_selection_total{tenant_id="1",mode="fallback",selection="provider_b"}' in rendered
    assert 'ai_guardrail_evaluations_total{tenant_id="1",stage="pre",detector="pii",decision="blocked"}' in rendered
    assert 'ai_guardrail_blocked_total{tenant_id="1",detector="pii",reason="sensitive_content"}' in rendered
    assert 'ai_guardrail_evaluation_duration_seconds_total{tenant_id="1",stage="pre"}' in rendered
    assert 'ai_guardrail_evaluation_duration_seconds_count{tenant_id="1",stage="pre"}' in rendered


def test_capacity_matching_covers_availability_and_restriction_branches() -> None:
    req = _req(restrictions_required=["exam_enabled"])
    cap = _cap()

    unavailable = RoomCapabilityMatchEvidence(availability_ok=False, restrictions_ok=True)
    result_unavailable = build_capacity_matching_result(1, req, capability=cap, capability_match=unavailable)
    assert "availability" in result_unavailable.unsatisfied_requirements

    unknown_restrictions = RoomCapabilityMatchEvidence(availability_ok=None, restrictions_ok=None)
    result_unknown = build_capacity_matching_result(1, req, capability=cap, capability_match=unknown_restrictions)
    assert "restrictions" in result_unknown.unsatisfied_requirements

    bad_restrictions = RoomCapabilityMatchEvidence(availability_ok=True, restrictions_ok=False)
    result_bad = build_capacity_matching_result(1, req, capability=cap, capability_match=bad_restrictions)
    assert any(reason.value == "restriction_mismatch" for reason in result_bad.mismatch_reasons)


def test_ai_gateway_database_helper_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(ai_gateway_service, "psycopg", object())
    assert ai_gateway_service._db_url() == "postgresql://example"
    assert ai_gateway_service._use_database() is True

    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert ai_gateway_service._use_database() is False


def test_room_recommendation_helper_branches_and_fail_closed_tenant() -> None:
    assert _capacity_delta(30, None) == 10**6
    assert _capacity_delta(30, 20) == 10**6 + 10
    assert _capacity_delta(30, 40) == 10

    fallback = _derive_recommendation_status(
        recommendation_score=55,
        capacity_result=SimpleNamespace(
            match_status=CapacityMatchStatus.GOOD_MATCH,
            risk_level=CapacityRiskLevel.LOW,
        ),
    )
    assert fallback == RoomAllocationRecommendationStatus.FALLBACK

    acceptable = _derive_recommendation_status(
        recommendation_score=70,
        capacity_result=SimpleNamespace(
            match_status=CapacityMatchStatus.GOOD_MATCH,
            risk_level=CapacityRiskLevel.LOW,
        ),
    )
    assert acceptable == RoomAllocationRecommendationStatus.ACCEPTABLE

    review_required = _derive_recommendation_status(
        recommendation_score=90,
        capacity_result=SimpleNamespace(
            match_status=CapacityMatchStatus.GOOD_MATCH,
            risk_level=CapacityRiskLevel.HIGH,
        ),
    )
    assert review_required == RoomAllocationRecommendationStatus.REVIEW_REQUIRED

    not_recommended = _derive_recommendation_status(
        recommendation_score=95,
        capacity_result=SimpleNamespace(
            match_status=CapacityMatchStatus.UNAVAILABLE,
            risk_level=CapacityRiskLevel.CRITICAL,
        ),
    )
    assert not_recommended == RoomAllocationRecommendationStatus.NOT_RECOMMENDED

    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        build_room_allocation_recommendation_result(0, _req(), [_cap()])
