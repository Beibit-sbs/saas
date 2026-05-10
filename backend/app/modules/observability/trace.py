"""Trace context generation and propagation utilities."""
from __future__ import annotations

import uuid
from typing import Any

from .logging import get_log_context

__all__ = ["generate_request_id", "generate_trace_id", "inject_trace_context"]


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    """Generate a new trace ID (correlation ID)."""
    return str(uuid.uuid4())


def inject_trace_context(
    payload: dict[str, Any],
    *,
    include_all: bool = False,
    exclude_keys: set[str] | None = None,
) -> dict[str, Any]:
    """
    Inject trace context (request_id, trace_id, tenant_id, actor_id) into a payload.

    Used for outbox events, webhooks, automation, audit entries, etc.
    """
    exclude_keys = exclude_keys or set()
    context = get_log_context()

    if not include_all:
        # Only inject non-empty, non-default values
        trace_fields = {
            k: v for k, v in context.items()
            if v != "-" and k not in exclude_keys
        }
    else:
        trace_fields = {k: v for k, v in context.items() if k not in exclude_keys}

    return {**payload, **trace_fields}
