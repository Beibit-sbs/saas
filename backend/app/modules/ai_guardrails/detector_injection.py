"""Prompt injection detector — pattern and heuristic based."""
from __future__ import annotations

import re

from app.modules.ai_guardrails.schemas import DetectorResult, GuardrailDecision

# Known prompt injection patterns
_INJECTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)", re.I),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)", re.I),
    re.compile(r"you\s+are\s+now\s+(a\s+)?(?!a\s+student|an?\s+admin)", re.I),
    re.compile(r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(a\s+)?(?!a\s+student|an?\s+admin)", re.I),
    re.compile(r"(new|updated|system|hidden)\s+(instruction|prompt|directive|rule)s?\s*:", re.I),
    re.compile(r"<\s*(system|instruction|prompt)\s*>", re.I),
    re.compile(r"\[\s*(system|instruction|override)\s*\]", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"DAN\s+(mode|prompt)", re.I),
    re.compile(r"do\s+anything\s+now", re.I),
    re.compile(r"pretend\s+(you\s+(have|don'?t have)|there\s+(are|is)\s+no)", re.I),
)

_HIGH_RISK_SCORE = 0.9
_PATTERN_SCORE = 0.75


def detect_injection(text: str) -> DetectorResult:
    """Detect prompt injection attempts in text."""
    if not text or not text.strip():
        return DetectorResult(
            detector="injection",
            decision=GuardrailDecision.PASS,
            score=0.0,
        )

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return DetectorResult(
                detector="injection",
                decision=GuardrailDecision.BLOCK,
                score=_HIGH_RISK_SCORE,
                reason=f"Pattern match: {pattern.pattern[:60]}",
            )

    # Heuristic: suspicious role-override keywords without pattern match
    _ROLE_OVERRIDE_WORDS = ("override", "bypass", "unlock", "unrestricted", "sudo", "admin mode")
    lowered = text.lower()
    matched = [w for w in _ROLE_OVERRIDE_WORDS if w in lowered]
    if len(matched) >= 2:
        return DetectorResult(
            detector="injection",
            decision=GuardrailDecision.WARN,
            score=_PATTERN_SCORE,
            reason=f"Heuristic: suspicious keywords {matched}",
        )

    return DetectorResult(
        detector="injection",
        decision=GuardrailDecision.PASS,
        score=0.0,
    )
