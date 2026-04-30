"""Tests for LLM Bridge (XV1) — fail-safe Ollama client.

All tests use mocked HTTP; no real Ollama instance required.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.platform.ai import llm_bridge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_ollama_response(content: str) -> MagicMock:
    """Build a mock urllib response returning given content."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(
        {"message": {"content": content}}
    ).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# Test: generate_explanation
# ---------------------------------------------------------------------------

class TestGenerateExplanation:
    def test_returns_llm_text_when_ollama_available(self):
        """generate_explanation returns LLM text on successful call."""
        expected = "The student shows declining attendance with 62% rate."
        mock_resp = _mock_ollama_response(expected)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = llm_bridge.generate_explanation(
                event_type="student.attendance_risk.detected",
                situation_type="academic_risk",
                severity="high",
                urgency="immediate",
                factors=["attendance_rate=0.62", "grade_trend=declining"],
                actions=["create_intervention_case", "notify_advisor"],
            )

        assert result == expected

    def test_strips_think_tags_from_deepseek(self):
        """<think>...</think> blocks from deepseek-r1 are removed."""
        raw = "<think>internal reasoning here</think>Clean explanation text."
        mock_resp = _mock_ollama_response(raw)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = llm_bridge.generate_explanation(
                event_type="thesis.overdue_alert.triggered",
                situation_type="thesis_risk",
                severity="medium",
                urgency="high",
                factors=["overdue_days=14"],
                actions=["notify_advisor"],
            )

        assert result == "Clean explanation text."
        assert "<think>" not in (result or "")

    def test_returns_none_when_ollama_unavailable(self):
        """Returns None gracefully when Ollama is not reachable."""
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            result = llm_bridge.generate_explanation(
                event_type="student.dropout_risk.detected",
                situation_type="dropout_risk",
                severity="critical",
                urgency="immediate",
                factors=["gpa=1.8"],
                actions=["create_intervention_case"],
            )

        assert result is None

    def test_returns_none_when_llm_disabled(self, monkeypatch):
        """Returns None when LLM_ENABLED=0."""
        monkeypatch.setenv("LLM_ENABLED", "0")

        result = llm_bridge.generate_explanation(
            event_type="faculty.overload.detected",
            situation_type="workload_risk",
            severity="high",
            urgency="normal",
            factors=["active_theses=12"],
            actions=["create_workload_review_task"],
        )

        assert result is None


# ---------------------------------------------------------------------------
# Test: classify_risk
# ---------------------------------------------------------------------------

class TestClassifyRisk:
    def test_parses_json_from_llm(self):
        """classify_risk parses JSON risk classification from LLM."""
        json_response = json.dumps(
            {
                "risk_level": "high",
                "priority": "urgent",
                "rationale": "Student has not attended for 3 weeks.",
            }
        )
        mock_resp = _mock_ollama_response(json_response)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = llm_bridge.classify_risk(
                event_type="student.attendance_risk.detected",
                context_summary="attendance_rate=0.45, missed_3_weeks=True",
            )

        assert result is not None
        assert result["risk_level"] == "high"
        assert result["priority"] == "urgent"
        assert "Student" in result["rationale"]

    def test_returns_none_on_invalid_json(self):
        """Returns None if LLM returns non-parseable content."""
        mock_resp = _mock_ollama_response("Sorry, I cannot process that.")

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = llm_bridge.classify_risk(
                event_type="test.event",
                context_summary="test",
            )

        assert result is None


# ---------------------------------------------------------------------------
# Test: health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_returns_true_when_models_available(self):
        """health_check returns True when Ollama has models loaded."""
        resp = MagicMock()
        resp.read.return_value = json.dumps(
            {"models": [{"name": "deepseek-r1:8b"}]}
        ).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=resp):
            assert llm_bridge.health_check() is True

    def test_returns_false_when_ollama_down(self):
        """health_check returns False when Ollama is unreachable."""
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            assert llm_bridge.health_check() is False
