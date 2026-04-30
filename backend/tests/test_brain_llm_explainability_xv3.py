"""XV3: LLM Decision Explainability — Brain Core /simulate returns LLM explanation.

Tests verify that Brain Core process_signal enriches the explanation block with
a non-None llm_explanation when llm_bridge.generate_explanation returns a value.
All HTTP is mocked — no real Ollama instance required.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.brain_core.service import BrainCoreService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_student_risk_signal(tenant_id: int = 1) -> dict:
    """Minimal signal that Brain Core will accept (supported event_type)."""
    return {
        "signal_id": "xv3-test-signal-001",
        "tenant_id": tenant_id,
        "correlation_id": "xv3-corr-001",
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": "S001", "course_id": "C001"},
        "payload": {
            "student_id": "S001",
            "course_id": "C001",
            "attendance_rate": 0.55,
            "grade_trend": "declining",
            "source_entity_type": "section_attendance",
            "source_entity_id": "SEC001",
        },
        "metadata": {"source": "brain_api_simulation"},
    }


# ---------------------------------------------------------------------------
# XV3 Tests
# ---------------------------------------------------------------------------

class TestBrainLLMExplainability:
    """Brain Core /simulate enriches explanation with LLM-generated text."""

    def test_llm_explanation_present_when_ollama_returns_content(self):
        """When llm_bridge returns a string, decision.explanation.llm_explanation must be non-None."""
        svc = BrainCoreService()
        signal = _make_student_risk_signal()

        mock_explanation = (
            "The student shows a concerning attendance rate of 55% with a declining grade trend, "
            "triggering a high-priority academic risk alert that requires faculty advisor outreach."
        )

        with patch(
            "app.platform.ai.llm_bridge.generate_explanation",
            return_value=mock_explanation,
        ):
            result = svc.process_signal(signal)

        assert result.get("status") not in {"ignored", "rejected"}, (
            f"Signal must be processed, got: {result}"
        )
        decision = result.get("decision", {})
        explanation = decision.get("explanation")
        assert explanation is not None, "explanation block must be present in decision"
        assert isinstance(explanation, dict), "explanation must be a dict"
        llm_exp = explanation.get("llm_explanation")
        assert llm_exp is not None, (
            f"llm_explanation must be non-None when LLM returns content; got: {llm_exp!r}"
        )
        assert mock_explanation in llm_exp or llm_exp == mock_explanation, (
            f"llm_explanation content mismatch: {llm_exp!r}"
        )
        print(f"\n[XV3] llm_explanation: {llm_exp[:80]}...")

    def test_llm_explanation_none_when_ollama_unavailable(self):
        """When llm_bridge returns None (Ollama down), llm_explanation is None — decision still succeeds."""
        svc = BrainCoreService()
        signal = _make_student_risk_signal()

        with patch(
            "app.platform.ai.llm_bridge.generate_explanation",
            return_value=None,
        ):
            result = svc.process_signal(signal)

        assert result.get("status") not in {"ignored", "rejected"}, (
            f"Signal must be processed even without LLM; got: {result}"
        )
        decision = result.get("decision", {})
        explanation = decision.get("explanation")
        assert explanation is not None, "explanation block must still be present without LLM"
        assert explanation.get("llm_explanation") is None, (
            "llm_explanation must be None when LLM is unavailable"
        )
        assert explanation.get("summary"), "rule-based summary must still be present"
        print(f"\n[XV3] Rule-based summary (no LLM): {explanation.get('summary')}")

    def test_explanation_factors_always_present(self):
        """explanation.factors must always list classification factors regardless of LLM."""
        svc = BrainCoreService()
        signal = _make_student_risk_signal()

        with patch(
            "app.platform.ai.llm_bridge.generate_explanation",
            return_value=None,
        ):
            result = svc.process_signal(signal)

        explanation = result.get("decision", {}).get("explanation", {})
        factors = explanation.get("factors")
        assert factors is not None, "factors must be present"
        assert isinstance(factors, list) and len(factors) > 0, (
            f"factors must be a non-empty list; got: {factors!r}"
        )
        # Must contain event_type factor
        joined = " ".join(str(f) for f in factors)
        assert "academic.attendance_risk.detected" in joined, (
            f"event_type must appear in factors; got: {factors}"
        )
        print(f"\n[XV3] Factors ({len(factors)}): {factors[:3]}")

    def test_simulate_returns_decision_id_and_llm_explanation_together(self):
        """Processed signal must contain both decision_id and llm_explanation in one response."""
        svc = BrainCoreService()
        signal = _make_student_risk_signal(tenant_id=1)

        with patch(
            "app.platform.ai.llm_bridge.generate_explanation",
            return_value="Automated intervention triggered due to academic risk indicators.",
        ):
            result = svc.process_signal(signal)

        decision = result.get("decision", {})
        assert "decision_id" in decision, f"decision_id missing from decision: {list(decision.keys())}"
        assert decision.get("explanation", {}).get("llm_explanation") is not None, (
            "llm_explanation must be present alongside decision_id"
        )
        print(
            f"\n[XV3] decision_id={decision['decision_id'][:8]}... "
            f"llm_explanation present: {bool(decision['explanation']['llm_explanation'])}"
        )

    def test_llm_exception_does_not_crash_pipeline(self):
        """If llm_bridge raises an unexpected exception, Brain Core must still return a valid decision."""
        svc = BrainCoreService()
        signal = _make_student_risk_signal()

        with patch(
            "app.platform.ai.llm_bridge.generate_explanation",
            side_effect=RuntimeError("Ollama connection timeout"),
        ):
            result = svc.process_signal(signal)

        assert result.get("status") not in {"ignored", "rejected"}, (
            f"Pipeline must survive LLM exception; got: {result}"
        )
        decision = result.get("decision", {})
        explanation = decision.get("explanation", {})
        # llm_explanation may be None (exception caught by ExplanationEngine._build_llm_explanation)
        assert "summary" in explanation, "summary must still be present after LLM exception"
        print(f"\n[XV3] Exception resilience: decision_type={decision.get('decision_type')}, llm_explanation={explanation.get('llm_explanation')!r}")
