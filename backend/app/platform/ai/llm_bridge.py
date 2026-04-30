"""LLM Bridge — HTTP client for Ollama local inference.

Provides a lightweight, fail-safe interface to the local Ollama server
(deepseek-r1:8b). All calls are optional: if Ollama is unavailable,
methods return ``None`` and the caller falls back to rule-based output.

Environment variables:
    OLLAMA_URL   — base URL (default: http://localhost:11434)
    OLLAMA_MODEL — model name (default: deepseek-r1:8b)
    OLLAMA_TIMEOUT_SECONDS — HTTP timeout (default: 30)
    LLM_ENABLED  — set to "0"/"false" to fully disable (default: enabled)
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_URL = "http://localhost:11434"
_DEFAULT_MODEL = "deepseek-r1:8b"
_DEFAULT_TIMEOUT = 30


def _is_enabled() -> bool:
    raw = os.getenv("LLM_ENABLED", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _ollama_url() -> str:
    return os.getenv("OLLAMA_URL", _DEFAULT_URL).rstrip("/")


def _model() -> str:
    return os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)


def _timeout() -> int:
    try:
        return int(os.getenv("OLLAMA_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT)))
    except ValueError:
        return _DEFAULT_TIMEOUT


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST JSON to Ollama and return parsed response or None on any error."""
    url = f"{_ollama_url()}{path}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_timeout()) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.debug("LLM bridge: Ollama unavailable (%s)", exc)
        return None


def generate_explanation(
    *,
    event_type: str,
    situation_type: str,
    severity: str,
    urgency: str,
    factors: list[str],
    actions: list[str],
    context_summary: str = "",
) -> str | None:
    """Ask LLM to produce a human-readable decision explanation.

    Returns a plain-text string or ``None`` if LLM is disabled/unavailable.
    """
    if not _is_enabled():
        return None

    actions_text = ", ".join(actions) if actions else "none"
    factors_text = "\n".join(f"  - {f}" for f in factors)
    prompt = (
        f"You are a university operations AI. Explain the following automated decision "
        f"in 2-3 clear sentences for a university administrator. Be concise and factual.\n\n"
        f"Event: {event_type}\n"
        f"Situation: {situation_type} (severity={severity}, urgency={urgency})\n"
        f"Key factors:\n{factors_text}\n"
        f"Actions triggered: {actions_text}\n"
        f"Additional context: {context_summary or 'none'}\n\n"
        f"Explanation:"
    )

    result = _post_json(
        "/api/chat",
        {
            "model": _model(),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 150},
        },
    )

    if result is None:
        return None

    # Ollama /api/chat response: {"message": {"content": "...", "thinking": "..."}, ...}
    # deepseek-r1 may put response in "thinking" field with empty "content"
    msg = result.get("message") or {}
    content = msg.get("content", "").strip()
    if not content:
        # Fall back to thinking field for deepseek-r1 reasoning models
        content = msg.get("thinking", "").strip()
    if not content:
        return None

    # Strip <think>...</think> tags that some deepseek-r1 variants may emit inline
    import re
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content or None


def classify_risk(
    *,
    event_type: str,
    context_summary: str,
) -> dict[str, str] | None:
    """Ask LLM to classify risk level and suggest priority.

    Returns ``{"risk_level": "...", "priority": "...", "rationale": "..."}``
    or ``None`` if unavailable.
    """
    if not _is_enabled():
        return None

    prompt = (
        f"You are a university risk assessment AI. Given the following event, respond with "
        f"a JSON object containing exactly these fields: risk_level (low/medium/high/critical), "
        f"priority (low/normal/high/urgent), rationale (one sentence).\n\n"
        f"Event: {event_type}\n"
        f"Context: {context_summary}\n\n"
        f"Respond with valid JSON only, no additional text:"
    )

    result = _post_json(
        "/api/chat",
        {
            "model": _model(),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 100},
        },
    )

    if result is None:
        return None

    msg = result.get("message") or {}
    content = msg.get("content", "").strip()
    if not content:
        content = msg.get("thinking", "").strip()
    if not content:
        return None

    import re
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    # Extract JSON block
    json_match = re.search(r"\{.*?\}", content, re.DOTALL)
    if not json_match:
        return None
    try:
        data = json.loads(json_match.group())
        return {
            "risk_level": str(data.get("risk_level", "medium")),
            "priority": str(data.get("priority", "normal")),
            "rationale": str(data.get("rationale", "")),
        }
    except (json.JSONDecodeError, AttributeError):
        return None


def health_check() -> bool:
    """Return True if Ollama is reachable."""
    if not _is_enabled():
        return False
    result = _post_json("/api/tags", {})
    # /api/tags is GET, use different approach
    url = f"{_ollama_url()}/api/tags"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return isinstance(data.get("models"), list)
    except Exception:
        return False
