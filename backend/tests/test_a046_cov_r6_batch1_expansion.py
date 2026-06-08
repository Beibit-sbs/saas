from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app import main as app_main
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.ai_gateway import service as ai_gateway_service
from app.modules.brain_core.service import BrainCoreService
from app.modules.observability import metrics as obs_metrics
from app.modules.observability.security_signals import clear_security_signal_state
from app.modules.scheduling.room_allocation_readiness import (
    CapacityMatchStatus,
    CapacityRiskLevel,
    RoomAllocationRecommendationStatus,
    _capacity_delta,
    _derive_recommendation_status,
)
from app.modules.scheduling.service import SchedulingService
from app.platform import router_admin
from app.platform.kpi import service as kpi_service


@pytest.fixture(autouse=True)
def _reset_shared_state() -> None:
    ai_gateway_service.clear_ai_gateway_state()
    obs_metrics.clear_metrics_state()
    clear_security_signal_state()


def _request(
    *,
    headers: dict[str, str] | None = None,
    path: str = "/api/admin/brain/test",
    client_host: str = "127.0.0.1",
    request_id: str = "req-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        headers=headers or {},
        url=SimpleNamespace(path=path),
        client=SimpleNamespace(host=client_host),
        state=SimpleNamespace(request_id=request_id),
    )


def _claims(
    *,
    tenant_id: int,
    roles: list[str] | None = None,
    user_id: str = "owner@example.com",
    permissions: list[str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        tenant_id=tenant_id,
        roles=roles or [],
        user_id=user_id,
        permissions=permissions or [],
    )


def _brain_service() -> BrainCoreService:
    return BrainCoreService()


def _replay_request_record(
    request_id: str,
    *,
    tenant_id: int,
    priority: str,
    status: str = "pending",
    created_at: datetime,
    first_response_at: datetime | None = None,
    resolved_at: datetime | None = None,
) -> dict[str, object]:
    return {
        "request_id": request_id,
        "tenant_id": tenant_id,
        "signal_id": f"signal-{request_id}",
        "decision_id": f"decision-{request_id}",
        "requested_by": "tester@example.com",
        "priority": priority,
        "escalation_level": 0,
        "status": status,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
        "first_response_at": first_response_at.isoformat() if first_response_at else None,
        "resolved_at": resolved_at.isoformat() if resolved_at else None,
    }


def _kpi_card(
    metric_key: str,
    value: int | float | bool | None,
    *,
    title: str | None = None,
    source_status: str | None = None,
    lineage: dict[str, object] | None = None,
    trend: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    card: dict[str, object] = {"metric_key": metric_key, "value": value}
    if title is not None:
        card["title"] = title
    if source_status is not None:
        card["source_status"] = source_status
    if lineage is not None:
        card["metadata_json"] = {"lineage": lineage}
    if trend is not None:
        card["trend"] = trend
    return card


# ---------------------------------------------------------------------------
# Brain Core replay / policy branches
# ---------------------------------------------------------------------------


def test_brain_replay_policy_round_trip_and_history() -> None:
    svc = _brain_service()

    default_policy = svc.get_replay_policy(17)
    assert default_policy["tenant_id"] == 17
    assert default_policy["max_window_days"] == 90
    assert default_policy["max_replays_per_signal"] == 5

    result = svc.set_replay_policy(
        17,
        actor="admin@uni.edu",
        max_window_days=120,
        allowed_actors=["admin@uni.edu"],
        auto_reject_threshold=0.75,
        require_dual_approval=True,
        max_replays_per_signal=7,
    )

    assert result["tenant_id"] == 17
    assert result["max_window_days"] == 120
    assert svc.get_replay_policy(17)["require_dual_approval"] is True
    history = svc.get_replay_policy_history(17)
    assert len(history) == 1
    assert history[0]["policy"]["max_replays_per_signal"] == 7


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_window_days": 0}, "max_window_days"),
        ({"max_window_days": 366}, "max_window_days"),
        ({"max_replays_per_signal": 0}, "max_replays_per_signal"),
        ({"max_replays_per_signal": 101}, "max_replays_per_signal"),
        ({"auto_reject_threshold": -0.1}, "auto_reject_threshold"),
        ({"auto_reject_threshold": 1.1}, "auto_reject_threshold"),
    ],
)
def test_brain_replay_policy_validation_guardrails(kwargs: dict[str, object], message: str) -> None:
    svc = _brain_service()
    with pytest.raises(ValueError, match=message):
        svc.set_replay_policy(1, actor="admin", **kwargs)


@pytest.mark.parametrize(
    ("policy_kwargs", "actor", "audit_events", "expected_allowed"),
    [
        ({"allowed_actors": ["owner@example.com"]}, "owner@example.com", [], True),
        ({"allowed_actors": ["owner@example.com"]}, "other@example.com", [], False),
        (
            {"max_replays_per_signal": 2},
            "owner@example.com",
            [
                {"tenant_id": 1, "signal_id": "sig-1", "event": "replay_approved"},
                {"tenant_id": 1, "signal_id": "sig-1", "event": "replay_executed"},
            ],
            False,
        ),
    ],
)
def test_brain_check_replay_policy_branches(
    policy_kwargs: dict[str, object],
    actor: str,
    audit_events: list[dict[str, object]],
    expected_allowed: bool,
) -> None:
    svc = _brain_service()
    svc._reprocess_audit = list(audit_events)
    svc.set_replay_policy(1, actor="admin", **policy_kwargs)
    result = svc.check_replay_policy(1, actor=actor, signal_id="sig-1")
    assert result["allowed"] is expected_allowed


def test_brain_replay_request_queue_filters_and_sorts() -> None:
    svc = _brain_service()
    base = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    low = svc.create_replay_request(1, signal_id="sig-low", decision_id="dec-low", requested_by="a", priority="low")
    high = svc.create_replay_request(1, signal_id="sig-high", decision_id="dec-high", requested_by="b", priority="high")
    urgent = svc.create_replay_request(1, signal_id="sig-urgent", decision_id="dec-urgent", requested_by="c", priority="urgent")
    other = svc.create_replay_request(2, signal_id="sig-other", decision_id="dec-other", requested_by="d", priority="urgent")
    svc._replay_request_queue[low["request_id"]]["created_at"] = (base + timedelta(minutes=2)).isoformat()
    svc._replay_request_queue[high["request_id"]]["created_at"] = (base + timedelta(minutes=1)).isoformat()
    svc._replay_request_queue[urgent["request_id"]]["created_at"] = base.isoformat()
    svc._replay_request_queue[other["request_id"]]["created_at"] = base.isoformat()
    svc._replay_request_queue[high["request_id"]]["status"] = "resolved"

    pending = svc.get_replay_request_queue(1, status="pending")
    assert [item["priority"] for item in pending] == ["urgent", "low"]
    assert [item["request_id"] for item in pending] == [urgent["request_id"], low["request_id"]]

    filtered = svc.get_replay_request_queue(1, priority="urgent")
    assert [item["request_id"] for item in filtered] == [urgent["request_id"]]
    assert all(item["tenant_id"] == 1 for item in filtered)


def test_brain_escalate_replay_request_guardrails_and_history() -> None:
    svc = _brain_service()
    request = svc.create_replay_request(1, signal_id="sig-1", decision_id="dec-1", requested_by="ops", priority="normal")

    with pytest.raises(ValueError, match="must be > current escalation_level"):
        svc.escalate_replay_request(request["request_id"], reason="duplicate review", target_level=0)

    with pytest.raises(ValueError, match="not found"):
        svc.escalate_replay_request("missing", reason="missing", target_level=1)

    result = svc.escalate_replay_request(request["request_id"], reason="needs human review", target_level=2)
    assert result["updated_request"]["escalation_level"] == 2
    assert len(svc.get_escalation_history(request["request_id"])) == 1


def test_brain_replay_queue_metrics_tracks_resolution_and_response_times() -> None:
    svc = _brain_service()
    base = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    pending = svc.create_replay_request(1, signal_id="sig-p", decision_id="dec-p", requested_by="ops", priority="urgent")
    resolved = svc.create_replay_request(1, signal_id="sig-r", decision_id="dec-r", requested_by="ops", priority="high")
    svc._replay_request_queue[pending["request_id"]].update(
        {
            "created_at": (base + timedelta(minutes=5)).isoformat(),
            "first_response_at": (base + timedelta(minutes=7)).isoformat(),
        }
    )
    svc._replay_request_queue[resolved["request_id"]].update(
        {
            "created_at": base.isoformat(),
            "first_response_at": (base + timedelta(minutes=1)).isoformat(),
            "resolved_at": (base + timedelta(minutes=3)).isoformat(),
            "status": "resolved",
        }
    )
    svc._replay_escalations[resolved["request_id"]] = [{"escalation_id": "e1"}]

    metrics = svc.get_replay_queue_metrics(1)
    assert metrics["total_requests"] == 2
    assert metrics["pending_requests"] == 1
    assert metrics["resolved_requests"] == 1
    assert metrics["queue_by_priority"]["urgent"] == 1
    assert metrics["total_escalations"] == 1
    assert metrics["avg_first_response_time_sec"] == 90.0
    assert metrics["avg_resolution_time_sec"] == 180.0


def test_brain_reason_about_policy_uses_recorded_outcomes() -> None:
    svc = _brain_service()
    svc._outcome_tracker._outcomes = [
        {"tenant_id": 9, "effectiveness": "positive"},
        {"tenant_id": 9, "effectiveness": "negative"},
        {"tenant_id": 9, "effectiveness": "positive"},
        {"tenant_id": 3, "effectiveness": "negative"},
    ]

    report = svc.reason_about_policy(9)
    assert report["tenant_id"] == 9
    assert "2 positive" in report["reasoning"]
    assert len(report["recommendations"]) == 1
    assert len(report["alternative_policies"]) == 2


def test_brain_cross_tenant_recommendations_counts_peer_tenants() -> None:
    svc = _brain_service()
    svc._quality_tracker._observations = [
        {"tenant_id": 1, "effectiveness": "positive"},
        {"tenant_id": 2, "effectiveness": "negative"},
        {"tenant_id": 3, "effectiveness": "positive"},
        {"tenant_id": 1, "effectiveness": "positive"},
    ]

    result = svc.get_cross_tenant_recommendations(1)
    assert result["sample_size"] == 2
    assert result["recommended_profile"]["tenant_id"] == 1
    assert result["peer_benchmarks"]["median_autonomy_level"] == 2


@pytest.mark.parametrize(
    ("positive_count", "total_count", "has_drift", "high_signal_count", "expected_band", "expected_risk"),
    [
        (4, 4, False, 0, "low", 0.2),
        (3, 4, True, 0, "moderate", 0.5),
        (1, 4, False, 0, "high", 0.7),
        (2, 4, False, 2, "high", 0.8),
    ],
)
def test_brain_predict_policy_optimization_branches(
    positive_count: int,
    total_count: int,
    has_drift: bool,
    high_signal_count: int,
    expected_band: str,
    expected_risk: float,
) -> None:
    svc = _brain_service()
    svc._quality_tracker._observations = [
        {"tenant_id": 11, "effectiveness": "positive"} for _ in range(positive_count)
    ] + [
        {"tenant_id": 11, "effectiveness": "negative"} for _ in range(total_count - positive_count)
    ]
    if has_drift:
        svc._drift_alerts[11] = [{"status": "active"}]
    svc._signals = [{"tenant_id": 11, "severity": "high"} for _ in range(high_signal_count)]

    result = svc.predict_policy_optimization(11)
    assert result["forecast_band"] == expected_band
    assert result["risk_score"] == pytest.approx(expected_risk)


@pytest.mark.parametrize(
    ("positive_count", "total_count", "peer_count", "expected_band", "can_auto_apply"),
    [
        (4, 4, 2, "low", True),
        (3, 5, 1, "moderate", False),
        (1, 4, 3, "moderate", False),
    ],
)
def test_brain_generate_policy_rollout_plan_branches(
    positive_count: int,
    total_count: int,
    peer_count: int,
    expected_band: str,
    can_auto_apply: bool,
) -> None:
    svc = _brain_service()
    svc._quality_tracker._observations = [
        {"tenant_id": 12, "effectiveness": "positive"} for _ in range(positive_count)
    ] + [
        {"tenant_id": 12, "effectiveness": "negative"} for _ in range(total_count - positive_count)
    ]
    svc._quality_tracker._observations.extend(
        {"tenant_id": peer, "effectiveness": "positive"} for peer in range(20, 20 + peer_count)
    )

    result = svc.generate_policy_rollout_plan(12)
    assert result["forecast_band"] == expected_band
    assert result["can_auto_apply"] is can_auto_apply
    assert result["peer_sample_size"] == peer_count


def test_brain_proactive_recommendations_branches_and_llm_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    svc = _brain_service()
    svc._policy_resolver.get_profile = lambda tenant_id: SimpleNamespace(enable_ai_reasoning=True)
    svc._signals = [
        {"tenant_id": 15, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 15, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 15, "event_type": "faculty.workload_overload.detected"},
        {"tenant_id": 15, "event_type": "faculty.workload_overload.detected"},
    ]
    svc._decisions = [
        {"tenant_id": 15, "priority": "critical"},
        {"tenant_id": 15, "priority": "critical"},
    ]
    monkeypatch.setattr(
        "app.modules.brain_core.service.llm_bridge.generate_explanation",
        lambda **kwargs: "LLM summary",
    )

    result = svc.proactive_recommendations(15)
    recommendation_types = {item["recommendation_type"] for item in result["items"]}
    assert recommendation_types == {
        "student_retention_playbook",
        "faculty_capacity_rebalance",
        "executive_review",
    }
    assert result["ai_reasoning_enabled"] is True
    assert result["llm_summary"] == "LLM summary"


def test_brain_proactive_recommendations_without_ai_summary() -> None:
    svc = _brain_service()
    svc._policy_resolver.get_profile = lambda tenant_id: SimpleNamespace(enable_ai_reasoning=False)
    svc._signals = [
        {"tenant_id": 16, "event_type": "academic.attendance_risk.detected"},
        {"tenant_id": 16, "event_type": "academic.attendance_risk.detected"},
    ]

    result = svc.proactive_recommendations(16)
    assert result["items"][0]["recommendation_type"] == "student_retention_playbook"
    assert result["llm_summary"] is None


# ---------------------------------------------------------------------------
# AI Gateway helper / validation / rate-limit branches
# ---------------------------------------------------------------------------


def test_ai_gateway_runtime_helpers_cover_boundary_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER_TIMEOUT_SECONDS", " 0 ")
    assert ai_gateway_service._timeout() == 1.0

    monkeypatch.setenv("AI_PROVIDER_TIMEOUT_SECONDS", "not-a-float")
    assert ai_gateway_service._timeout() == 8.0

    monkeypatch.setattr(
        ai_gateway_service,
        "get_global_runtime_value",
        lambda setting_key, env_name, default: "abc",
    )
    assert ai_gateway_service._runtime_int("k", "ENV", 5) == 5

    monkeypatch.setattr(
        ai_gateway_service,
        "get_global_runtime_value",
        lambda setting_key, env_name, default: {
            "ai.rate_limit.provider.openai": "3",
            "ai.rate_limit.user.user_example_com": "-1",
            "ai.rate_limit.user.default": "9",
            "ai.rate_limit.role.admin": "-1",
            "ai.rate_limit.role.default": "11",
            "ai.rate_limit.window_seconds": "0",
        }.get(setting_key, default),
    )
    assert ai_gateway_service._provider_limit("openai") == 3
    assert ai_gateway_service._user_limit("user@example.com") == 9
    assert ai_gateway_service._role_limit("admin") == 11
    assert ai_gateway_service._rate_limit_window_seconds() == 1


def test_ai_gateway_rate_limit_enforces_provider_user_role(monkeypatch: pytest.MonkeyPatch) -> None:
    ai_gateway_service.clear_rate_limit_state()
    monkeypatch.setattr(ai_gateway_service, "_rate_limit_window_seconds", lambda: 60)
    monkeypatch.setattr(ai_gateway_service, "_provider_limit", lambda provider: 1)
    monkeypatch.setattr(ai_gateway_service, "_user_limit", lambda actor: 2)
    monkeypatch.setattr(ai_gateway_service, "_role_limit", lambda role: 3)
    monkeypatch.setattr(ai_gateway_service.time, "time", lambda: 1000.0)

    first = ai_gateway_service.enforce_rate_limit("openai", "owner@example.com", ["admin"])
    assert first["provider_used"] == 1
    assert first["user_used"] == 1

    with pytest.raises(ValueError, match="provider:openai"):
        ai_gateway_service.enforce_rate_limit("openai", "reviewer@example.com", ["admin"])


@pytest.mark.parametrize(
    ("provider", "configured", "validation_url", "expected_message"),
    [
        ("unknown", None, None, "unknown provider"),
        ("openai", False, "https://example.invalid", "openai is not configured"),
        ("openai", True, "", "validation URL is not configured"),
    ],
)
def test_ai_gateway_validate_provider_runtime_rejects_configuration_gaps(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    configured: bool | None,
    validation_url: str | None,
    expected_message: str,
) -> None:
    monkeypatch.setattr(
        ai_gateway_service,
        "_provider_config",
        lambda tenant_id=None: {
            "openai": {
                "configured": configured if configured is not None else True,
                "validation_url": validation_url if validation_url is not None else "https://example.invalid",
                "headers": lambda: {},
                "params": lambda: {},
            }
        },
    )
    with pytest.raises(ValueError, match=expected_message):
        ai_gateway_service.validate_provider_runtime(provider, actor="admin@example.com", roles=["admin"], tenant_id=1)


def test_ai_gateway_validate_provider_runtime_success_includes_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ai_gateway_service,
        "_provider_config",
        lambda tenant_id=None: {
            "openai": {
                "configured": True,
                "validation_url": "https://example.invalid/validate",
                "headers": lambda: {"Authorization": "Bearer test-key"},
                "params": lambda: {"region": "us"},
            }
        },
    )

    class FakeResponse:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(ai_gateway_service, "_request", lambda method, url, headers, params: FakeResponse())
    monkeypatch.setattr(ai_gateway_service, "enforce_rate_limit", lambda provider, actor, roles: {"window_seconds": 60, "provider_used": 1, "user_used": 1})

    result = ai_gateway_service.validate_provider_runtime("openai", actor="admin@example.com", roles=["admin"], tenant_id=1)
    assert result["status"] == "validated"
    assert result["rate_limit"]["provider_used"] == 1


def test_ai_gateway_list_provider_status_uses_provider_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ai_gateway_service,
        "_provider_config",
        lambda tenant_id=None: {
            "openai": {"configured": True, "validation_url": "https://openai.example", "headers": lambda: {}, "params": lambda: {}},
            "custom": {"configured": False, "validation_url": "", "headers": lambda: {}, "params": lambda: {}},
        },
    )

    rows = ai_gateway_service.list_provider_status(tenant_id=7)
    assert rows == [
        {"provider": "openai", "configured": True, "validation_url": "https://openai.example"},
        {"provider": "custom", "configured": False, "validation_url": ""},
    ]


def test_ai_gateway_clear_state_resets_runtime_containers() -> None:
    ai_gateway_service._model_registry["x"] = {"model_key": "x"}
    ai_gateway_service._usage_logs.append({"tenant_id": 1})
    ai_gateway_service._limit_events[("provider", "openai")].append(1.0)

    ai_gateway_service.clear_ai_gateway_state()
    assert ai_gateway_service._model_registry == {}
    assert len(ai_gateway_service._usage_logs) == 0
    assert len(ai_gateway_service._limit_events) == 0


# ---------------------------------------------------------------------------
# KPI helper branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metric_key", "expected_event"),
    [
        ("total_students", "student.created"),
        ("total_enrollments", "enrollment.created"),
        ("total_grades_submitted", "grade.submitted"),
        ("missing.metric", ""),
    ],
)
def test_kpi_metric_key_to_event_branches(metric_key: str, expected_event: str) -> None:
    assert kpi_service._metric_key_to_event(metric_key) == expected_event


@pytest.mark.parametrize(
    ("snapshot_date", "generated_at", "expected_status"),
    [
        ("2026-01-01", "2026-01-01T00:00:00+00:00", "ready"),
        (None, "2026-01-01T00:00:00+00:00", "partial_metadata"),
        ("2026-01-01", None, "partial_metadata"),
    ],
)
def test_kpi_freshness_status_branches(snapshot_date: str | None, generated_at: str | None, expected_status: str) -> None:
    assert kpi_service._freshness_status(snapshot_date=snapshot_date, generated_at=generated_at) == expected_status


@pytest.mark.parametrize(
    ("metric_key", "lineage", "expected_status"),
    [
        ("analytics_kpi_reads_total", {"source_type": "platform_events"}, "derived_from_events"),
        ("analytics_kpi_reads_share_pct", None, "derived_from_usage"),
        ("total_students", None, "derived_from_snapshot"),
    ],
)
def test_kpi_card_source_status_branches(metric_key: str, lineage: dict[str, object] | None, expected_status: str) -> None:
    assert kpi_service._card_source_status(metric_key=metric_key, lineage=lineage) == expected_status


@pytest.mark.parametrize(
    ("cards", "expected_mode"),
    [
        ([], "empty"),
        ([{"source_status": "derived_from_events"}], "derived_from_events"),
        ([{"source_status": "derived_from_usage"}], "derived_from_usage"),
        ([{"source_status": "derived_from_snapshot"}], "derived_from_snapshot"),
        ([{"source_status": "derived_from_events"}, {"source_status": "derived_from_usage"}], "mixed_source"),
    ],
)
def test_kpi_response_source_mode_variants(cards: list[dict[str, object]], expected_mode: str) -> None:
    assert kpi_service._response_source_mode(cards) == expected_mode


@pytest.mark.parametrize(
    ("metric_key", "value", "expected_severity", "expected_actionability"),
    [
        ("total_failed_jobs", 0, "normal", "observe"),
        ("total_failed_jobs", 1, "warning", "review"),
        ("total_failed_jobs", 5, "critical", "act_now"),
        ("analytics_kpi_reads_share_pct", 0, "no_data", "no_action"),
        ("analytics_kpi_reads_share_pct", 15, "warning", "review"),
        ("analytics_kpi_reads_share_pct", 50, "normal", "observe"),
        ("analytics_kpi_reads_share_pct", 85, "warning", "review"),
        ("missing_metric", 10, None, None),
    ],
)
def test_kpi_severity_and_actionability_rules(
    metric_key: str,
    value: int,
    expected_severity: str | None,
    expected_actionability: str | None,
) -> None:
    severity, basis, _policy_pack = kpi_service._severity_for_metric(metric_key, value)
    actionability = kpi_service._actionability_for_severity(severity)
    assert severity == expected_severity
    assert actionability == expected_actionability
    if expected_severity is None:
        assert basis is None


def test_kpi_summary_helpers_cover_portfolio_change_and_source_mix() -> None:
    cards = [
        {"severity": "critical", "actionability_state": "act_now", "trend": [{"value": 1}, {"value": 3}], "source_status": "derived_from_events"},
        {"severity": "warning", "actionability_state": "review", "trend": [{"value": 5}, {"value": 4}], "source_status": "derived_from_usage"},
        {"severity": "normal", "actionability_state": "observe", "trend": [{"value": 7}, {"value": 7}], "source_status": "derived_from_snapshot"},
        {"severity": "no_data", "actionability_state": "no_action", "trend": [], "source_status": "mixed_source"},
    ]

    portfolio = kpi_service._build_kpi_portfolio_summary(cards)
    change = kpi_service._build_kpi_change_digest(cards)
    source_mix = kpi_service._build_kpi_source_mix_summary(cards)

    assert portfolio["overall_portfolio_status"] == "urgent"
    assert change["overall_change_direction"] == "stable"
    assert source_mix["dominant_source_mode"] == "mixed"


def test_kpi_sections_manifest_marks_populated_and_empty_sections() -> None:
    manifest = kpi_service._build_kpi_sections_manifest(
        cards=[{"metric_key": "total_students"}],
        summary={"total_kpis": 1},
        change_digest={"total_kpis": 1},
        source_mix_summary={"total_kpis": 1},
        capabilities={"supports_cards": True},
        surface_id=kpi_service.KPI_SURFACE_ID,
        contract_version=kpi_service.KPI_CONTRACT_VERSION,
        surface_profile={"primary_audience": "human_dashboard"},
        field_semantics={"capabilities": "supported surface features"},
        card_field_semantics={"value": "current count"},
        response_examples={"default": {}},
        surface_map={"cards": {}},
        workflow_hints={"refresh": ["manual"]},
        stability_tiers={"stable": ["cards"]},
        contract_fingerprint={"sha256": "abc"},
        contract_compatibility={"version": "v1"},
    )
    assert manifest["cards"] == "populated"
    assert manifest["summary"] == "populated"
    assert manifest["contract_identity"] == "present"

    empty_manifest = kpi_service._build_kpi_sections_manifest(
        cards=[],
        summary=None,
        change_digest=None,
        source_mix_summary=None,
        capabilities=None,
        surface_id=None,
        contract_version=None,
        surface_profile=None,
        field_semantics=None,
        card_field_semantics=None,
        response_examples=None,
        surface_map=None,
        workflow_hints=None,
        stability_tiers=None,
        contract_fingerprint=None,
        contract_compatibility=None,
    )
    assert empty_manifest["cards"] == "empty"
    assert empty_manifest["capabilities"] == "empty"
    assert empty_manifest["contract_identity"] == "empty"


@pytest.mark.parametrize(
    ("trend", "expected_type", "expected_summary_fragment"),
    [
        ({"key": "analytics_kpi_reads_share_pct", "title": "KPI Reads", "latest_value": 85, "delta": 3, "points": [{"value": 82}, {"value": 85}]}, "high_share", "high at 85%"),
        ({"key": "analytics_kpi_reads_share_pct", "title": "KPI Reads", "latest_value": 10, "delta": -5, "points": [{"value": 15}, {"value": 10}]}, "low_share", "low at 10%"),
        ({"key": "analytics_kpi_reads_share_pct", "title": "KPI Reads", "latest_value": 45, "delta": 0, "points": [{"value": 45}, {"value": 45}]}, "no_change", "stable at 45%"),
        ({"key": "total_students", "title": "Students", "latest_value": 12, "delta": 2, "points": [{"value": 10}, {"value": 12}]}, "growth", "increased by 2"),
        ({"key": "total_students", "title": "Students", "latest_value": 10, "delta": -1, "points": [{"value": 11}, {"value": 10}]}, "decline", "decreased by 1"),
    ],
)
def test_kpi_insight_and_recommendation_helpers_cover_branches(
    trend: dict[str, object],
    expected_type: str,
    expected_summary_fragment: str,
) -> None:
    insight = kpi_service._build_insight_from_trend_row(trend)
    recommendation = kpi_service._build_recommendation_from_insight_row(insight)
    assert insight["type"] == expected_type
    assert expected_summary_fragment in insight["summary"]
    assert recommendation["title"]


@pytest.mark.parametrize(
    ("cards", "expected_risk", "expected_review"),
    [
        ([{"metric_key": "academic_integrity_high_risk_count", "title": "A", "value": 2}], "critical", True),
        ([{"metric_key": "exam_integrity_requires_approval_count", "title": "B", "value": 1}], "high", True),
        ([{"metric_key": "thesis_governance_requires_approval_count", "title": "C", "value": 1}], "medium", True),
        ([{"metric_key": "academic_integrity_high_risk_count", "title": "D", "value": 0}], "low", False),
        ([], "unavailable", False),
    ],
)
def test_kpi_rector_evidence_drilldowns_cover_risk_levels(
    cards: list[dict[str, object]],
    expected_risk: str,
    expected_review: bool,
) -> None:
    drilldowns = kpi_service._build_rector_kpi_evidence_drilldowns(cards=cards)
    first = drilldowns[0]
    assert first["risk_level"] == expected_risk
    assert first["review_required"] is expected_review


# ---------------------------------------------------------------------------
# Router admin and app main helper branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected_module"),
    [
        ("/api/admin/org/students", "faculty"),
        ("/api/admin/org-units/list", "org_structure"),
        ("/api/admin/research-grants/list", "research"),
        ("/api/admin/accreditation-compliance/list", "accreditation"),
        ("/api/admin/ops/health", "operations"),
        ("/api/admin/university/records/list", "academic_records"),
        ("/api/admin/admissions/list", "admissions"),
    ],
)
def test_main_extract_admin_module_from_path(path: str, expected_module: str) -> None:
    assert app_main._extract_admin_module_from_path(path) == expected_module


@pytest.mark.parametrize(
    ("path", "expected_security", "expected_admin"),
    [
        ("/api/admin/security/events", True, True),
        ("/platform/metrics", True, True),
        ("/health", False, False),
    ],
)
def test_main_path_scope_helpers(path: str, expected_security: bool, expected_admin: bool) -> None:
    assert app_main._is_security_scoped_path(path) is expected_security
    assert app_main._is_admin_scoped_path(path) is expected_admin


def test_main_request_resolution_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(
        headers={
            "authorization": "Bearer token",
            "x-tenant-id": "8",
            "x-actor-id": " actor-1 ",
            "x-institution-id": " inst-1 ",
            "x-real-ip": "10.0.0.1",
            "x-forwarded-for": "1.1.1.1, 2.2.2.2",
        },
        client_host="127.0.0.1",
    )
    monkeypatch.setattr(app_main, "parse_access_token_from_request", lambda req, auth: _claims(tenant_id=8, roles=["student"], user_id="actor-token"))
    monkeypatch.setattr(app_main, "resolve_current_user_claims", lambda req, auth: _claims(tenant_id=8, roles=["student"], user_id="actor-token"))
    assert app_main._has_bearer_auth(request) is True
    assert app_main._resolve_rate_limit_actor(request) == "actor-token"
    assert app_main._resolve_request_tenant_id(request) == 8
    assert app_main._resolve_metrics_tenant_id(request) == 8
    assert app_main._resolve_request_actor_id(request) == "actor-token"
    assert app_main._resolve_request_institution_id(request) == "inst-1"
    assert app_main._resolve_client_ip(request) == "10.0.0.1"

    monkeypatch.setattr(app_main, "parse_access_token_from_request", lambda req, auth: (_ for _ in ()).throw(app_main.TokenValidationError("bad")))
    request2 = _request(headers={"x-tenant-id": "12", "x-actor-id": " actor-2 ", "x-forwarded-for": "1.1.1.1, 2.2.2.2"}, client_host="127.0.0.2")
    assert app_main._resolve_request_tenant_id(request2) == app_main._DEFAULT_TENANT_ID
    assert app_main._resolve_metrics_tenant_id(request2) == 12
    assert app_main._resolve_request_actor_id(request2) == "actor-2"
    assert app_main._resolve_client_ip(request2) == "2.2.2.2"


def test_main_authorize_observability_permission_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(headers={"authorization": "Bearer token"})
    monkeypatch.setattr(app_main, "resolve_current_user_claims", lambda req, auth: _claims(tenant_id=4, roles=["admin"], permissions=["obs.read"]))
    app_main._authorize_observability_permission(request, "obs.read")

    monkeypatch.setattr(app_main, "resolve_current_user_claims", lambda req, auth: _claims(tenant_id=4, roles=["superadmin"], permissions=[]))
    app_main._authorize_observability_permission(request, "obs.write")

    monkeypatch.setattr(app_main, "resolve_current_user_claims", lambda req, auth: _claims(tenant_id=4, roles=["admin"], permissions=[]))
    monkeypatch.setattr(app_main, "resolve_permissions_for_tenant", lambda roles, tenant_id: ["obs.read"])
    with pytest.raises(app_main.HTTPException, match="missing permission: obs.write"):
        app_main._authorize_observability_permission(request, "obs.write")


@pytest.mark.parametrize(
    ("body", "expected_code"),
    [
        (b'{"detail": {"code": "E123"}}', "E123"),
        (b'{"code": "E456"}', "E456"),
        (b"not-json", None),
        (b"", None),
    ],
)
def test_main_extract_error_code_from_response_branches(body: bytes, expected_code: str | None) -> None:
    response = SimpleNamespace(body=body)
    assert app_main._extract_error_code_from_response(response) == expected_code


def test_router_admin_request_tenant_and_audit_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(
        headers={"authorization": "Bearer token", "x-tenant-id": "5"},
        path="/api/admin/platform/tenants",
        client_host="10.0.0.9",
        request_id="abc-123",
    )
    monkeypatch.setattr(router_admin, "resolve_current_user_claims", lambda req, auth: _claims(tenant_id=1, roles=["superadmin"], user_id="owner@example.com"))
    monkeypatch.setattr(router_admin, "get_tenant", lambda tenant_id: {"tenant_id": tenant_id, "status": "active"})
    monkeypatch.setattr(router_admin, "is_platform_admin", lambda user_id: True)

    assert router_admin._require_request_tenant_id(request) == 5

    captured: dict[str, object] = {}

    def _capture(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(router_admin, "log_admin_action", _capture)
    router_admin._audit(request, "owner@example.com", "tenant.update", 5, {"k": "v"})
    assert captured["path"] == "/api/admin/platform/tenants"
    assert captured["metadata"] == {"k": "v"}


@pytest.mark.parametrize(
    ("header_value", "claims", "platform_admin", "tenant_result", "expected_status", "expected_message"),
    [
        (None, _claims(tenant_id=1, roles=["user"]), False, {"tenant_id": 1, "status": "active"}, None, None),
        ("1", _claims(tenant_id=1, roles=["user"]), False, {"tenant_id": 1, "status": "active"}, None, None),
        ("2", _claims(tenant_id=1, roles=["superadmin"]), True, {"tenant_id": 2, "status": "active"}, None, None),
        ("bad", _claims(tenant_id=1, roles=["user"]), False, {"tenant_id": 1, "status": "active"}, 400, "invalid tenant header"),
        ("2", _claims(tenant_id=1, roles=["user"]), False, {"tenant_id": 2, "status": "active"}, 403, "cross-tenant override forbidden"),
        (None, _claims(tenant_id=1, roles=["user"]), False, None, 404, "not found"),
        (None, _claims(tenant_id=1, roles=["user"]), False, {"tenant_id": 1, "status": "inactive"}, 403, "not active"),
    ],
)
def test_router_admin_request_tenant_validation_branches(
    monkeypatch: pytest.MonkeyPatch,
    header_value: str | None,
    claims: SimpleNamespace,
    platform_admin: bool,
    tenant_result: dict[str, object] | None,
    expected_status: int | None,
    expected_message: str | None,
) -> None:
    request_headers = {"authorization": "Bearer token"}
    if header_value is not None:
        request_headers["x-tenant-id"] = header_value
    request = _request(headers=request_headers)
    monkeypatch.setattr(router_admin, "resolve_current_user_claims", lambda req, auth: claims)
    monkeypatch.setattr(router_admin, "is_platform_admin", lambda user_id: platform_admin)
    monkeypatch.setattr(router_admin, "get_tenant", lambda tenant_id: tenant_result)

    if expected_status is None:
        result = router_admin._require_request_tenant_id(request)
        assert result in {1, 2}
    else:
        with pytest.raises(app_main.HTTPException, match=expected_message):
            router_admin._require_request_tenant_id(request)


def test_router_admin_tenant_match_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(router_admin, "_require_request_tenant_id", lambda request: router_admin.PLATFORM_TENANT_ID)

    request = _request(headers={"authorization": "Bearer token"})
    router_admin._enforce_target_tenant_match(request, router_admin.PLATFORM_TENANT_ID)
    router_admin._require_platform_tenant_context(request)

    with pytest.raises(app_main.HTTPException, match="cross-tenant access denied"):
        router_admin._enforce_target_tenant_match(request, router_admin.PLATFORM_TENANT_ID + 1)

    monkeypatch.setattr(router_admin, "_require_request_tenant_id", lambda request: router_admin.PLATFORM_TENANT_ID + 1)
    with pytest.raises(app_main.HTTPException, match="cross-tenant access denied"):
        router_admin._require_platform_tenant_context(request)


@pytest.mark.parametrize(
    ("row", "expected_updated_at"),
    [
        ({"id": 1, "tenant_id": 2, "job_type": "sync", "status": "queued", "retry_count": 1, "max_retries": 3, "payload_json": {"a": 1}, "result_json": None, "error_message": None, "created_at": "2026-01-01T00:00:00+00:00", "finished_at": "2026-01-01T00:05:00+00:00", "started_at": "2026-01-01T00:01:00+00:00"}, "2026-01-01T00:05:00+00:00"),
        ({"id": 1, "tenant_id": 2, "job_type": "sync", "status": "queued", "retry_count": 1, "max_retries": 3, "payload_json": {"a": 1}, "result_json": None, "error_message": None, "created_at": "2026-01-01T00:00:00+00:00", "finished_at": None, "started_at": "2026-01-01T00:01:00+00:00"}, "2026-01-01T00:01:00+00:00"),
        ({"id": 1, "tenant_id": 2, "job_type": "sync", "status": "queued", "retry_count": 1, "max_retries": 3, "payload_json": {"a": 1}, "result_json": None, "error_message": None, "created_at": "2026-01-01T00:00:00+00:00", "finished_at": None, "started_at": None}, "2026-01-01T00:00:00+00:00"),
    ],
)
def test_router_admin_legacy_job_read_timestamp_precedence(row: dict[str, object], expected_updated_at: str) -> None:
    job = router_admin._legacy_job_read(row)
    assert job.updated_at == expected_updated_at
    assert job.payload == {"a": 1}


@pytest.mark.parametrize(
    ("raw", "expected_age"),
    [
        (None, -1.0),
        ("not-an-iso", -1.0),
        ("2026-01-01T00:00:00+00:00", 0.0),
    ],
)
def test_metrics_parse_iso_and_age_seconds_branches(raw: str | None, expected_age: float) -> None:
    parsed = obs_metrics._parse_iso(raw)
    if raw and raw != "not-an-iso":
        assert parsed is not None
        assert obs_metrics._age_seconds_from_iso(raw) >= expected_age
    else:
        assert parsed is None
        assert obs_metrics._age_seconds_from_iso(raw) == -1.0


@pytest.mark.parametrize(
    ("status", "bucket_value", "expected_status_class", "expected_bucket_label"),
    [
        (0, 1.0, "0xx", "1"),
        (204, 1.5, "2xx", "1.5"),
        (404, 2.0, "4xx", "2"),
    ],
)
def test_metrics_status_class_and_bucket_label_branches(
    status: int,
    bucket_value: float,
    expected_status_class: str,
    expected_bucket_label: str,
) -> None:
    assert obs_metrics._status_class(status) == expected_status_class
    assert obs_metrics._bucket_label(bucket_value) == expected_bucket_label


def test_metrics_render_escapes_and_includes_additional_series() -> None:
    obs_metrics.clear_metrics_state()
    obs_metrics.record_request("get", '/x"y\\z\n', 200, 0.123, tenant_id=7)
    obs_metrics.observe_auth_login_attempt(auth_source="password", outcome="success", tenant_id=7)
    obs_metrics.observe_developer_analytics_contract(endpoint="/api/x", outcome="ok", reason="ready")
    obs_metrics.observe_playbook_execution_started(tenant_id=7, triggered_by="cron")
    obs_metrics.observe_playbook_execution_finished(tenant_id=7, status="success", duration_seconds=1.25)
    obs_metrics.record_brain_signal_emitted(tenant_id=7)
    obs_metrics.record_brain_decision_made(tenant_id=7, decision_type="risk")
    obs_metrics.record_brain_action_dispatched(tenant_id=7, status="dispatched")

    rendered = obs_metrics.render_metrics()
    assert 'http_requests_total{method="GET",path="/x\\\"y\\\\z\\n"' in rendered
    assert 'auth_login_attempts_total{tenant_id="7",auth_source="password",outcome="success"} 1' in rendered
    assert 'brain_signals_emitted_total{tenant_id="7"} 1' in rendered
    assert 'brain_decisions_total{tenant_id="7",decision_type="risk"} 1' in rendered
    assert 'brain_actions_dispatched_total{tenant_id="7",status="dispatched"} 1' in rendered


def test_scheduling_helpers_cover_attendance_and_contract_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    assert SchedulingService._derive_attendance_risk_level(None) is None
    assert SchedulingService._derive_attendance_risk_level(0.39) == "high"
    assert SchedulingService._derive_attendance_risk_level(0.59) == "medium"
    assert SchedulingService._derive_attendance_risk_level(0.60) is None

    service = SchedulingService(MagicMock())
    monkeypatch.setattr("app.modules.scheduling.service._list_tenant_entities", lambda entity_type, tenant_id: [])
    assert service._check_instructor_has_active_contract(1, "ins-1") is None

    monkeypatch.setattr(
        "app.modules.scheduling.service._list_tenant_entities",
        lambda entity_type, tenant_id: [{"faculty_id": "ins-1", "status": "terminated"}],
    )
    with pytest.raises(DomainValidationError):
        service._check_instructor_has_active_contract(1, "ins-1")

    monkeypatch.setattr(
        "app.modules.scheduling.service._list_tenant_entities",
        lambda entity_type, tenant_id: [{"faculty_id": "ins-1", "status": "active"}],
    )
    assert service._check_instructor_has_active_contract(1, "ins-1") is None

    monkeypatch.setattr(
        "app.modules.scheduling.service._list_tenant_entities",
        lambda entity_type, tenant_id: (_ for _ in ()).throw(RuntimeError("entity service down")),
    )
    assert service._check_instructor_has_active_contract(1, "ins-1") is None


def test_room_allocation_helper_branches_cover_capacity_and_recommendation_status() -> None:
    assert _capacity_delta(20, None) == 10**6
    assert _capacity_delta(20, 15) == 10**6 + 5
    assert _capacity_delta(20, 25) == 5

    available = SimpleNamespace(match_status=CapacityMatchStatus.GOOD_MATCH, risk_level=CapacityRiskLevel.LOW)
    unavailable = SimpleNamespace(match_status=CapacityMatchStatus.UNAVAILABLE, risk_level=CapacityRiskLevel.CRITICAL)
    review_required = SimpleNamespace(match_status=CapacityMatchStatus.GOOD_MATCH, risk_level=CapacityRiskLevel.HIGH)

    assert _derive_recommendation_status(recommendation_score=90, capacity_result=available) == RoomAllocationRecommendationStatus.RECOMMENDED
    assert _derive_recommendation_status(recommendation_score=55, capacity_result=available) == RoomAllocationRecommendationStatus.FALLBACK
    assert _derive_recommendation_status(recommendation_score=90, capacity_result=review_required) == RoomAllocationRecommendationStatus.REVIEW_REQUIRED
    assert _derive_recommendation_status(recommendation_score=95, capacity_result=unavailable) == RoomAllocationRecommendationStatus.NOT_RECOMMENDED
