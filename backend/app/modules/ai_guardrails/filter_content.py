"""Content moderation filter — deny-list and category-based blocking."""
from __future__ import annotations

import re

from app.modules.ai_guardrails.schemas import DetectorResult, GuardrailDecision

# Categories and their patterns
_CONTENT_CATEGORIES: dict[str, list[re.Pattern]] = {
    "violence": [
        re.compile(r"\b(how\s+to\s+)?(kill|murder|harm|hurt|attack|weapon|explosive|bomb)\b", re.I),
        re.compile(r"\b(make|build|create)\s+(a\s+)?(weapon|bomb|explosive|poison)\b", re.I),
    ],
    "harassment": [
        re.compile(r"\b(racist|sexist|bigot|discriminat)\b", re.I),
        re.compile(r"\b(hate speech|slur)\b", re.I),
    ],
    "illegal": [
        re.compile(r"\b(how\s+to\s+)?(hack|crack|exploit|breach|bypass)\s+(a\s+)?(system|server|database|account|password)\b", re.I),
        re.compile(r"\b(buy|sell|obtain)\s+(illegal|illicit|controlled)\s+(drugs?|substances?|firearms?)\b", re.I),
    ],
    "inappropriate": [
        re.compile(r"\b(explicit|pornograph|nsfw|adult\s+content)\b", re.I),
    ],
}


def filter_content(text: str, extra_deny_patterns: list[str] | None = None) -> DetectorResult:
    """Check content against deny-list categories and optional tenant patterns."""
    if not text or not text.strip():
        return DetectorResult(
            detector="content",
            decision=GuardrailDecision.PASS,
            score=0.0,
        )

    # Check built-in categories
    for category, patterns in _CONTENT_CATEGORIES.items():
        for pattern in patterns:
            if pattern.search(text):
                return DetectorResult(
                    detector="content",
                    decision=GuardrailDecision.BLOCK,
                    score=0.95,
                    reason=f"Content category blocked: {category}",
                    metadata={"category": category},
                )

    # Check tenant-specific deny patterns
    if extra_deny_patterns:
        for raw_pattern in extra_deny_patterns:
            try:
                compiled = re.compile(raw_pattern, re.I)
            except re.error:
                # Treat as literal string if invalid regex
                compiled = re.compile(re.escape(raw_pattern), re.I)
            if compiled.search(text):
                return DetectorResult(
                    detector="content",
                    decision=GuardrailDecision.BLOCK,
                    score=0.9,
                    reason=f"Tenant deny-list match: {raw_pattern[:40]}",
                )

    return DetectorResult(
        detector="content",
        decision=GuardrailDecision.PASS,
        score=0.0,
    )
