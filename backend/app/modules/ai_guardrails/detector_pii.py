"""PII detector — regex-based detection of personally identifiable information."""
from __future__ import annotations

import re

from app.modules.ai_guardrails.schemas import DetectorResult, GuardrailDecision

_PII_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("email", re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")),
    ("phone_us", re.compile(r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b")),
    ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("date_of_birth", re.compile(r"\b(?:dob|date\s+of\s+birth|born\s+on)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", re.I)),
    ("passport", re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")),
)

_WARN_THRESHOLD = 1   # 1+ PII type found → warn
_BLOCK_THRESHOLD = 3  # 3+ distinct PII types → block


def detect_pii(text: str) -> DetectorResult:
    """Detect PII in text. Returns WARN for isolated PII, BLOCK for dense PII."""
    if not text or not text.strip():
        return DetectorResult(
            detector="pii",
            decision=GuardrailDecision.PASS,
            score=0.0,
        )

    found: list[str] = []
    for label, pattern in _PII_PATTERNS:
        if pattern.search(text):
            found.append(label)

    if len(found) >= _BLOCK_THRESHOLD:
        return DetectorResult(
            detector="pii",
            decision=GuardrailDecision.BLOCK,
            score=min(len(found) / len(_PII_PATTERNS), 1.0),
            reason=f"Multiple PII types detected: {found}",
            metadata={"pii_types": found},
        )

    if len(found) >= _WARN_THRESHOLD:
        return DetectorResult(
            detector="pii",
            decision=GuardrailDecision.WARN,
            score=len(found) / _BLOCK_THRESHOLD,
            reason=f"PII detected: {found}",
            metadata={"pii_types": found},
        )

    return DetectorResult(
        detector="pii",
        decision=GuardrailDecision.PASS,
        score=0.0,
    )
