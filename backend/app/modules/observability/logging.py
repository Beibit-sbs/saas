"""JSON structured logging with request_id + trace_id propagation."""
from __future__ import annotations

import json
import logging
import os
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone

# Stores the current request_id for the running async/sync context.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
tenant_id_var: ContextVar[str | int] = ContextVar("tenant_id", default="-")
actor_id_var: ContextVar[str] = ContextVar("actor_id", default="-")
institution_id_var: ContextVar[str | int] = ContextVar("institution_id", default="-")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


@dataclass(slots=True)
class LogContextTokens:
    request_id: object | None = None
    tenant_id: object | None = None
    actor_id: object | None = None
    institution_id: object | None = None
    trace_id: object | None = None


def bind_log_context(
    *,
    request_id: str | None = None,
    tenant_id: str | int | None = None,
    actor_id: str | None = None,
    institution_id: str | int | None = None,
    trace_id: str | None = None,
) -> LogContextTokens:
    tokens = LogContextTokens()
    if request_id is not None:
        tokens.request_id = request_id_var.set(str(request_id))
    if tenant_id is not None:
        tokens.tenant_id = tenant_id_var.set(tenant_id)
    if actor_id is not None:
        tokens.actor_id = actor_id_var.set(str(actor_id))
    if institution_id is not None:
        tokens.institution_id = institution_id_var.set(institution_id)
    if trace_id is not None:
        tokens.trace_id = trace_id_var.set(str(trace_id))
    return tokens


def reset_log_context(tokens: LogContextTokens) -> None:
    if tokens.trace_id is not None:
        trace_id_var.reset(tokens.trace_id)
    if tokens.institution_id is not None:
        institution_id_var.reset(tokens.institution_id)
    if tokens.actor_id is not None:
        actor_id_var.reset(tokens.actor_id)
    if tokens.tenant_id is not None:
        tenant_id_var.reset(tokens.tenant_id)
    if tokens.request_id is not None:
        request_id_var.reset(tokens.request_id)


def get_log_context() -> dict[str, str | int]:
    """Get current log context as dict."""
    return {
        "request_id": request_id_var.get(),
        "trace_id": trace_id_var.get(),
        "actor_id": actor_id_var.get(),
        "user_id": actor_id_var.get(),
        "tenant_id": tenant_id_var.get(),
        "institution_id": institution_id_var.get(),
    }


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line with structured fields."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        payload: dict = {
            "timestamp": timestamp,
            "level": record.levelname,
            "service": "ai-platform",
            "environment": os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")),
            "request_id": request_id_var.get("-"),
            "trace_id": trace_id_var.get("-"),
            "actor_id": actor_id_var.get("-"),
            "user_id": actor_id_var.get("-"),
            "tenant_id": tenant_id_var.get("-"),
            "institution_id": institution_id_var.get("-"),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Endpoint info
        endpoint = getattr(record, "endpoint", None) or getattr(record, "path", None)
        if endpoint:
            payload["endpoint"] = endpoint
            payload["path"] = endpoint
        
        # HTTP info
        for key in ("method", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        
        # Event/async work fields
        for key in ("event_type", "event_id", "automation_rule_id", "automation_execution_id",
                    "webhook_delivery_id", "developer_app_id", "error_code"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        
        if record.exc_info:
            payload["error_message"] = self.formatException(record.exc_info)
        
        return json.dumps(payload, ensure_ascii=False, default=str)


class _RequestIdFilter(logging.Filter):
    """Inject request context from ContextVar into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        record.trace_id = trace_id_var.get("-")
        record.tenant_id = tenant_id_var.get("-")
        record.actor_id = actor_id_var.get("-")
        record.user_id = actor_id_var.get("-")
        record.institution_id = institution_id_var.get("-")
        return True


def configure_json_logging(level: int = logging.INFO) -> None:
    """
    Replace the root handler with a JSON formatter.
    Call once at application startup (before uvicorn installs its own handlers).
    """
    formatter = _JsonFormatter()
    filter_ = _RequestIdFilter()

    root = logging.getLogger()
    root.setLevel(level)

    # Replace all existing handlers on root logger
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(filter_)
    root.addHandler(handler)

    # Route uvicorn loggers through root so output stays in JSON format.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
