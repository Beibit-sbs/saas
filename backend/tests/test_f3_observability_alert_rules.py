from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _load_rules() -> list[dict]:
    repo_root = Path(__file__).resolve().parents[2]
    alerts_path = repo_root / "infra" / "prometheus" / "alerts.yml"
    try:
        raw = alerts_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pytest.skip(f"alerts config not found at {alerts_path}")
    except PermissionError:
        pytest.skip(f"alerts config is not readable in this runtime: {alerts_path}")
    payload = yaml.safe_load(raw)
    groups = payload.get("groups", [])
    rules: list[dict] = []
    for group in groups:
        rules.extend(group.get("rules", []))
    return rules


def test_f3_alert_rules_are_present_with_expected_signals() -> None:
    rules = _load_rules()
    by_name = {rule.get("alert"): rule for rule in rules}

    required_rules = {
        "F3CohortAnalysisLatencyHigh": (
            "f3_cohort_operation_duration_seconds_total",
            "operation=\"analyze\"",
            "status=\"success\"",
        ),
        "F3CohortOperationErrorRateHigh": (
            "f3_cohort_operations_total",
            "status=\"error\"",
        ),
        "F3GuardrailPassRateLow": (
            "f3_guardrails_evaluated_total",
            "result=\"pass\"",
        ),
        "F3AnalysisQueueBacklogHigh": (
            "f3_active_cohort_analysis_queue_depth",
            "status=\"pending\"",
        ),
    }

    for alert_name, expr_markers in required_rules.items():
        assert alert_name in by_name, f"Missing required F3 alert rule: {alert_name}"
        expr = str(by_name[alert_name].get("expr", ""))
        for marker in expr_markers:
            assert marker in expr, f"Alert {alert_name} expression missing marker: {marker}"
