"""GuardrailEngine — orchestrates pre and post guardrail chains."""
from __future__ import annotations

import time

from app.modules.ai_guardrails.detector_injection import detect_injection
from app.modules.ai_guardrails.detector_pii import detect_pii
from app.modules.ai_guardrails.filter_content import filter_content
from app.modules.ai_guardrails.schemas import (
    DetectorResult,
    GuardrailDecision,
    GuardrailPolicy,
    GuardrailResult,
    GuardrailStage,
)

_DEFAULT_POLICY = GuardrailPolicy()


def _worst_decision(results: list[DetectorResult]) -> GuardrailDecision:
    """Return the most severe decision from a list of detector results."""
    if any(r.decision == GuardrailDecision.BLOCK for r in results):
        return GuardrailDecision.BLOCK
    if any(r.decision == GuardrailDecision.WARN for r in results):
        return GuardrailDecision.WARN
    return GuardrailDecision.PASS


class GuardrailEngine:
    """Orchestrates pre and post guardrail evaluation chains."""

    def __init__(self, policy: GuardrailPolicy | None = None) -> None:
        self._policy = policy or _DEFAULT_POLICY

    @property
    def policy(self) -> GuardrailPolicy:
        return self._policy

    def evaluate_pre(self, text: str) -> GuardrailResult:
        """Evaluate input text through pre-call guardrails."""
        start = time.monotonic()
        results: list[DetectorResult] = []

        if self._policy.injection_detection:
            results.append(detect_injection(text))

        if self._policy.content_moderation:
            results.append(filter_content(text, self._policy.blocked_patterns or None))

        if self._policy.pii_detection:
            results.append(detect_pii(text))

        decision = _worst_decision(results)
        # In audit_only mode, never actually block
        if self._policy.audit_only:
            blocked = False
        else:
            blocked = decision == GuardrailDecision.BLOCK

        latency_ms = (time.monotonic() - start) * 1000

        return GuardrailResult(
            stage=GuardrailStage.PRE,
            decision=decision,
            blocked=blocked,
            detectors=results,
            latency_ms=latency_ms,
        )

    def evaluate_post(self, text: str) -> GuardrailResult:
        """Evaluate provider output through post-call guardrails."""
        start = time.monotonic()
        results: list[DetectorResult] = []

        if self._policy.content_moderation:
            results.append(filter_content(text, self._policy.blocked_patterns or None))

        if self._policy.pii_detection:
            results.append(detect_pii(text))

        decision = _worst_decision(results)
        if self._policy.audit_only:
            blocked = False
        else:
            blocked = decision == GuardrailDecision.BLOCK

        latency_ms = (time.monotonic() - start) * 1000

        return GuardrailResult(
            stage=GuardrailStage.POST,
            decision=decision,
            blocked=blocked,
            detectors=results,
            latency_ms=latency_ms,
        )
