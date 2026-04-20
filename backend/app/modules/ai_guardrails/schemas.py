"""Schemas for AI Guardrails module."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GuardrailDecision(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


class GuardrailStage(str, Enum):
    PRE = "pre"
    POST = "post"


@dataclass
class DetectorResult:
    detector: str
    decision: GuardrailDecision
    score: float = 0.0
    reason: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class GuardrailResult:
    stage: GuardrailStage
    decision: GuardrailDecision
    blocked: bool
    detectors: list[DetectorResult] = field(default_factory=list)
    latency_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return not self.blocked


@dataclass
class GuardrailPolicy:
    injection_detection: bool = True
    content_moderation: bool = True
    pii_detection: bool = True
    audit_only: bool = False
    blocked_patterns: list[str] = field(default_factory=list)
